import pytest

# from test_utils import MockFile
from om3utils.MOM6InputParser import MOM6InputParser
from unittest.mock import mock_open, call


@pytest.fixture()
def mom6_input():
    return [
        "! === HEADER 1 ===\n",
        "REGRIDDING_COORDINATE_MODE = ZSTAR   ! default = 'LAYER''\n",
        "                                     ! Coordinate mode for vertical regridding. Choose among the following\n",
        "! === HEADER 2 ===\n",
        "KPP%\n",
        "N_SMOOTH = 4                         ! default = 0\n",
        "                                     ! The number of times the 1-1-4-1-1 Laplacian filter is applied on OBL depth.\n",
        "%KPP\n",
        "DT = 1800.0\n",
        "BOOL = True\n",
    ]


@pytest.fixture()
def param_output():
    return {
        "REGRIDDING_COORDINATE_MODE": "ZSTAR",
        "KPP%": "",
        "N_SMOOTH": "4",
        "%KPP": "",
        "DT": "1800.0",
        "BOOL": "True",
    }


@pytest.fixture()
def commt_output():
    return {
        "REGRIDDING_COORDINATE_MODE": "default = 'LAYER''\n! Coordinate mode for vertical regridding. Choose among the following",
        "KPP%": "",
        "N_SMOOTH": "default = 0\n! The number of times the 1-1-4-1-1 Laplacian filter is applied on OBL depth.",
        "%KPP": "",
        "DT": "",
        "BOOL": "",
    }


def test_read_mom6_input(mocker, mom6_input):
    mocker.patch("builtins.open", mocker.mock_open(read_data="".join(mom6_input)))
    parser = MOM6InputParser()
    parser.read_input("tmp_path")
    assert parser.lines == mom6_input


def test_param_commt_output(mom6_input, param_output, commt_output):
    parser = MOM6InputParser()
    parser.lines = mom6_input
    parser.parse_lines()
    assert parser.param_dict == param_output
    assert parser.commt_dict == commt_output


def test_write_mom6_input(mocker, mom6_input):
    mock_file = mock_open()
    mocker.patch("builtins.open", mock_file)
    parser = MOM6InputParser()
    parser.lines = mom6_input
    parser.parse_lines()
    parser.writefile_MOM_input("tmp_path")  # write to the mock_file

    expected_calls = [
        call("! This file was written by the script xxx \n"),
        call("! and records the non-default parameters used at run-time.\n"),
        call("\n"),
        call("REGRIDDING_COORDINATE_MODE = ZSTAR ! default = 'LAYER''\n"),
        call(
            "                                 ! Coordinate mode for vertical regridding. Choose among the following\n"
        ),
        call("KPP%\n"),
        call("N_SMOOTH = 4                     ! default = 0\n"),
        call(
            "                                 ! The number of times the 1-1-4-1-1 Laplacian filter is applied on OBL depth.\n"
        ),
        call("%KPP\n"),
        call("DT = 1800.0\n"),
        call("BOOL = True\n"),
    ]

    mock_file().write.assert_has_calls(expected_calls, any_order=False)
