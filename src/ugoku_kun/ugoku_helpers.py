import json
from typing import List, Dict, Union


class UgokuHelpers:
    """Helper functions for ugoku-kun."""

    @staticmethod
    def import_json(
        fpath: str, decode: str = "utf-8", content_is_str: bool = False
    ) -> Union[Dict, List]:
        """Takes a json file and imports it
        If you are certain that the content is a string, set content_is_str to True

        :param fpath: import file path
        :type fpath: str
        :param decode: file encoding, defaults to "utf-8"
        :type decode: str, optional
        :param content_is_str: True if entire file content is pure string, defaults to False
        :type content_is_str: bool, optional
        :return: imported json data
        :rtype: Union[Dict, List]
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

        :param bool_str: String to be converted to bool.
        :type bool_str: str
        :param true_str: List of strings that represent True, defaults to ["true", "t", "yes", "y", "1", "mark"]
        :type true_str: List[str], optional
        :param false_str: List of strings that represent False, defaults to ["false", "f", "no", "n", "0", "space"]
        :type false_str: List[str], optional
        :raises ValueError: Could not convert to bool
        :return: Converted bool.
        :rtype: bool
        """
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
