import json
import time
import warnings
import requests as req

from ugoku_helpers import UgokuHelpers as helpers


def _req_handle(func):
    def wrapper(instance, api_str, *args, **kwargs):
        """Handle HTTP requests and only return when status_code is 200, raise error otherwise."""
        # Check if api is available
        assert api_str in instance.api_url, "API not available: " + str(api_str)

        helpers.logger("API URL: " + str(api_str))

        # Try to get response for max_attempts times
        for attempt in range(instance.max_attemts):
            if attempt > 0:
                time.sleep(instance.wait_time)

            try:
                response = func(instance, api_str, *args, **kwargs)

            # timeout
            except req.exceptions.Timeout as timeout_err:
                if attempt < instance.max_attemts - 1:
                    helpers.logger("  - timeout, retrying...")
                    continue
                warnings.warn("Timeout: " + str(api_str))
                raise timeout_err

            # network problems
            except req.exceptions.ConnectionError as connection_err:
                if attempt < instance.max_attemts - 1:
                    helpers.logger("  - ConnectionError, retrying...")
                    continue
                warnings.warn("ConnectionError: " + str(api_str))
                raise connection_err

            # invalid HTTP response
            except req.exceptions.HTTPError as http_err:
                if attempt < instance.max_attemts - 1:
                    helpers.logger("  - HTTPError, retrying...")
                    continue
                warnings.warn("HTTPError: " + str(api_str))
                raise http_err

            # bad URL
            except req.exceptions.TooManyRedirects as redirect_err:
                if attempt < instance.max_attemts - 1:
                    helpers.logger("  - TooManyRedirects, retrying...")
                    continue
                warnings.warn("TooManyRedirects: " + str(api_str))
                raise redirect_err

            # all exceptions that requests can raise
            except req.exceptions.RequestException as req_err:
                if attempt < instance.max_attemts - 1:
                    helpers.logger("  - RequestException, retrying...")
                    continue
                warnings.warn("RequestException: " + str(api_str))
                raise req_err

            # continue if response is not valid
            if hasattr(response, "status_code") is False:
                helpers.logger("  - Invalid (no status code), retrying...")
                continue

            # return if success
            if response.status_code == 200:
                helpers.logger("  - Request success: 200")
                return response
            # continue if failed
            else:
                helpers.logger(
                    "  - Request failed, retrying: " + str(response.status_code)
                )
                continue

        # if failed
        helpers.logger("  - Failed to get response: " + str(api_str))
        assert hasattr(response, "status_code"), "I'm a teapot: NO status code returned"
        raise ConnectionError("I'm a teapot: " + str(response.status_code))

    return wrapper


