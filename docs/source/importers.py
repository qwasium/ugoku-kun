"""
helper functions for scraping
Nov 2023 SK
Python3.10.12 Ubuntu22
"""

import os
import sys


class AddPath:
    """
    safely add a path to sys.path for importing modules

    sys.path.insert might not add the path if it is already there
    and sys.path.remove might remove the wrong path if it occurs

    reference:
    https://stackoverflow.com/questions/17211078/how-to-temporarily-modify-sys-path-in-python

    Parameters
    ----------
    path : str
        path to add to sys.path
        always absolute path

    Example
    -------
    lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'path', 'to', 'lib')
    with AddPath(lib_path):
        module = __import__('mymodule')

    """

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            sys.path.remove(self.path)
        except ValueError:
            pass


class JumpDir:
    """
    change directory for reading/saving files, importing modules and other operations and return to the original directory

    Parameters
    ----------
    target_path : str
        path to change to
        can be relative path

    start_path : str
        path of starting returning directory
        absulute path is recommended

    Example
    -------
    for jupyter notebook, use os.getcwd() instead of __file__
    jupyter notebook cannnot know the location of the script so manually check your path

    with JumpDir(os.path.join('..', 'paht', 'to', 'lib'), os.path.dirname(os.path.abspath(__file__))):
        contents = os.listdir()

    """

    def __init__(self, target_path, start_path):
        self.path = target_path
        self.home = start_path

    def __enter__(self):

        # check if current directory is the location of the script
        if os.getcwd() != self.home:
            os.chdir(self.home)
            print("current directory is not the location of the script")
            print(f"cd {self.home}")

        try:
            os.chdir(self.path)
        except FileNotFoundError:
            print(f"path does not exist: {self.path}")
            print(f"your current path  : {os.getcwd()}")
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.home)
