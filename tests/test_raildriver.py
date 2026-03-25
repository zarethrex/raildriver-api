from typing import Literal
import pytest
import pathlib
import winreg

from raildriver_api.file_system import (
    check_raildriver_running,
    find_tsclassic,
    get_raildriver_dll,
)

from raildriver_api import RailDriver


@pytest.mark.unit
@pytest.mark.file_system
def test_check_raildriver_running_pass(mock_rd_running) -> None:
    _ = mock_rd_running
    assert check_raildriver_running(use_x86=False)


@pytest.mark.unit
@pytest.mark.file_system
def test_check_raildriver_running_fail() -> None:
    assert not check_raildriver_running(use_x86=True)


@pytest.mark.unit
@pytest.mark.file_system
def test_find_railworks_directory(mock_winreg: str) -> None:
    _railworks_expected_dir = pathlib.Path(mock_winreg)
    assert find_tsclassic() == _railworks_expected_dir


@pytest.mark.unit
@pytest.mark.file_system
@pytest.mark.parametrize("scenario", ("x86", "x64"))
def test_find_cdll(mock_winreg: str, scenario: Literal["x86", "x64"]) -> None:
    _plugins_expected_path = pathlib.Path(mock_winreg).joinpath("plugins")

    if scenario == "x64":
        assert get_raildriver_dll(use_x86=False) == _plugins_expected_path.joinpath(
            "RailDriver64.dll"
        )
    else:
        assert get_raildriver_dll(use_x86=True) == _plugins_expected_path.joinpath(
            "RailDriver.dll"
        )


@pytest.mark.unit
@pytest.mark.raildriver
def test_raildriver_list_controllers(mock_dll, mock_rd_running) -> None:
    """Test RailDriver can list controllers."""
    assert "Horn" in RailDriver().controller_list


@pytest.mark.unit
@pytest.mark.raildriver
def test_get_loco_name(mock_dll, mock_rd_running) -> None:
    """Test Loco Name Retrieval."""
    _loco_name = RailDriver().current_train
    assert _loco_name.author == "Author"
    assert _loco_name.product == "TestPack"
    assert _loco_name.train == "TestLoco"


@pytest.mark.unit
@pytest.mark.raildriver
@pytest.mark.parametrize(
    "control,value_type",
    [
        ("Horn", "max"),
        ("Regulator", "min"),
        ("Damper", "current"),
        ("FireboxCoal", "current"),
        ("WaterTankLevel", "current"),
    ],
    ids=("Horn", "Regulator", "Damper", "FireboxCoal", "WaterTankLevel"),
)
def test_controller_value(
    mock_dll, mock_rd_running, control: str, value_type: str
) -> None:
    """Test controller value retrieval."""
    _ = RailDriver().get_controller_value(control, value_type)
    RailDriver().set_controller_value(control, 100)
