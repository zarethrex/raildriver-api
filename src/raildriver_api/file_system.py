"""Utilities for location the local TSClassic installation."""

import typing

import pathlib
import winreg
import psutil
import re

__all__ = ["get_raildriver_dll"]


def find_tsclassic() -> pathlib.Path:
    """Locate the TSClassic program on the current file system."""
    _railworks_registry_key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\RailSimulator.com\RailWorks"
    )
    _railworks_path, _ = winreg.QueryValueEx(_railworks_registry_key, "Install_Path")
    _steam_path = typing.cast("str", _railworks_path)
    return pathlib.Path(_steam_path)


def get_raildriver_dll(*, use_x86: bool = False) -> pathlib.Path:
    """Retrieve the location of the Raildriver DLL."""
    _railworks_plugins_directory = find_tsclassic().joinpath("plugins")

    _dll_file_name: str = f"raildriver{'' if use_x86 else '64'}.dll"

    if not (_dll_location := _railworks_plugins_directory.joinpath(_dll_file_name)):
        raise FileNotFoundError(
            "Failed to locate Raildriver DLL file, "
            + f"'{_dll_file_name}' not found in '{_railworks_plugins_directory}'"
        )
    if not _dll_location.exists():
        raise FileNotFoundError(
            f"Location '{_dll_location}' in Windows registry does not exist."
        )
    return _dll_location


def check_raildriver_running(use_x86: bool) -> bool:
    """Check if the RailDriver Utility is running."""
    _raildriver_process_x64: re.Pattern[str] = re.compile(r"^RailDriver_\w+_x64.exe")
    _raildriver_process_x86: re.Pattern[str] = re.compile(r"^RailDriver_\w+_x32.exe")

    _raildriver_search = _raildriver_process_x86 if use_x86 else _raildriver_process_x64

    for process in psutil.process_iter(["name"]):
        if re.match(_raildriver_search, process.info["name"]):
            return True
    return False
