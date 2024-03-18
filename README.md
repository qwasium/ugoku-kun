# ugoku-kun

This is a Python library for controlling Cannon cameras and Keigan Motor for SfM (Structure from Motion) applications.

This Python library is built as part of a internship project at the National Agriculture and Food Research Organization (NARO) in Japan.

## Codemap

- README.md: This file.
- ugoku_kun: The main package.
  - __init__.py
  - cannon_wrapper.py: The camera module.
  - keigan_wrapper.py: The Keigan Motor module.
  - ugoku_kun.py: The main module.
  - ugoku_helers.py: The utility module.
- docs: The documentation. WIP.
- tests/*: Tests, not automated, WIP.
- readme_demo: Read this for quick start.
  - readme.ipynb: READ THIS FIRST.

## Dependencies

This Python library is built on top of official APIs provided by Cannon and Keigan.

- Cannon's [ccapi](https://asia.canon/en/campaign/developerresources/sdk#digital-camera)
- Keigan's [pykeigan](https://github.com/keigan-motor/pykeigan_motor)

Tested on:

- Ubuntu 22.04
- Python 3.10.12
- Cannon EOS R100 firmware 1.6.0
- Keigan Motor KM-1S-M6829-TS
- pykeigan-motor 2.4.0 via pip

Should work on Windows too. ccapi is platform independent.

## Network Configuration

**Important**: Inappropriate settings can lead to connection issues.

Kill any "smart" features on your router that automatically adjusts configurations such as the following:

- Don't mix authentication methods -> If in doubt, use WPA2-PSK (AES) only
- Don't mix 2.4/5GHz bands -> set a dedicated SSID for 2.4GHz
- Don't mix channel width (20MHz/40MHz) -> set to either 20MHz ONLY or 40MHz ONLY
- Use channels 1-11 only -> Auto channel selection is OK as long as 12/13 channels are disabled

## Workflow

1. Create task csv and device json.
2. Set up camera(s) and turntable.
3. Adjust focus on camera(s).
4. Run Jupyter Notebook.
5. export log

## Device List JSON

All devices are identified by a unique ID. This ID is used to refer to the device in the task CSV.

```json
{
  "cannon": {
    "some_unique_camera_id": "ip_address:port"
  },
  "keigan": {
    "some_unique_turntable_id": "ip_address:port"
  }
}
```

## Task CSV

### Headers

The csv file must have the following headers or it will raise an error.:

- task_id (str): Unique ID of the task. Any Duplicate task_id will raise an error.
- wait_time (float): Time to wait from previous task. In seconds.
- target (str): The device to control. Must be a device ID defined in the device list JSON.
- action (str): Depends on target. See below.
- param (str): Depends on action. See below.
- payload (str): Depends on action. See below.

### Target == Cannon camera ID

- action == "get": HTTP GET request.
  - param: The URL to GET.
- action == "post": HTTP POST request.
  - param: The URL to POST.
  - payload: The payload to POST.
- action == "put": HTTP PUT request.
  - param: The URL to PUT.
  - payload: The payload to PUT.
- action == "delete": HTTP DELETE request.
  - param: The URL to DELETE.
- action == "shutter": CannonWrapper.shutter()
  - param: do autofocus if True, else False
- action == "aperature": CannonWrapper.set_aperature()
  - param: aperture value
- action == "shutterspeed": CannonWrapper.set_shutterspeed()
  - param: shutterspeed value
- action == "iso": CannonWrapper.set_iso()
  - param: iso value
- action == "whitebalance": CannonWrapper.set_whitebalance()
  - param: whitebalance value
- action == "color_temperature": CannonWrapper.set_color_tempe()
  - param: color temperature value
- action == "white_balance": CannonWrapper.set_white_balance()
  - param: white balance value

### Target == Keigan turntable ID

- action == "cw": turn clockwise relative to current position
  - param: The angle to turn
- action == "ccw": turn counter-clockwise relative to current position
  - param: The angle to turn
- action == "speed": set speed
  - param: The speed in rpm

### Target == "all"

- action == "wait": Halt entire system for specified in wait_time.


## Limitations

### ccapi

ccapi cannot get the setting values when set to "auto". It will just return "auto".
Also, getting file information needs some effort and I couldn't implement it yet.
It would be nice to at least get the file name of any photo taken.

### pykeigan

Though any official API is appreciated, pykeigan is not well documented so it is easier to read the source code to understand how to use it.
The software design is based on using it as a CLI tool, where the user is expected to read the console output and terminate the process via Ctrl+C when necessary.
Thus, methods won't return any useful information and reading attributes are also not that useful.
Subroutines can easily lead to non-terminating processes making it hard to handle with Python.
Anyone who wants to use this library in a serious production environment should fork the repository and make the necessary changes to the source code.

## TODO

1. Host documentation on readthedocs.
2. Package the code and host on PyPI.
