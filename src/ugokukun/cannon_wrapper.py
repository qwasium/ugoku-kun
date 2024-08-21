"""Wrapper for Cannon camera."""

import json
import time
import os
import warnings
import itertools
import logging
import re
from typing import Any, Callable, Tuple, Dict

import requests as req


def _req_handle(func: Callable[[Any, str, Any], Any]) -> Callable[[Any, str, Any], Any]:
    def wrapper(instance: Any, api_str: str, *args, **kwargs) -> req.models.Response:
        """Wrapper to repeat HTTP requests until success or max_attempts is reached.

        Repeat HTTP requests until success or max_attempts is reached.
        Only return when status_code is 200, raise error otherwise.

        Returns
        -------
        req.models.Response
            Response of the request.

        Raises
        ------
        timeout_err
            timeout error
        connection_err
            network problems
        http_err
            invalid HTTP response
        redirect_err
            bad URL
        req_err
            all exceptions that requests can raise
        ConnectionError
            if failed to get response

        """
        # Check if api is available
        assert api_str in instance.api_url, "API not available: " + str(api_str)

        instance.logger.info("API URL: %s", str(api_str))

        # Try to get response for max_attempts times
        for attempt in range(instance.max_attemts):
            if attempt > 0:
                time.sleep(instance.wait_time)

            try:
                response = func(instance, api_str, *args, **kwargs)

            # timeout
            except req.exceptions.Timeout as timeout_err:
                if attempt < instance.max_attemts - 1:
                    instance.logger.warning("  - timeout, retrying...")
                    continue
                warnings.warn("Timeout: " + str(api_str))
                raise timeout_err

            # network problems
            except req.exceptions.ConnectionError as connection_err:
                if attempt < instance.max_attemts - 1:
                    instance.logger.warning("  - ConnectionError, retrying...")
                    continue
                warnings.warn("ConnectionError: " + str(api_str))
                raise connection_err

            # invalid HTTP response
            except req.exceptions.HTTPError as http_err:
                if attempt < instance.max_attemts - 1:
                    instance.logger.warning("  - HTTPError, retrying...")
                    continue
                warnings.warn("HTTPError: " + str(api_str))
                raise http_err

            # bad URL
            except req.exceptions.TooManyRedirects as redirect_err:
                if attempt < instance.max_attemts - 1:
                    instance.logger.warning("  - TooManyRedirects, retrying...")
                    continue
                warnings.warn("TooManyRedirects: " + str(api_str))
                raise redirect_err

            # all exceptions that requests can raise
            except req.exceptions.RequestException as req_err:
                if attempt < instance.max_attemts - 1:
                    instance.logger.warning("  - RequestException, retrying...")
                    continue
                warnings.warn("RequestException: " + str(api_str))
                raise req_err

            # continue if response is not valid
            if hasattr(response, "status_code") is False:
                instance.logger.warning("  - Invalid (no status code), retrying...")
                continue

            # return if success
            if response.status_code == 200:
                instance.logger.info("  - Request success: 200")
                return response
            # continue if failed
            else:
                instance.logger.warning(
                    "  - Request failed, retrying: %d", response.status_code
                )
                continue

        # if failed
        instance.logger.warning("  - Failed to get response: %s", str(api_str))
        assert hasattr(response, "status_code"), "I'm a teapot: NO status code returned"
        raise ConnectionError("I'm a teapot: " + str(response.status_code))

    return wrapper


