from pathlib import Path

import yaml

from exceptions.exceptions import *


class Config:
    def __init__(self):
        """Initialize"""
        self.config = None
        self.main()

    def main(self):
        """Read config file and set config in the variable."""

        # Check config file after call function.
        if self.check_file():
            with open(r"config/config.yaml") as f:
                self.config = yaml.load(f, Loader=yaml.FullLoader)

    def check_file(self):
        """The function check config file.

        Returns
        -------
            True : bool
                If file was founded.
            Error Message : FileError
                If file wasn't founded.
        """

        if not Path(r"config/config.yaml").is_file():
            raise FileError("'config.yaml' is not found")
        return True