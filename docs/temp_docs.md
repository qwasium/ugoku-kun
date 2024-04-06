# Temporary Documentation

This is a temporary documentation file. It will be deleted after the documentation is complete.

- Mar. 29, 2024
- Simon Kuwahara

For a quick start, see `readme_demo/readme.ipynb`.

## Class `CannonWrapper`

This class is a wrapper for the Canon camera API.

Note:

All HTTP requests are wrapped in the `_req_handle` method.
It is defined above `CannonWrapper`in `cannon_wrapper.py`.
This method will retry the request if it fails until it reaches the maximum number of attempts specified in the attribute `max_attempts` and will wait between requests for the specified time in the attribute `wait_time` between attempts.
Any error that could not be resolved by retrying will raise an exception and halt the program.

### `CannonWrapper()`

Constructor of cannon wrapper.
This class will be instantiated for each camera.

Parameters:

- wait_time: float
  - Wait time between attempts in seconds.
  - Defaults: 3
- max_attempts: int
  - Maximum number of HTTP request attempts.
  - Defaults: 5
- req_timeout: Tuple[float, float]
  - Request timeout.
- ip_port: str
  - IP address and port of the camera. Format is: {IP address}:{port}.
  - Defaults: "192.168.1.2:8080"
- auto_power_off: bool
  - Disables auto power off if False.
  - Defaults: False
- log_path: str
  - Path of log file for logging.
  - Defaults: "log.txt"

### `http_get()`

HTTP GET request.
It will be wrapped in @_req_handle

Parameters:

- api_str: str
  - API string to GET.

Returns:

- requests.models.Response

### `http_post()`

HTTP POST request.
It will be wrapped in @_req_handle

Parameters:

- api_str: str
  - API string to POST.
- payload: dict
  - Payload to POST.

Returns:

- requests.models.Response

### `http_put()`

HTTP PUT request.
It will be wrapped in @_req_handle

Parameters:

- api_str: str
  - API string to PUT.
- payload: dict
  - Payload to PUT.

Returns:

- requests.models.Response

### `http_delete()`

HTTP DELETE request.
It will be wrapped in @_req_handle

Parameters:

- api_str: str
  - API string to DELETE.
- payload: dict
  - Payload to DELETE.

Returns:

- requests.models.Response

### `get_full_uri()`

Parameters:

- api_str: str
  - API string after: "http://{self.ip_address}:{self.port}/ccapi/"version".
  - Example: "/shooting/control/shutterbutton".

Returns:

- str: Full API URL of the newest version of the input API.
  - Example: "http://192.168.1.2:8080/ccapi/ver100/shooting/control/shutterbutton"

### `kill_auto_power_off()`

Disables auto power off.

Returns:

- requests.models.Response

### `get_shooting_param()`

Get all shooting parameters and overwrite self.settings.

Returns:

- requests.models.Response

Note:

- self.settings["color_temperature"]["ability"] is changed to a list of available color temperatures.
  - Example:
	- Before: {"min": 2500, "max": 10000, "step": 100}
	- After:  [2500, 2600, 2700, ..., 10000]

### `set_shooting_settings()`

Wrapper for setting shooting parameters.

Parameters:

- param: str
  - Parameter to be set, such as:
	- "shutter_speed"
	- "aperture"
	- "iso"
	- "exposure"
	- "whitebalance"
	- "colortemperature"
  - Valid entries are hard coded in this method.
- value: str
  - Value of the parameter. Depends on the parameter. payload is {"value": value}

Returns:

- requests.models.Response

Raises:

- ValueError: If invalid `param` is provided.

### `set_shutter_speed()`

Set shutter speed.

Payload example: {"value": "5\""}

Parameters:

- shutter_speed: str
  - Shutter speed. Example: "5\""
  - The backslash in the above example is an escape character.

Returns:

- requests.models.Response

### `set_aperture()`

Set aperture.

