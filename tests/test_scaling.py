import pytest

from om3utils.profiling_analyses import scaling_ncpus, scaling_speedup, scaling_efficiency


@pytest.fixture()
def scaling_run_dir(tmp_path):
    file = tmp_path / "config.yaml"
    file.write_text("ncpus: 4")


def test_scaling_ncpus(tmp_path, scaling_run_dir):
    ncpus = scaling_ncpus(tmp_path)

    assert ncpus == 4


def test_scaling_speedup(simple_scaling_data):
    speedup = scaling_speedup(simple_scaling_data)

    assert (speedup.sel(region="Total runtime").values[:] == [1.0, 2.0, 2.0]).all()


def test_efficiency(simple_scaling_data):
    efficiency = scaling_efficiency(simple_scaling_data)

    assert (efficiency.sel(region="Total runtime").values[:] == [100.0, 100.0, 50.0]).all()
