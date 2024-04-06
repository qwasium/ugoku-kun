Task CSV Reference
==================

Ugoku-kun uses a csv file to define a sequence of tasks to execute.

This CSV file will define all actions to be performed by the system.

``ugokukun.ugoku_kun.run()`` will execute the tasks defined in the csv file from the top.

The csv file must be in the following format:

Headers
-------

.. table:: Task CSV Format
   +-----------+--------------+-----------------------+-----------+-----------+-----------+
   | task_id   | wait_time    | target                | action    | param     | payload   |
   +===========+==============+=======================+===========+===========+===========+
   | unique ID | time to wait | reference device json | see below | see below | see below |
   +-----------+--------------+-----------------------+-----------+-----------+-----------+

The csv file must have the following headers or it will raise an error.:

* ``task_id`` (str): Set a unique ID for each task. Any Duplicate task_id will raise an error.
* ``wait_time`` (float): Time to wait from the previous task in seconds.
* ``target`` (str): The device to control. Must be a device ID defined in the device list JSON.
* ``action`` (str): Depends on target. See below.
* ``param`` (str): Depends on action. See below.
* ``payload`` (str): Depends on action. See below.

Values in ``action``, ``param``, and ``payload`` depend on the target device.

See below for the possible values for each ``target`` type.

``Target`` == "Cannon camera ID"
--------------------------------

The possible ``action`` for a Cannon camera are:

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

``Target`` == "Keigan turntable ID"
-----------------------------------

The possible ``action`` for a Keigan turntable are:

* action == "cw": turn clockwise relative to current position
  * param: The angle to turn
* action == "ccw": turn counter-clockwise relative to current position
  * param: The angle to turn
* action == "speed": set speed
  * param: The speed in rpm

``Target`` == "all"
-------------------

The possible ``action`` for all devices are:

* action == "wait": Halt entire system for specified in wait_time.