Payload example: {"value": "f4.0"}

Parameters:

- aperture: str
  - Aperture. Example: "f4.0"

Returns:

- requests.models.Response

### `set_iso()`

Set ISO value.

Payload example: {"value": "3200"}

Parameters:

- iso: str
  - ISO. Example: "3200"

Returns:

- requests.models.Response

### `set_exposure()`

Set exposure.

Payload example: {"value": "-2_2/3"}

Parameters:

- exposure: str
  - Exposure. Example: "-2_2/3"

Returns:

- requests.models.Response

### `set_white_balance()`

Set white balance.

Payload example: {"value": "auto"}

Parameters:

- white_balance: str
  - White balance. Example: "auto"

Returns:

- requests.models.Response

### `set_color_temp()`

Set color temperature.

Payload example: {"value": 4000}

Parameters:

- color_temp: int
  - Color temperature. Example: 4000

Returns:

- requests.models.Response

### `shutter()`

Take a picture.

Parameters:

- af: bool
  - Auto focus. Key value for payload.
  - Defaults: False

Returns:

- requests.models.Response

### `dump_attributes()`

Dump all settings to JSON file.

Parameters:

- output_path: str
  - Path to the output file.
  - Defaults: "camera_settings.json"

Returns:

- Dict: Dumped settings.
  - Example:
  	- {
  		"shutter_speed": "1/100",
  		"aperture": "f4.0",
  		"iso": "3200",
  		"exposure": "-2_2/3",
  		"whitebalance": "auto",
  		"colortemperature": 4000
  	}

## Class `KeiganWrapper`

Wrapper for pykeigan library.

This class will be instantiated for each turntable.

Anything not implemented in this class is meant to ve accessed directly from motor object.
pykeigan is poorly documented so I advise you to just go read the source code.
https://github.com/keigan-motor/pykeigan_motor/tree/master

Attribute `motor`: pykeigan.usbcontroller.USBController

- Motor object.
- motor.serial is the serial.Serial object.

### `KeiganWrapper()`

Constructor of KeiganWrapper.

Parameters:

- port: str
  - Serial port to connect to.
  - Defaults: "/dev/ttyUSB0"
- speed: int
  - Motor speed in rpm.
  - Defaults: 30
- baudrate: int
  - Baudrate.
  - Defaults: 115200
- log_path: str
  - Path to log file. If file doesn't exist, it will be created.
  - Defaults: "log.txt"

Raises:

- ValueError: Port not available.

Note:

- If the port is not available, it will raise a ValueError.
- If the port is available but the motor is already connected, a subroutine will go into an infinite loop of retrying to connect. This is a bug in pykeigan and annoying, but is probably not a problem.

### `connect_motor()`

pykeigan.usbcontorller.USBcontroller() with timeout using `timeout_decorator`.

This is method is extracted just to have a timeout to the pykeigan method. It is called when the object is instantiated.

This method fails solve the problem for robustness, so idealy, pykeigan should be forked and modified to have a timeout in the source code.

## `turn_relative()`

Turn motor by relative position.

This method will wait for the motor to finish turning.
Rotation by absolute position is not implemented in this class.
This is because it is hard to know when the motor has finished turning due to limitations in pykeigan.

Parameters:

- clock_wise: bool
  - Direction to turn the motor. Clockwise if True, counter-clockwise if False.
  - Defaults: False
- degrees: int
  - Degrees to rotate. Will accept negative values, if that's what you want.

## Class `UgokuKun`

Control multiple cannon cameras and Keigan turntables with user defined csv task table.

### `UgokuKun()`

Initialize UgokuKun object.

It will read device json and create CannonWrapper and KeiganWrapper objects for each device.

Parameters:

- task_csv_path: str
  - Path of the task csv file.
  - See README.md and readme_demo for the format of the task csv.
- device_json_path: str
  - Path of the json file containing the device id and addresses.
  - See README.md and readme_demo for the format of the device json.
