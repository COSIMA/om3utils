import numpy as np
import pytest
from pathlib import Path
import xarray as xr

from om3utils.profiling import ProfilingParser, parse_profiling_data


class MockProfilingParser(ProfilingParser):
    def __init__(self, data: dict):
        super().__init__()

        self._metrics = ["hits", "tmin", "tmax", "tavg"]
        self._data = data

    @property
    def metrics(self) -> list:
        return self._metrics

    def read(self, path: Path) -> dict:
        return self._data[path.name]


@pytest.fixture()
def simple_scaling_runs(tmp_path, profiling_data):
    regions, ncpus, hits, tmin, tmax, tavg = profiling_data

    data = {}
    run_dirs = []
    for i in range(len(ncpus)):
        run_name = f"run_{ncpus[i]}"
        run_dir = tmp_path / run_name
        run_dirs.append(run_dir.as_posix())
        data[run_name] = dict(region=regions, hits=hits[i], tmin=tmin[i], tmax=tmax[i], tavg=tavg[i])

    parser = MockProfilingParser(data)

    return run_dirs, parser


def test_parse_profiling_data(tmp_path, simple_scaling_runs, simple_scaling_data):
    run_dirs, parser = simple_scaling_runs

    def get_ncpus(run_dir):
        return int(run_dir.name.split("_")[1])

    stats = parse_profiling_data(run_dirs, parser, "ncpus", get_ncpus)

    assert stats.equals(simple_scaling_data)
