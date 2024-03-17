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
        Only return when status_code is 200, raise error otherwise.

        :raises timeout_err: timeout error
        :raises connection_err: network problems
        :raises http_err: invalid HTTP response
        :raises redirect_err: bad URL
        :raises req_err: all exceptions that requests can raise
        :raises ConnectionError: if failed to get response
        :return: response
        :rtype: req.models.Response
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

    :ivar float wait_time: Wait time between attempts.


    """

    def __init__(
        self,
        wait_time: float = 3,
        max_attempts: int = 5,
        req_timeout: Tuple[float, float] = (3.0, 7.5),
        ip_port: str = "192.168.1.2:8080",
        auto_power_off: bool = False,
        log_path: str = "log.txt",
    ):
        """Initialize connector by connecting to cannon camera and disabling auto power off.

        :param wait_time: Wait time between attempts., defaults to 3
        :type wait_time: float, optional
        :param max_attempts: Maximum number of HTTP request attempts., defaults to 5
        :type max_attempts: int, optional
        :param req_timeout: Request timeout., defaults to (3.0, 7.5)
        :type req_timeout: Tuple[float, float], optional
        :param ip_port: IP address and port of the camera. Format is: {IP address}:{port}., defaults to "192.168.1.2:8080"
        :type ip_port: str, optional
        :param auto_power_off: Disables auto power off if False., defaults to False
        :type auto_power_off: bool, optional
        :param log_path: Path of log file for logging., defaults to "log.txt"
        :type log_path: str, optional
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
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write("")

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

        # message connected
        # print("\n#####################################################################")
        self.logger.info("Connected to Cannon camera: ")
        self.logger.info("  - %s", self.device_info["productname"])
        self.logger.info("  - %s", self.ip_port)
        # print("#####################################################################\n")

    @_req_handle
    def http_get(self, api_str: str) -> req.models.Response:
        """HTTP get request."""
        return req.get(api_str, timeout=self.req_timeout)

    @_req_handle
    def http_post(self, api_str: str, payload: Dict) -> req.models.Response:
        """HTTP post request."""
        return req.post(api_str, json=payload, timeout=self.req_timeout)

    @_req_handle
    def http_put(self, api_str: str, payload: Dict) -> req.models.Response:
        """HTTP put request."""
        return req.put(api_str, json=payload, timeout=self.req_timeout)

    @_req_handle
    def http_delete(self, api_str: str) -> req.models.Response:
        """HTTP delete request."""
        return req.delete(api_str, timeout=self.req_timeout)

    def get_full_uri(self, api_str: str) -> str:
        """Get full URI. I was not sure if there would be different versions of the same API. If that is not the case, the function can be simplified.

        :param api_str: API URL string after: "http://{self.ip_address}:{self.port}/ccapi/"version".
            Example: "/shooting/control/shutterbutton".

        :type api_str: str
        :raises ValueError: If API is not available.
        :return valid_api: Full API URL of the newest version of the input API.
            Example: "http://192.168.1.2:8080/ccapi/ver100/shooting/control/shutterbutton"

        :rtype: str
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

        :return: Auto power off result.
        :rtype: req.models.Response
        """
        auto_off_api = self.get_full_uri("/functions/autopoweroff")
        auto_off = self.http_put(auto_off_api, payload={"value": "disable"})
        self.logger.info(
            "  - Auto power off is disabled: %s", auto_off.content.decode("utf-8")
        )
        return auto_off

    def get_shooting_param(self) -> req.models.Response:
        """Get all shooting parameters.
        self.settings["color_temperature"]["ability"] is changed to a list of available color temperatures.
        Example:
            Before: {"min": 2500, "max": 10000, "step": 100}
            After:  [2500, 2600, 2700, ..., 10000]

        :return: Shooting parameters.
        :rtype: req.models.Response
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
        """Wrapper for setting shooting parameters.

        :param param: Parameter to be set, such as:
            - "shutter_speed"
            - "aperture"
            - "iso"
            - "exposure"
            - "whitebalance"
            - "colortemperature"
            Valid entries are hard coded in this method.
        :type param: str
        :param value: Value of the parameter. Depends on the parameter. payload is {"value": value}
        :type value: str
        :raises ValueError: If invalid `param` is provided.
        :return: Response of the request.
        :rtype: req.models.Response
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
        """Set shutter speed. Payload example: {"value": "5\""}

        :param shutter_speed: Shutter speed. Example: "5\""
        :type shutter_speed: str
        :return: Response of the request.
        :rtype: req.models.Response
        """
        shutter_speed_response = self.set_shooting_settings(
            "shutter_speed", shutter_speed
        )
        self.logger.info("  - Shutter speed set to: %s", shutter_speed)
        return shutter_speed_response

    def set_aperture(self, aperture: str) -> req.models.Response:
        """Set aperture. Payload example: {"value": "f4.0"}

        :param aperture: Aperture. Example: "f4.0"
        :type aperture: str
        :return: Response of the request.
        :rtype: req.models.Response
        """
        aperture_response = self.set_shooting_settings("aperture", aperture)
        self.logger.info("  - Exposure set to: %s", aperture)
        return aperture_response

    def set_iso(self, iso: str) -> req.models.Response:
        """Set ISO value. Payload example: {"value": "3200"}

        :param iso: ISO. Example: "3200"
        :type iso: str
        :return: Response of the request.
        :rtype: req.models.Response
        """
        iso_response = self.set_shooting_settings("iso", iso)
        self.logger.info("  - ISO set to: %s", iso)
        return iso_response

    def set_exposure(self, exposure: str) -> req.models.Response:
        """Set exposure. Payload example: {"value": "-2_2/3"}

        :param exposure: Exposure. Example: "-2_2/3"
        :type exposure: str
        :return: Response of the request.
        :rtype: req.models.Response
        """
        exposure_response = self.set_shooting_settings("exposure", exposure)
        self.logger.info("  - Exposure set to: %s", exposure)
        return exposure_response

    def set_white_balance(self, white_balance: str) -> req.models.Response:
        """Set white balance. Payload example: {"value": "auto"}

        :param white_balance: White balance. Example: "auto"
        :type white_balance: str
        :return: Response of the request.
        :rtype: req.models.Response
        """
        white_balance_response = self.set_shooting_settings(
            "whitebalance", white_balance
        )
        self.logger.info("  - White balance set to: %s", white_balance)
        return white_balance_response

    def set_color_temp(self, color_temp: int) -> req.models.Response:
        """Set color temperature. Payload example: {"value": 4000}

        :param color_temp: Color temperature. Example: 4000
        :type color_temp: int
        :return: Response of the request.
        :rtype: req.models.Response
        """
        color_temp_response = self.set_shooting_settings("colortemperature", color_temp)
        self.logger.info("  - Color temperature set to: %s", str(color_temp))
        return color_temp_response

    def shutter(self, af: bool = False) -> req.models.Response:
        """Take a picture. Payload example: {"af": False}.
        Set the AF/MF tab on the camera to the AF side to enable automatic focus.

        :param af: Auto focus. Key value for payload., defaults to False
        :type af: bool, optional
        :return: Shutter button response.
        :rtype: req.models.Response
        """
        af = bool(af)  # int [0|1] -> int::bool [False|True]
        payload = {"af": af}
        api_str = self.get_full_uri("/shooting/control/shutterbutton")
        shot = self.http_post(api_str, payload)
        self.logger.info("  - Shutter button pressed")
        return shot

    def dump_attributes(self, ouput_path: str = "camera_settings.json") -> None:
        """Dump all settings to JSON file.

        :param ouput_path: Path to the output file., defaults to "camera_settings.json"
        :type ouput_path: str, optional
        :return: Dumped settings.
        :rtype: Dict
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
