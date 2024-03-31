"""Wrapper for the pykeigan library, the official library for Keigan motor."""

import os
import time
import subprocess
import logging

import serial
import serial.tools.list_ports
from pykeigan import usbcontroller, utils
import timeout_decorator


class KeiganWrapper:
    """Class to supplement the pykeigan library, the official library for Keigan motor.

    Attributes
    ----------
    port : str
        Serial port to connect to.
    baudrate : int
        Baudrate for serial communication.
    motor : pykeigan.usbcontroller.USBController
        Motor object.
        motor.serial is the serial.Serial object.
    speed : int
        Motor speed in rpm.
    log_path : str
        Path to log file.
    logger : logging.Logger
        Logger object.

    Notes
    -----
    Anything not implemented in this class -> access directly from motor object.
    pykeigan is poorly documented so I advise you to just go read the source code.
    https://github.com/keigan-motor/pykeigan_motor/tree/master
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        speed: int = 30,
        baudrate: int = 115200,
        log_path: str = "log.txt",
    ):
        """Connect to Keigan motor.

        Parameters
        ----------
        port : str, optional
            Serial port to connect to., by default "/dev/ttyUSB0"
        speed : int, optional
            Motor speed in rpm., by default 30
        baudrate : int, optional
            Baudrate., by default 115200
        log_path : str, optional
            Path to log file. If file doesn't exist, it will be created., by default "log.txt"

        Raises
        ------
        ValueError
            Port not available.
        """

        # check if probided port is available
        serial_ports = serial.tools.list_ports.comports()
        available_ports = [port.device for port in serial_ports]
        if port not in available_ports:
            raise ValueError(f"Port {port} not available.")

        # set serial port attributes
        self.port = port
        self.baudrate = baudrate
        self.speed = speed

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

        # close serial port if it's already open
        # still needs work
        if os.name == "nt":
            # windows not implemented yet
            serial.Serial(self.port, self.baudrate).close()
        else:
            # This will kill this process if ran the second time on the same port.
            command = f"fuser -k {self.port}"
            print(
                f"NOTICE: attempting to kill any process using the serial port: {self.port}"
            )
            try:
                shell_return = subprocess.run(
                    command, shell=True, capture_output=True, check=True, text=True
                )
                print("  - shell return: ", shell_return)
            except subprocess.CalledProcessError as e:
                print("  - shell error: ", e.stderr)

        print("  - Connecting to motor...")

        # connect to motor
        self.motor = None
        self.connect_motor()

        # turn off LED so it doesn"t affect the camera
        self.motor.set_led(0, 0, 0, 0)  # (LED state:0==OFF, Red:0, Green:0, Blue:0)

        # motor doesn't turn off automatically so it might be already turning
        self.motor.disable_action()

        # set speed
        self.motor.set_speed(utils.rpm2rad_per_sec(self.speed))

        # # initialize current motor position to 0
        # self.motor.preset_position(0)

        # set notify position arrival settings
        # self.motor.set_notify_pos_arrival_settings(True, utils.deg2rad(1), 1)

        # set acceleration curve
        self.motor.set_curve_type(0)

        # # message connected
        # # there is no way to check if the connection was successful
        # print("\n#####################################################################")
        self.logger.info("Initialized Keigan motor at: ")
        self.logger.info("  - %s", self.port)
        # print("#####################################################################\n")

    @timeout_decorator.timeout(5, timeout_exception=serial.SerialTimeoutException)
    def connect_motor(self) -> None:
        """pykeigan.usbcontorller.USBcontroller() with timeout."""
        # disconnect if already connected
        if self.motor is not None:
            if self.motor.is_connected():
                self.motor.disconnect()

        self.motor = usbcontroller.USBController(port=self.port, baud=self.baudrate)
        print(
            "Probably connected to Keigan motor (not sure until it's used).\n",
            "  If this is not the first connection to the motor,",
            "it can get stuck in an endless loop in:\n",
            "  - pykeigan.usbcontroller.USBController.reconnect()\n",
            "  If the connection works fine, you can just ignore it.",
        )

    def turn_relative(self, clock_wise: False, degrees: int) -> None:
        """Turn motor based on relative position.

        Parameters
        ----------
        clock_wise : bool, optional
            Direction to turn the motor. Clockwise if True, counter-clockwise if False., by default False
        degrees : int
            Degrees to rotate. Will accept negative values, if that's what you want.

        Raises
        ------
        ValueError
            If the motor is not connected.
        """
        self.motor.enable_action()
        if clock_wise:
            degrees = -degrees
        self.motor.move_by_dist_wait(utils.deg2rad(degrees))

        # wait for the motor to finish turning
        # second = degrees to turn / (6 * rpm)
        wait_time = abs(degrees / (self.speed * 6))
        time.sleep(wait_time)

        direction = "clockwise" if clock_wise else "counter-clockwise"
        self.logger.info(
            "Motor turned %d degrees %s at %d rpm.", degrees, direction, self.speed
        )
