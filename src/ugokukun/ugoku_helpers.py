import json
from typing import List, Dict, Union

import numpy as np


class UgokuHelpers:
    """Helper functions for ugoku-kun.

    All methods are static.
    """

    @staticmethod
    def import_json(
        fpath: str, decode: str = "utf-8", content_is_str: bool = False
    ) -> Union[Dict, List]:
        """Take a json file and import it

        Parameters
        ----------
        fpath : str
            import file path
        decode : str, optional
            file encoding, by default "utf-8"
        content_is_str : bool, optional
            True if entire file content is pure string, by default False
            Sometimes, json gets read as a single string, so this method re-loads the laoded data.

        Returns
        -------
        Union[Dict, List]
            imported json data

        Raises
        ------
        FileNotFoundError
            File not found
        """
        with open(fpath, "r", encoding=decode) as file:
            data = json.load(file)

        # sometimes data comes out as a str, in that case, convert it to a list/dict
        if not content_is_str and isinstance(data, str):
            data = json.loads(data)

        return data

    @staticmethod
    def strtobool(
        bool_str: str, true_str: List[str] = None, false_str: List[str] = None
    ) -> bool:
        """Workaround for distutils.util.strtobool getting deprecated.

        Parameters
        ----------
        bool_str : str
            String to be converted to bool. numpy.bool is accepted as type str.
        true_str : List[str], optional
            List of strings that represent True, by default ["true", "t", "yes", "y", "1", "mark"]
        false_str : List[str], optional
            List of strings that represent False, by default ["false", "f", "no", "n", "0", "space"]

        Returns
        -------
        bool
            Converted bool. If numpy.bool is passed, it will return as is.

        Raises
        ------
        ValueError
            Could not convert to bool
        """
        if isinstance(bool_str, np.bool):
            # numpy.bool does not have .lower() attribute
            return bool_str

        # magic strings
        if true_str is None:
            true_str = ["true", "t", "yes", "y", "1", "mark"]
        if false_str is None:
            false_str = ["false", "f", "no", "n", "0", "space"]

        bool_str = bool_str.lower()
        if bool_str in true_str:
            return True
        elif bool_str in false_str:
            return False
        else:
            raise ValueError(f"Could not convert to bool: {bool_str}")
