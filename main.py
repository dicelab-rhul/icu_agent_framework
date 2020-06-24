#!/usr/bin/env python3

__author__ = "cloudstrife9999"

from sys import version_info, exit
from json import load

from icu_environment.icu_environment import ICUEnvironment


def check_preconditions() -> None:
    minimum_major = 3
    minimum_minor = 6
    minimum_version = "{}.{}".format(minimum_major, minimum_minor)

    if version_info.major < minimum_major or version_info.minor < minimum_minor:
        print("The minimum required version of Python is {}, while {}.{} was found.".format(minimum_version, version_info.major, version_info.minor))
        exit(-1)


# TODO: check whether or not to load a saved state.
def main() -> None:
    check_preconditions()

    with open("config.json", "r") as i_f:
        config: dict = load(fp=i_f)

    ICUEnvironment(config=config)
   

if __name__ == "__main__":
    main()