class CannonWrapper:
    """Wrapper for Cannon ccapi.

    An instance of this class represents a single Cannon camera connection.

    Attributes
    ----------
    wait_time : float
        Wait time between attempts.
    req_timeout : Tuple[float, float]
        Request timeout.
    ip_port : str
        IP address and port of the camera. Format is: {IP address}:{port}.
    auto_power_off : bool
        Disables auto power off if False.
    log_path : str
        Path of log file for logging.
    logger : logging.Logger
        Logger for logging.
    api_url : List[str]
        List of API URLs.
    available_api : Dict
        Available API.
    device_info : Dict
        Device information.
    settings : Dict
        Shooting parameters.

    """

    def __init__(
        self,
        wait_time: float = 3,
        max_attempts: int = 5,
        req_timeout: Tuple[float, float] = (3.0, 7.5),
        ip_port: str = "192.168.1.2:8080",
        auto_power_off: bool = False,
        sync_time: bool = True,
        log_path: str = "log.txt",
    ):
        """Initialize connector by connecting to cannon camera and disabling auto power off.

        The constructor will...
        - Connect to the camera.
        - Disable auto power off.

        Parameters
        ----------
        wait_time : float, optional
            Wait time between attempts., by default 3
        max_attempts : int, optional
            Maximum number of HTTP request attempts., by default 5
        req_timeout : Tuple[float, float], optional
            Request timeout., by default (3.0, 7.5)
        ip_port : str, optional
            IP address and port of the camera. Format is: {IP address}:{port}., by default "
        auto_power_off : bool, optional
            Disables auto power off if False., by default False
        sync_time : bool, optional
            Synchronize camera time with computer time if True., by default True
        log_path : str, optional
            Path of log file for logging., by default "log.txt"
        """
        # set attributes
        self.wait_time = wait_time
        self.req_timeout = req_timeout
        self.ip_port = ip_port
        self.ip_address = ip_port.split(":")[0]
        self.port = ip_port.split(":")[1]
        self.uri = f"http://{ip_port}/ccapi"
        self.max_attemts = max_attempts

        # logging
        self.log_path = log_path
        if os.path.dirname(log_path) and not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        _console_handler = logging.StreamHandler()
        _console_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(_console_handler)

        _file_handler = logging.FileHandler(self.log_path)
        _file_handler.setLevel(logging.DEBUG)
        _file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(_file_handler)

        # Initialize connection
        self.api_url = [self.uri]  # set to make first request
        self.available_api = self.http_get(self.uri).json()
        self.logger.info("  - Connection established")
        self.api_url = [
            api["url"]
            for api in (itertools.chain.from_iterable(self.available_api.values()))
        ]
        self.device_info = self.http_get(self.get_full_uri("/deviceinformation")).json()
        self.logger.info("  - Acquired device information")

        # shooting parameters
        self.settings = {}
        self.get_shooting_param()

        # Disable auto power off
        if not auto_power_off:
            self.kill_auto_power_off()

        # Sync time
        if sync_time:
            self.sync_time()

        # message connected
        # print("\n#####################################################################")
        self.logger.info("Connected to Cannon camera: ")
        self.logger.info("  - %s", self.device_info["productname"])
        self.logger.info("  - %s", self.ip_port)
        # print("#####################################################################\n")

    @_req_handle
    def http_get(self, api_str: str) -> req.models.Response:
        """HTTP get request wrapped in _req_handle."""
        return req.get(api_str, timeout=self.req_timeout)

    @_req_handle
    def http_post(self, api_str: str, payload: Dict) -> req.models.Response:
        """HTTP post request wrapped in _req_handle."""
        return req.post(api_str, json=payload, timeout=self.req_timeout)

    @_req_handle
    def http_put(self, api_str: str, payload: Dict) -> req.models.Response:
        """HTTP put request wrapped in _req_handle."""
        return req.put(api_str, json=payload, timeout=self.req_timeout)

    @_req_handle
    def http_delete(self, api_str: str) -> req.models.Response:
        """HTTP delete request wrapped in _req_handle."""
        return req.delete(api_str, timeout=self.req_timeout)

    def get_full_uri(self, api_str: str) -> str:
        """Get full URI. I was not sure if there would be different versions of the same API. If that is not the case, the function can be simplified.

        I was not sure if there would be different versions of the same API command in different API versions.
        If that is not the case, the function can be simplified.

        Parameters
        ----------
        api_str : str
            API URL string after: "http://{self.ip_address}:{self.port}/ccapi/"version".
            Example: "/shooting/control/shutterbutton".

        Returns
        -------
        str
            Full API URL of the newest version of the input API.
            Example: "http://192.168.1.2:8080/ccapi/ver100/shooting/control/shutterbutton"

        Notes
        -----
        I was not sure if there would be different versions of the same API command in different API versions.
        If that is not the case, the function can be simplified.
        """
        # match available API that encs with api_str
        match = re.compile(f"{api_str}$").search
        valid_api = ""
        for api in self.api_url:
            if match(api):
                valid_api = api  # we want the latest version

        # if API is not available, valid_api==""
        if not valid_api:
            raise ValueError("API not available for: " + str(api_str))
        return valid_api

    def kill_auto_power_off(self) -> req.models.Response:
        """Disable auto power off.

        Returns
        -------
        req.models.Response
            Auto power off result.
        """
        auto_off_api = self.get_full_uri("/functions/autopoweroff")
        auto_off = self.http_put(auto_off_api, payload={"value": "disable"})
        self.logger.info(
            "  - Auto power off is disabled: %s", auto_off.content.decode("utf-8")
        )
        return auto_off

    def get_shooting_param(self) -> req.models.Response:
        """Get all shooting parameters.

        Returns
        -------
        req.models.Response
            Shooting parameters.

        Notes
        -----
        self.settings["color_temperature"]["ability"] is changed to a list of available color temperatures.
        Example:
            Before: {"min": 2500, "max": 10000, "step": 100}
            After:  [2500, 2600, 2700, ..., 10000]
        """
        settings_api = self.get_full_uri("/shooting/settings")
        settings = self.http_get(settings_api)
        self.logger.info(
            "  - Current shooting parameters: %s", settings.content.decode("utf-8")
        )
        self.settings = settings.json()
        # convert color temperature to a list
        if self.settings["colortemperature"]["ability"]:
            self.settings["colortemperature"]["ability"] = [
                ct
                for ct in range(
                    self.settings["colortemperature"]["ability"]["min"],
                    self.settings["colortemperature"]["ability"]["max"]
                    + self.settings["colortemperature"]["ability"]["step"],
                    self.settings["colortemperature"]["ability"]["step"],
                )
            ]

        return settings

    def set_shooting_settings(self, param: str, value: str) -> req.models.Response:
        """Set shooting parameters.

        Parameters
        ----------
        param : str
            Parameter to be set, such as:
            - "shutter_speed"
            - "aperture"
            - "iso"
            - "exposure"
            - "whitebalance"
            - "colortemperature"
            Valid entries are hard coded in this method.
        value : str
            Value of the parameter. Depends on the parameter. payload is {"value": value}

        Returns
        -------
        req.models.Response
            Response of the request.

        Raises
        ------
        ValueError
            If invalid `param` is provided.
        """
        param = param.lower()
        param_key = {
            "shutter_speed": "tv",
            "aperture": "av",
            "iso": "iso",
            "exposure": "exposure",
            "whitebalance": "wb",
            "colortemperature": "colortemperature",
        }

        # check if param is valid
        if value not in self.settings[param_key[param]]["ability"]:
            raise ValueError("Invalid " + param + ": " + value)

        # set param
        param_api = self.get_full_uri(f"/shooting/settings/{param_key[param]}")
        response = self.http_put(param_api, payload={"value": value})

        # update self.settings
        self.get_shooting_param()

        return response

    def set_shutter_speed(self, shutter_speed: str) -> req.models.Response:
        """Set shutter speed.

        Payload example: {"value": "5\""}
        The backslash is an excape charactor.

        Parameters
        ----------
        shutter_speed : str
            Shutter speed. Example: "5\""

        Returns
        -------
        req.models.Response
            Response of the request.
        """
        shutter_speed_response = self.set_shooting_settings(
            "shutter_speed", shutter_speed
        )
        self.logger.info("  - Shutter speed set to: %s", shutter_speed)
        return shutter_speed_response

    def set_aperture(self, aperture: str) -> req.models.Response:
        """Set aperture.

        Payload example: {"value": "f4.0"}

        Parameters
        ----------
        aperture : str
            Aperture. Example: "f4.0"

        Returns
        -------
        req.models.Response
            Response of the request.
        """
        aperture_response = self.set_shooting_settings("aperture", aperture)
        self.logger.info("  - Exposure set to: %s", aperture)
        return aperture_response

    def set_iso(self, iso: str) -> req.models.Response:
        """Set ISO value.

        Payload example: {"value": "3200"}

        Parameters
        ----------
        iso : str
            ISO. Example: "3200"

        Returns
        -------
        req.models.Response
            Response of the request.
        """
        iso_response = self.set_shooting_settings("iso", iso)
        self.logger.info("  - ISO set to: %s", iso)
        return iso_response

    def set_exposure(self, exposure: str) -> req.models.Response:
        """Set exposure.

        Payload example: {"value": "-2_2/3"}

        Parameters
        ----------
        exposure : str
            Exposure. Example: "-2_2/3"

        Returns
        -------
        req.models.Response
            Response of the request.
        """
        exposure_response = self.set_shooting_settings("exposure", exposure)
        self.logger.info("  - Exposure set to: %s", exposure)
        return exposure_response

    def set_white_balance(self, white_balance: str) -> req.models.Response:
        """Set white balance.

        Payload example: {"value": "auto"}

        Parameters
        ----------
        white_balance : str
            White balance. Example: "auto"

        Returns
        -------
        req.models.Response
            Response of the request.
        """
        white_balance_response = self.set_shooting_settings(
            "whitebalance", white_balance
        )
        self.logger.info("  - White balance set to: %s", white_balance)
        return white_balance_response

    def set_color_temp(self, color_temp: int) -> req.models.Response:
        """Set color temperature.

        Payload example: {"value": 4000}"

        Parameters
        ----------
        color_temp : int
            Color temperature. Example: 4000

        Returns
        -------
        req.models.Response
            Response of the request.
        """
        color_temp_response = self.set_shooting_settings("colortemperature", color_temp)
        self.logger.info("  - Color temperature set to: %s", str(color_temp))
        return color_temp_response

    def shutter(self, af: bool = False) -> req.models.Response:
        """Take a picture.

        Payload example: {"af": False}."

        Parameters
        ----------
        af : bool, optional
            Auto focus. Key value for payload., by default False

        Returns
        -------
        req.models.Response
            Shutter button response.
        """
        payload = {"af": bool(af)} # int [0|1] -> int::bool [False|True]
        api_str = self.get_full_uri("/shooting/control/shutterbutton")
        shot = self.http_post(api_str, payload)
        self.logger.info("  - Shutter button pressed")
        return shot

    def sync_time(self) -> req.models.Response:
        """Set camera time to current time (of the computer).

        Returns
        -------
        req.models.Response
            Response of the request.
        """
        now = time.localtime()

        if now.tm_isdst == -1:
            self.logger.warning("  - Daylight saving time is not known")
            raise ValueError("Daylight saving time is not known")

        payload = {
            "datetime": time.strftime("%a, %d %b %Y %H:%M:%S %z", now),
            "dst": bool(now.tm_isdst) # int [0|1] -> int::bool [False|True]
        }
        print(payload)
        api_str = self.get_full_uri("/functions/datetime")
        sync = self.http_put(api_str, payload)
        self.logger.info("  - Time synchronized")
        return sync

    def dump_attributes(self, ouput_path: str = "camera_settings.json") -> None:
        """Dump all settings to JSON file.

        Parameters
        ----------
        ouput_path : str, optional
            Path to the output file., by default "camera_settings.json"

        Returns
        -------
        Dict
            Dumped settings.
        """
        dump_dict = {
            "wait_time": self.wait_time,
            "req_timeout": self.req_timeout,
            "ip_port": self.ip_port,
            "max_attempts": self.max_attemts,
            "available_api": self.available_api,
            "api_url": self.api_url,
            "device_info": self.device_info,
            "settings": self.settings,
        }
        with open(ouput_path, "w", encoding="utf-8") as file:
            json.dump(dump_dict, file)
        self.logger.info("  - Settings dumped to: %s", ouput_path)
        return dump_dict
