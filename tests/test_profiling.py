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
def profiling_data():
    regions = ["Total runtime", "Ocean Initialization"]
    ncpus = [1, 2, 4]
    hits = []
    tmin = []
    tmax = []
    tavg = []
    for n in ncpus:
        hits.append([1, 2])
        tmin.append([value / min(n, 2) for value in [138.600364, 2.344926]])
        tmax.append([value / min(n, 2) for value in [138.600366, 2.345701]])
        tavg.append([value / min(n, 2) for value in [600365, 2.345388]])

    return regions, ncpus, hits, tmin, tmax, tavg


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


@pytest.fixture()
def simple_scaling_data(profiling_data):
    regions, ncpus, hits, tmin, tmax, tavg = profiling_data

    return xr.Dataset(
        data_vars=dict(
            hits=(["ncpus", "region"], hits),
            tmin=(["ncpus", "region"], tmin),
            tmax=(["ncpus", "region"], tmax),
            tavg=(["ncpus", "region"], tavg),
        ),
        coords=dict(region=regions, ncpus=ncpus),
    )


def test_parse_profiling_data(tmp_path, simple_scaling_runs, simple_scaling_data):
    run_dirs, parser = simple_scaling_runs

    def get_ncpus(run_dir):
        return int(run_dir.name.split("_")[1])

    stats = parse_profiling_data(run_dirs, parser, "ncpus", get_ncpus)

    assert stats.equals(simple_scaling_data)
