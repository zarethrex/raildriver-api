"""RailDriver API for Python."""

import pydantic
import typing
import pefile
import ctypes
import pathlib

from .file_system import get_raildriver_dll, check_raildriver_running
from .data import LocoInfo

T = typing.TypeVar("T", bound=object)

type RailDriverMethod[T] = typing.Callable[..., T]

type CType = ctypes.c_bool | ctypes.c_float | ctypes.c_char | ctypes.c_char_p | ctypes.c_int


@pydantic.validate_call(config={"arbitrary_types_allowed": True})
def check_in_dll(
    func_name: str,
    *,
    ctype_argtypes: list[type[CType]] | None,
    ctype_restype: type[CType] | None,
) -> typing.Callable[
    [RailDriverMethod[T]],
    RailDriverMethod[T],
]:
    """Decorator for verifying DLL function setup."""

    def _inner_decorator(
        func: RailDriverMethod[T],
    ) -> RailDriverMethod[T]:
        def _wrapper(
            self: "RailDriver", *args: str | float, **kwargs: str | float
        ) -> T:
            if ctype_argtypes:
                setattr(getattr(self.cdll, func_name), "argtypes", ctype_argtypes)
            if ctype_restype:
                setattr(getattr(self.cdll, func_name), "restype", ctype_restype)
            if func_name not in self.get_dll_members():
                raise RuntimeError(
                    f"Method '{func_name}' in RailDriver class not found in DLL."
                )
            return func(self, *args, **kwargs)

        return _wrapper

    return _inner_decorator


class RailDriver:
    def __init__(self, x86: bool = False) -> None:
        self._raildriver_dll: pathlib.Path = get_raildriver_dll(use_x86=x86)

        if not check_raildriver_running(use_x86=x86):
            raise RuntimeError(
                f"RailDriver Utility ({'x32' if x86 else 'x64'}) is not running."
            )

        self._cdll: ctypes.CDLL = ctypes.cdll.LoadLibrary(f"{self._raildriver_dll}")

    @property
    def cdll(self) -> ctypes.CDLL:
        """Get the DLL library."""
        return self._cdll

    @property
    @check_in_dll(
        "GetControllerList", ctype_restype=ctypes.c_char_p, ctype_argtypes=None
    )
    def controller_list(self) -> list[str]:
        """Get the next raildriver ID."""
        _controller_list: str = getattr(self._cdll, "GetControllerList")().decode()
        if not _controller_list:
            raise RuntimeError(
                "Could not find control list, is the RailDriver utility running?"
            )
        return _controller_list.split("::")

    @property
    @check_in_dll("GetLocoName", ctype_argtypes=None, ctype_restype=ctypes.c_char_p)
    def current_train(self) -> LocoInfo:
        """Get Current Loco Name."""
        _loco_name: str = getattr(self._cdll, "GetLocoName")().decode()
        if not _loco_name:
            raise RuntimeError(
                "Could not find control list, is the RailDriver utility running?"
            )
        _loco_information: list[str] = _loco_name.split(".:.")
        return LocoInfo(**dict(zip(("author", "product", "train"), _loco_information)))

    @check_in_dll(
        "GetControllerValue",
        ctype_argtypes=[ctypes.c_int, ctypes.c_int],
        ctype_restype=ctypes.c_float,
    )
    def get_controller_value(
        self, name: str, value_type: typing.Literal["min", "max", "current"]
    ) -> float:
        """Retrieve the value for the given control by index."""
        try:
            _control_index: int = self.controller_list.index(name)
        except IndexError:
            raise ValueError(f"Unrecognised control name '{name}'")

        _value_type_index: int = ("current", "min", "max").index(value_type)
        _controller_value = getattr(self._cdll, "GetControllerValue")(
            _control_index, _value_type_index
        )
        return typing.cast("float", _controller_value)

    @check_in_dll(
        func_name="SetControllerValue",
        ctype_argtypes=[ctypes.c_int, ctypes.c_float],
        ctype_restype=None,
    )
    @pydantic.validate_call
    def set_controller_value(self, name: str, value: float) -> None:
        """Set the value of a control."""
        try:
            _control_index: int = self.controller_list.index(name)
        except IndexError:
            raise ValueError(f"Unrecognised control name '{name}'")

        getattr(self._cdll, "SetControllerValue")(_control_index, value)

    def get_dll_members(self) -> list[str]:
        """Get all entries from the Raildriver DLL."""
        _portable_exe_file = pefile.PE(self._raildriver_dll)
        if (_export := getattr(_portable_exe_file, "DIRECTORY_ENTRY_EXPORT")) and (
            _symbols := getattr(_export, "symbols")
        ):
            _func_names: list[str] = typing.cast(
                "list[str]",
                [entry.name.decode("utf-8") for entry in _symbols if entry.name],
            )
            return _func_names
        raise RuntimeError("Failed to read entries from Raildriver DLL")
