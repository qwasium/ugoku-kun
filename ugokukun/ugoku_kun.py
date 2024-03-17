"""Control multiple cannon cameras and turntable."""

import os
import time
import json
import logging
from typing import Any, Tuple

import pandas as pd
from pykeigan import utils

from .cannon_wrapper import CannonWrapper
from .keigan_wrapper import KeiganWrapper
from .ugoku_helpers import UgokuHelpers as helpers


class UgokuKun:
    """
    Control multiple cannon cameras and turntable.

    """

    def __init__(
        self,
        task_csv_path: str,
        device_json_path: str,
        log_path: str = "log.txt",
        wait_time: float = 0.5,
        max_attempts: int = 20,
        req_timeout: Tuple[float, float] = (3.0, 7.5),
    ):
        """Initialize UgokuKun object.

        :param task_csv_path: Path of the task csv file.
        :type task_csv_path: str
        :param device_json_path: Path of the json file containing the device id and addresses.
        :type device_json_path: str
        :param log_path: Path of the log txt file., defaults to "log.txt"
        :type log_path: str, optional
        :param wait_time: Wait time between HTTP request attempts., defaults to 0.5
        :type wait_time: float, optional
        :param max_attempts: Maximum number of HTTP requests attempts., defaults to 20
        :type max_attempts: int, optional
        :param req_timeout: Timeout of the HTTP request., defaults to (3.0, 7.5)
        :type req_timeout: Tuple[float, float], optional
        :raises ValueError: No cameras found in the device json file.
        """
        self.wait_time = wait_time
        self.max_attempts = max_attempts
        self.req_timeout = req_timeout
        if self.wait_time * self.max_attempts < 2.0:
            print("NOTE: Camera might not respond fast enough with current parameters.")
            print("  - Current wait time: " + str(self.wait_time))
            print("  - Current max attempts: " + str(self.max_attempts))
        self.device_json_path = device_json_path
        self.devices = helpers.import_json(device_json_path)

        # csv
        self.task_csv_path = task_csv_path
        self.csv_df = None
        self.load_task_csv(task_csv_path)

        # log
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

        # turn table
        self.keigan_motors = self.devices["keigan"]
        if not self.keigan_motors:
            self.logger.info("No Keigan devices found in the device json file.")
        self.keigan_instances = {}
        for motor, serial_port in self.keigan_motors.items():
            self.keigan_instances[motor] = KeiganWrapper(
                port=serial_port, log_path=self.log_path
            )

        # camera
        self.cannon_cameras = self.devices["cannon"]
        if not self.cannon_cameras:
            raise ValueError("No devices found in the device json file.")
        self.cannon_instances = {}
        for camera, camera_address in self.cannon_cameras.items():
            self.cannon_instances[camera] = CannonWrapper(
                wait_time=self.wait_time,
                max_attempts=self.max_attempts,
                req_timeout=self.req_timeout,
                ip_port=camera_address,
                log_path=self.log_path,
            )

    def load_task_csv(self, task_csv_path: str) -> pd.DataFrame:
        """Load a new csv file and overwrite the current self.csv_df.

        :param task_csv_path: Path of the csv file.
        :type task_csv_path: str
        :raises ValueError: Missing header or duplicate task_id.
        :return: The csv file as a pandas DataFrame.
        :rtype: pd.DataFrame
        """
        self.task_csv_path = task_csv_path
        self.csv_df = pd.read_csv(task_csv_path, header=0, index_col=None)

        # check if csv file has the correct headers
        csv_headers = list(self.csv_df.columns)
        must_have_headers = [
            "task_id",
            "wait_time",
            "target",
            "action",
            "param",
            "payload",
        ]
        for header in must_have_headers:
            if header not in csv_headers:
                raise ValueError(f"Missing header: {header}")

        # check if task_id includes duplicates
        task_id_list = self.csv_df["task_id"].to_list()
        if len(task_id_list) != len(set(task_id_list)):
            raise ValueError("task_id must be unique.")

        return self.csv_df

    def execute_row(self, row_index: int) -> None:
        """Execute a single row in the csv file.
        if self.csv_df.at[row_index, "target"] is:
            - "all": self.execute_all()
            - camera_id: self.execute_cannon()
            - keigan_id: self.execute_keigan()

        :param row_index: Index of the row to be executed.
        :type row_index: int
        :raises ValueError: Invalid target.
        """
        if self.csv_df.at[row_index, "target"] == "all":
            self.execute_all(row_index)

        # camera
        elif self.csv_df.at[row_index, "target"] in self.cannon_cameras.keys():
            self.execute_cannon(self.csv_df.at[row_index, "target"], row_index)

        # turn table
        elif self.csv_df.at[row_index, "target"] in self.keigan_motors.keys():
            self.execute_keigan(self.csv_df.at[row_index, "target"], row_index)

        else:
            raise ValueError(f"Invalid target: {self.csv_df.at[row_index, 'target']}")

    def execute_cannon(self, camera: str, row_index: int) -> Any:
        """Execute a single row in the csv file where target==camera_id.
        if self.csv_df.at[row_index, "action"] is:
            - "get": self.cannon_instances[camera].http_get()
            - "post": self.cannon_instances[camera].http_post()
            - "put": self.cannon_instances[camera].http_put()
            - "delete": self.cannon_instances[camera].http_delete()
            - "shutter": self.cannon_instances[camera].shutter()
            - "aperture": self.cannon_instances[camera].set_aperture()
            - "exposure": self.cannon_instances[camera].set_exposure()
            - "iso": self.cannon_instances[camera].set_iso()
            - "color_temperature": self.cannon_instances[camera].set_color_temp()
            - "white_balance": self.cannon_instances[camera].set_white_balance()
            - "shutter_speed": self.cannon_instances[camera].set_shutter_speed()

        :param camera: camera_id in the device json file.
        :type camera: str
        :param row_index: Index of the row of the csv to be executed.
        :type row_index: int
        :raises ValueError: Invalid action.
        :return: The return of the executed action. Most likely requests.Response object.
        :rtype: Any
        """
        # HTTP GET
        if self.csv_df.at[row_index, "action"] == "get":
            api_str = self.cannon_instances[camera].get_full_uri(
                self.csv_df.at[row_index, "param"]
            )
            return self.cannon_instances[camera].http_get(api_str)

        # HTTP POST
        if self.csv_df.at[row_index, "action"] == "post":
            api_str = self.cannon_instances[camera].get_full_uri(
                self.csv_df.at[row_index, "param"]
            )
            return self.cannon_instances[camera].http_post(
                api_str,
                json.loads(self.csv_df.at[row_index, "payload"]),
            )

        # HTTP PUT
        if self.csv_df.at[row_index, "action"] == "put":
            api_str = self.cannon_instances[camera].get_full_uri(
                self.csv_df.at[row_index, "param"]
            )
            return self.cannon_instances[camera].http_put(
                api_str,
                json.loads(self.csv_df.at[row_index, "payload"]),
            )

        # HTTP DELETE
        if self.csv_df.at[row_index, "action"] == "delete":
            api_str = self.cannon_instances[camera].get_full_uri(
                self.csv_df.at[row_index, "param"]
            )
            return self.cannon_instances[camera].http_delete(api_str)

        # Shutter
        if self.csv_df.at[row_index, "action"] == "shutter":
            if pd.isna(self.csv_df.at[row_index, "param"]):
                return self.cannon_instances[camera].shutter()
            do_autofocus = helpers.strtobool(self.csv_df.at[row_index, "param"])
            return self.cannon_instances[camera].shutter(do_autofocus)

        # Aperture
        if self.csv_df.at[row_index, "action"] == "aperture":
            return self.cannon_instances[camera].set_aperture(
                aperture=self.csv_df.at[row_index, "param"]
            )

        # Exposure
        if self.csv_df.at[row_index, "action"] == "exposure":
            return self.cannon_instances[camera].set_exposure(
                exposure=self.csv_df.at[row_index, "param"]
            )

        # ISO
        if self.csv_df.at[row_index, "action"] == "iso":
            return self.cannon_instances[camera].set_iso(
                iso=self.csv_df.at[row_index, "param"]
            )

        # Color Temperature
        if self.csv_df.at[row_index, "action"] == "color_temperature":
            return self.cannon_instances[camera].set_color_temp(
                color_temp=int(self.csv_df.at[row_index, "param"])
            )

        # White Balance
        if self.csv_df.at[row_index, "action"] == "white_balance":
            return self.cannon_instances[camera].set_white_balance(
                white_balance=self.csv_df.at[row_index, "param"]
            )

        # Shutter Speed
        if self.csv_df.at[row_index, "action"] == "shutter_speed":
            return self.cannon_instances[camera].set_shutter_speed(
                shutter_speed=self.csv_df.at[row_index, "param"]
            )

        raise ValueError(f"Invalid action: {self.csv_df.at[row_index, 'action']}")

    def execute_keigan(self, motor_id: str, row_index: int):
        """Execute a single row in the csv file where target==keigan_id.

        :param motor_id: motor_id in the device json file.
        :type motor_id: str
        :param row_index: Index of the row of the csv to be executed.
        :type row_index: int
        :raises ValueError: Invalid action.
        :return: Return of the executed action. Mostly None.
        :rtype: Any
        """

        if self.csv_df.at[row_index, "action"] == "cw":
            return self.keigan_instances[motor_id].turn_relative(
                clock_wise=True, degrees=int(self.csv_df.at[row_index, "param"])
            )

        if self.csv_df.at[row_index, "action"] == "ccw":
            return self.keigan_instances[motor_id].turn_relative(
                clock_wise=False, degrees=int(self.csv_df.at[row_index, "param"])
            )

        if self.csv_df.at[row_index, "action"] == "speed":
            return self.keigan_instances[motor_id].motor.set_speed(
                utils.rpm2rad_per_sec(int(self.csv_df.at[row_index, "param"]))
            )

        raise ValueError(f"Invalid action: {self.csv_df.at[row_index, 'action']}")

    def execute_all(self, row: int):
        """Actions for target=="all"."""

        if self.csv_df.at[row, "action"] == "sleep":
            return

        raise ValueError(f"Invalid action: {self.csv_df.at[row, 'action']}")

    def dry_run(self) -> None:
        """Run all commannds in the csv file except WAIT commands.
        This method is useful to check if the commands are valid.
        Run this method before running the `run` method and fix if any errors are found.

        """
        for index, row in self.csv_df.iterrows():
            self.logger.info(
                "Executing task id: %s , action: %s", row["task_id"], row["action"]
            )
            self.execute_row(index)

    def run(self) -> None:
        """Run all commands in the csv file."""
        for index, row in self.csv_df.iterrows():
            time.sleep(row["wait_time"])
            self.logger.info(
                "Executing task id: %s , action: %s", row["task_id"], row["action"]
            )
            self.execute_row(index)
