from typing import Any, Callable
import tempfile
from collections.abc import Generator
import dataclasses
import pathlib
import pytest
import faker

_faker = faker.Faker()


class MockCDLLFunction:
    def __init__(self, wrapped_func: Callable) -> None:
        self._func = wrapped_func
        self.restype = None
        self.argtypes = None

    def __call__(self, *args, **kwargs) -> Any:
        return self._func(*args, **kwargs)


class DLLMocker:

    def __init__(self, *_, **__) -> None:
        self._controller_callbacks = {
            "Regulator": lambda: _faker.pyfloat(min_value=0, max_value=100),
            "Horn": lambda: _faker.pyint(min_value=0, max_value=1),
            "Damper": lambda: _faker.pyint(min_value=0, max_value=1),
            "FireboxCoal": lambda: _faker.pyfloat(min_value=0, max_value=1),
            "WaterTankLevel": lambda: _faker.pyfloat(min_value=0, max_value=1),
        }
        self.GetControllerValue = MockCDLLFunction(self._get_controller_value)
        self.SetControllerValue = MockCDLLFunction(self._set_controller_value)
        self.GetLocoName = MockCDLLFunction(self._get_loco_name)
        self.GetControllerList = MockCDLLFunction(self._get_controller_list)

    def _get_controller_value(self, control_index: int, _: int) -> float | int:
        _key = list(self._controller_callbacks.keys())[
            control_index % len(self._controller_callbacks)
        ]
        return self._controller_callbacks[_key]

    def _get_controller_list(self) -> bytes:
        return "::".join(self._controller_callbacks.keys()).encode("utf-8")

    def _set_controller_value(self, _: int, __: float) -> None:
        pass

    def _get_loco_name(self) -> bytes:
        return "Author.:.TestPack.:.TestLoco".encode("utf-8")


@dataclasses.dataclass
class MockSymbol:
    name: bytes


@dataclasses.dataclass
class MockDirectoryEntryPoint:
    symbols: list[MockSymbol] = dataclasses.field(
        default_factory=lambda: [
            MockSymbol("GetControllerList".encode("utf-8")),
            MockSymbol("SetControllerValue".encode("utf-8")),
            MockSymbol("GetControllerValue".encode("utf-8")),
            MockSymbol("GetLocoName".encode("utf-8")),
        ]
    )


@dataclasses.dataclass
class MockPE:
    name: str
    DIRECTORY_ENTRY_EXPORT: MockDirectoryEntryPoint = dataclasses.field(
        default_factory=MockDirectoryEntryPoint
    )


@dataclasses.dataclass
class MockProcess:
    info: dict[str, str] = dataclasses.field(
        default_factory=lambda: {"name": "RailDriver_TS2019_x64.exe"}
    )


@pytest.fixture
def mock_winreg(monkeypatch) -> Generator[str]:
    import winreg

    with tempfile.TemporaryDirectory() as tempd:
        _temp_dir = pathlib.Path(tempd)
        _temp_dir.joinpath("plugins").mkdir()
        _temp_dir.joinpath("plugins", "RailDriver64.dll").touch()
        _temp_dir.joinpath("plugins", "RailDriver.dll").touch()

        monkeypatch.setattr(winreg, "HKEY_LOCAL_MACHINE", "")
        monkeypatch.setattr(winreg, "OpenKey", lambda *_, **__: "")
        monkeypatch.setattr(winreg, "QueryValueEx", lambda *_, **__: (tempd, None))

        yield tempd


@pytest.fixture
def mock_dll(monkeypatch) -> None:
    import raildriver_api.file_system
    import pefile
    import ctypes

    monkeypatch.setattr(pefile, "PE", MockPE)
    monkeypatch.setattr(
        raildriver_api.file_system, "get_raildriver_dll", pathlib.Path("dummy.dll")
    )
    monkeypatch.setattr(ctypes.cdll, "LoadLibrary", DLLMocker)


@pytest.fixture
def mock_rd_running(monkeypatch) -> None:
    import psutil

    def mock_iter_process(*_, **__) -> Generator[MockProcess]:
        yield MockProcess()

    monkeypatch.setattr(psutil, "process_iter", mock_iter_process)
