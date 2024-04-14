Welcome to Ugoku-kun's documentation!
=====================================

**Ugoku-kun** is a Python library for structure from motion (SfM) using Cannon camera and Keigan motor.

What is Ugoku-kun and who is it for?
------------------------------------

This Python library is for SfM photography setups using Cannon camera and a turntabel.

**The Setup**:

* The object to be photographed is placed on a turntable and the camera(s) are placed around the turntable.
* The turntable and camera(s) are controlled by Ugoku-kun.
* Turn the turntable and take photos of the object from different angles.
* The photos are then used to create a 3D model of the object.

**Components**:

* Cannon camera(s) compatible with Cannon's `ccapi <https://asia.canon/en/campaign/developerresources/sdk#digital-camera>`_.
* Turn table using Keigan Motor compatible wit Keigan's `pykeigan <https://github.com/keigan-motor/pykeigan_motor>`_.

By using a user-defined task CSV file...

**Ugoku-kun can**:

* Take photo with Cannon camera.
* Set simple camera settings with Cannon camera.
* Rotate turn table with Keigan Motor.

**Ugoku-kun cannot**:

* Synchronize shutter for multiple cameras when taking photos.
* Rotate turn table with absolute position (only relative position is supported).

Installation
------------

Install from PyPI

.. code-block:: bash

    # Will not work yet
    pip install Ugoku-kun

Links
-----

* GitHub: https://github.com/qwasium/ugoku-kun/tree/main
* PyPI: https://pypi.org/project/Ugoku-kun/


Overview and Quickstart
-----------------------

.. toctree::
    :maxdepth: 1
    :caption: Contents:

    overview
    task_csv

Package Reference
-----------------

.. toctree::
    :maxdepth: 1
    :caption: Package Reference:

    ugokukun.ugoku_kun
    ugokukun.cannon_wrapper
    ugokukun.keigan_wrapper
    ugokukun.ugoku_helpers

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
