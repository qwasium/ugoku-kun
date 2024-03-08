import os
import time
import warnings
import logging
import shutil

import pandas as pd

from control_cannon import ControlCannon


class UgokuKun:
    """
    Control multiple cannon cameras and turntable.

    Attributes
    ----------
    csv_path : str
        Path of the csv file.
    csv_df : pandas.DataFrame
        DataFrame of the csv file.
    log_path : str
        Path of the log txt file.
    wait_time : float
        Wait time between attempts.
    max_attempts : int
        Maximum number of attempts.
    req_timeout : tuple
        Timeout of the request.
    uris : list of str
        URI of the cameras.
    """

    def __init__(
        self,
        camera_addresses,
        csv_path,
        log_path="./log.txt",
        wait_time=0,
        max_attempts=5,
        req_timeout=(3.0, 7.5),
    ):

        self.wait_time = wait_time
        self.max_attempts = max_attempts
        self.req_timeout = req_timeout

        # csv
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"{csv_path} not found.")
        self.csv_path = csv_path
        self.csv_df = pd.read_csv(csv_path, header=None, index_col=None)

        # log
        self.log_path = log_path
        if not os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")

        # camera
        if camera_addresses is None:
            # camera_addresses = {"camera1": "192.168.1.2:8080"}
            raise ValueError("camera_addresses is required.")
        self.cameras = {}
        for camera, camera_address in camera_addresses.items():
            self.cameras[camera] = ControlCannon(
                wait_time=self.wait_time,
                max_attempts=self.max_attempts,
                req_timeout=self.req_timeout,
                ip_port=camera_address,
            )
