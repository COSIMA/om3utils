import pytest
from pathlib import Path

from test_utils import MockFile
from om3utils.fms_profiling import FMSProfilingParser


@pytest.fixture()
def simple_fms_stats():
    return {
        "region": [
            "Total runtime",
            "Ocean Initialization",
            "Ocean",
            "Ocean dynamics",
            "Ocean thermodynamics and tracers",
        ],
        "hits": [1.0, 2.0, 23.0, 96.0, 72.0],
        "tmin": [138.600364, 2.344926, 86.869466, 43.721019, 27.377185],
        "tmax": [138.600366, 2.345701, 86.871652, 44.391032, 33.281659],
        "tavg": [138.600365, 2.345388, 86.87045, 43.957944, 29.950144],
        "tstd": [1e-06, 0.000198, 0.000744, 0.244785, 1.792324],
        "tfrac": [1.0, 0.017, 0.627, 0.317, 0.216],
        "grain": [0.0, 11.0, 1.0, 11.0, 11.0],
        "pemin": [0.0, 0.0, 0.0, 0.0, 0.0],
        "pemax": [11.0, 11.0, 11.0, 11.0, 11.0],
    }


@pytest.fixture()
def simple_fms_output_file(tmp_path):
    file = tmp_path / "simple_output_file "
    output_str = """Some random stuff
over a few lines
with some number: 1, 2, 3
and special symbols: | /* #
then the actual profiling output:
                                   hits          tmin          tmax          tavg          tstd  tfrac grain pemin pemax
Total runtime                         1    138.600364    138.600366    138.600365      0.000001  1.000     0     0    11
Ocean Initialization                  2      2.344926      2.345701      2.345388      0.000198  0.017    11     0    11
Ocean                                23     86.869466     86.871652     86.870450      0.000744  0.627     1     0    11
Ocean dynamics                       96     43.721019     44.391032     43.957944      0.244785  0.317    11     0    11
Ocean thermodynamics and tracers     72     27.377185     33.281659     29.950144      1.792324  0.216    11     0    11
 MPP_STACK high water mark=           0
"""
    return MockFile(file, output_str)


def test_fms_profiling_read(tmp_path, simple_fms_output_file, simple_fms_stats):
    parser = FMSProfilingParser(simple_fms_output_file.file.name)
    stats = parser.read(tmp_path)

    assert stats == simple_fms_stats


def test_read_missing_fms_profiling_file():
    with pytest.raises(FileNotFoundError):
        parser = FMSProfilingParser("benchmark")
        parser.read(Path("garbage"))
