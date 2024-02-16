import pytest
import xarray as xr


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