- log_path: str
  - Path of the log txt file.
  - Defaults: "log.txt"
- wait_time: float
  - Wait time between HTTP request attempts.
  - Defaults: 0.5
- max_attempts: int
  - Maximum number of HTTP requests attempts.
  - Defaults: 20
- req_timeout: Tuple[float, float]
  - Timeout of the HTTP request.
  - Defaults: (3.0, 7.5)

Raises:

- ValueError: No cameras found in the device json file.

#### `load_task_csv()`

Load a new csv file and overwrite the current self.csv_df.

Parameters:

- task_csv_path: str
  - Path of the csv file.

Returns:

- pd.DataFrame: The csv file as a pandas DataFrame.

Raises:

- ValueError: If the csv file does not have the correct headers or has duplicate task_id.

### `execute_row()`

Execute a single row in the csv file.

If `self.csv_df.at[row_index, "target"]` is:

- "all": `self.execute_all()`
- camera_id: `self.execute_cannon()`
- keigan_id: `self.execute_keigan()`

Parameters:

- row_index: int
  - Index of the row to be executed.

Raises:

- ValueError: Invalid target.

### `execute_cannnon()`

Execute a single row in the csv file where target==camera_id.

If `self.csv_df.at[row_index, "action"]` is:

- "get": `self.cannon_instances[camera].http_get()`
- "post": `self.cannon_instances[camera].http_post()`
- "put": `self.cannon_instances[camera].http_put()`
- "delete": `self.cannon_instances[camera].http_delete()`
- "shutter": `self.cannon_instances[camera].shutter()`
- "aperture": `self.cannon_instances[camera].set_aperture()`
- "exposure": `self.cannon_instances[camera].set_exposure()`
- "iso": `self.cannon_instances[camera].set_iso()`
- "color_temperature": `self.cannon_instances[camera].set_color_temp()`
- "white_balance": `self.cannon_instances[camera].set_white_balance()`
- "shutter_speed": `self.cannon_instances[camera].set_shutter_speed()`

Parameters:

- camera: str
  - camera_id in the device json file.
- row_index: int
  - Row index of the csv to be executed.

Raises:

- ValueError: Invalid action.

### `execute_keigan()`

Execute a single row in the csv file where target==keigan_id.

See README.md for the actions.

Parameters:

- motor_id: str
  - motor_id in the device json file.
- row_index: int
  - Index of the row of the csv to be executed.

Raises:

- ValueError: Invalid action.

### `execute_all()`

Execute a single row in the csv file where target=="all".

`self.csv_df.at[row_index, "action"]` == "sleep" is only supported for now.

Parameters:

- row_index: int
  - Index of the row of the csv to be executed.

### `test_run()`

Run all commannds in the csv file except WAIT commands.

This method is useful to check if the commands are valid.
Run this method before running the `run` method and fix if any errors are found.

### `run()`

Run all commands in the csv file.

## Class `UgokuHelpers`

Helper functions for UgokuKun.

All methods are static.

### `get_device_json()`

Takes a json file and imports it.

Static method.

Parameters:

- fpath: str
  - Import file path.
- decode: str
  - File encoding.
  - Defaults: "utf-8"
- content_is_str: bool
  - True if entire file content is pure string.
  - If you are certain that the content is a string, set content_is_str to True
  - Defaults: False

Returns:

- Union[Dict, List]: Imported json data.

### `strtobool()`

Workaround for distutils.util.strtobool getting deprecated.

Parameters:

- bool_str: str
  - String to be converted to bool.
- true_str: List[str]
  - List of strings that represent True.
  - Defaults: ["true", "t", "yes", "y", "1", "mark"]
- false_str: List[str]
  - List of strings that represent False.
  - Defaults: ["false", "f", "no", "n", "0", "space"]

Returns:

- bool: Converted bool.

Raises:

- ValueError: Could not convert to bool.