class ControlCannon:
    """Control cannon camera.

    Attributes
    ----------
    wait_time : float
        Wait time between requests.
    req_timeout : tuple
        Timeout of the request.
        Default==(3.0, 7.5)
    ip_port : str
        IP address and port of the camera.
        Format : "IPv4:port"
        "xxxx.xxxx.xxxx.xxxx:yyyy"
    ip_address : str
        IP address of the camera.
    port : str
        Port of the camera.
    uri : str
        URI of the camera.
    max_attempts : int
        Maximum number of attempts.
    available_api : dict
        Available API of the camera.
        Example:
        {"ver100": [{
            "delete": False,
            "get"   : True,
            "put"   : False,
            "url"   : "http://..."
        }, {...}], ...}
    ver : str
        Version of the camera.
    api_url : list of str
        API URL of the camera
    device_info : dict
        Device information.
    exposure : dict
        Current exposure settings.
    whitebalance : dict
        Current white balance settings.
    iso : dict
        Current ISO settings.
    settings : dict
        Current shooting parameters.
    """

    def __init__(
        self,
        wait_time=3,
        max_attempts=5,
        req_timeout=(3.0, 7.5),
        ip_port="192.168.1.2:8080",
        auto_power_off=False,
    ):
        """Initialize connector by connecting to cannon camera and disabling auto power off.

        Parameters
        ----------
        wait_time : float
            Wait time between attempts.
        max_attempts : int
            Maximum number of attempts.
        req_timeout : tuple
            Timeout of the request.
        ip_address : str
            IP address of the camera.
        port : str
            Port of the camera.
        ip_port : str
            IP address and port of the camera.
            Format : "IP address :port"
            Default: "192.168.1.2:8080"

        """
        # set attributes
        self.wait_time = wait_time
        self.req_timeout = req_timeout
        self.ip_port = ip_port
        self.ip_address = ip_port.split(":")[0]
        self.port = ip_port.split(":")[1]
        self.uri = f"http://{ip_port}/ccapi"
        self.max_attemts = max_attempts

        # shooting parameters set later
        self.settings = {}
        self.exposure = {}
        self.whitebalance = {}
        self.iso = {}

        # Initialize connection
        self.api_url = [self.uri]  # set to make first request
        self.available_api = self.http_get(self.uri).json()
        helpers.logger("  - Connection established")
        self.ver = str(list(self.available_api.keys())[0])  # "ver100"
        self.api_url = [api["url"] for api in self.available_api[self.ver]]
        self.device_info = self.http_get(
            self.uri + "/" + self.ver + "/deviceinformation"
        ).json()
        helpers.logger("  - Acquired device information")
        helpers.logger(
            "\n###############################################################"
        )
        helpers.logger("Connected to Cannon camera: ")
        helpers.logger("  - " + self.device_info["productname"])
        helpers.logger("  - " + self.ip_port)
        helpers.logger(
            "###############################################################\n"
        )

        # Disable auto power off
        if not auto_power_off:
            self.kill_auto_power_off()

    @_req_handle
    def http_get(self, api_str):
        """HTTP get request."""
        return req.get(api_str, timeout=self.req_timeout)

    @_req_handle
    def http_post(self, api_str, payload):
        """HTTP post request."""
        return req.post(api_str, json=payload, timeout=self.req_timeout)

    @_req_handle
    def http_put(self, api_str, payload):
        """HTTP put request."""
        return req.put(api_str, json=payload, timeout=self.req_timeout)

    @_req_handle
    def http_delete(self, api_str):
        """HTTP delete request."""
        return req.delete(api_str, timeout=self.req_timeout)

    def kill_auto_power_off(self):
        """Kill auto power off.

        Returns
        -------
        power_off : requests.models.Response
            Auto power off result.
        """
        auto_off_api = self.uri + "/" + self.ver + "/functions/autopoweroff"
        auto_off = self.http_put(auto_off_api, payload={"value": "disable"})
        helpers.logger(
            "  - Auto power off is disabled: " + auto_off.content.decode("utf-8")
        )
        return auto_off

    def get_shooting_param(self):
        """Get all shooting parameters.

        Returns
        -------
        settings : requests.models.Response
            Shooting parameters.

        """
        settings_api = self.uri + "/" + self.ver + "/shooting/settings"
        settings = self.http_get(settings_api)
        helpers.logger(
            "  - Current shooting parameters: " + settings.content.decode("utf-8")
        )
        self.settings = settings.json()
        self.iso = self.settings["iso"]
        self.exposure = self.settings["exposure"]
        self.whitebalance = self.settings["whitebalance"]
        return settings

    def shutter(self, payload=None):
        """Take a picture.

        Parameters
        ----------
        payload : dict
            Payload to be sent to the camera.

        Returns
        -------
        shot : requests.models.Response
            Shutter button response.

        Note
        ----
        Set the AF/MF tab on the camera to the AF side to enable automatic focus.
        """
        if payload is None:
            payload = {"af": False}
        api_str = self.uri + "/" + self.ver + "/shooting/control/shutterbutton"
        shot = self.http_post(api_str, payload)
        helpers.logger("  - Shutter button pressed")
        return shot

    def dump_attributes(self, ouput_path=""):
        """Dump all settings."""
        dump_dict = {}
        return
