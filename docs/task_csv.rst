Task CSV Reference
==================

Headers
-------

The csv file must have the following headers or it will raise an error.:

* task_id (str): Unique ID of the task. Any Duplicate task_id will raise an error.
* wait_time (float): Time to wait from the previous task. In seconds.
* target (str): The device to control. Must be a device ID defined in the device list JSON.
* action (str): Depends on target. See below.
* param (str): Depends on action. See below.
* payload (str): Depends on action. See below.

Target == "Cannon camera ID"
-----------------------------

* action == "get": HTTP GET request.
  * param: The URL to GET.
* action == "post": HTTP POST request.
  * param: The URL to POST.
  * payload: The payload to POST.
* action == "put": HTTP PUT request.
  * param: The URL to PUT.
  * payload: The payload to PUT.
* action == "delete": HTTP DELETE request.
  * param: The URL to DELETE.
* action == "shutter": CannonWrapper.shutter()
  * param: do autofocus if True, else False
* action == "aperature": CannonWrapper.set_aperature()
  * param: aperture value
* action == "shutterspeed": CannonWrapper.set_shutterspeed()
  * param: shutterspeed value
* action == "iso": CannonWrapper.set_iso()
  * param: iso value
* action == "whitebalance": CannonWrapper.set_whitebalance()
  * param: whitebalance value
* action == "color_temperature": CannonWrapper.set_color_tempe()
  * param: color temperature value
* action == "white_balance": CannonWrapper.set_white_balance()
  * param: white balance value

Target == "Keigan turntable ID"
-------------------------------

* action == "cw": turn clockwise relative to current position
  * param: The angle to turn
* action == "ccw": turn counter-clockwise relative to current position
  * param: The angle to turn
* action == "speed": set speed
  * param: The speed in rpm

Target == "all"
---------------

* action == "wait": Halt entire system for specified in wait_time.