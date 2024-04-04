import pytest
import xarray as xr
from numpy.testing import assert_allclose
from numpy import deg2rad
from subprocess import run

from om3utils.cice_grid import CiceGridNc

# ----------------
# test data:


class MomGrid:
    """Generate a sample tripole grid to use as test data"""

    def __init__(self, tmp_path):
        self.path = str(tmp_path) + "/ocean_hgrid.nc"
        self.mask_path = str(tmp_path) + "/ocean_mask.nc"

        # generate an tripolar grid as test data
        run(
            [
                "ocean_grid_generator.py",
                "-r",
                "0.25",  # 4 degree grid
                "--no_south_cap",
                "--ensure_nj_even",
                "-f",
                self.path,
            ]
        )

        # open ocean_hgrid.nc
        self.ds = xr.open_dataset(self.path)

        # an ocean mask with a arbitrary mask
        self.mask_ds = xr.Dataset()
        self.mask_ds["mask"] = (self.ds.area.coarsen(ny=2).sum().coarsen(nx=2).sum()) > 5e9
        self.mask_ds.to_netcdf(self.mask_path)


class CiceGrid:
    """Make the CICE grid, using script under test"""

    def __init__(self, mom_grid, tmp_path):
        self.path = str(tmp_path) + "/grid.nc"
        self.kmt_path = str(tmp_path) + "/kmt.nc"
        cice_grid = CiceGridNc(self.path, self.kmt_path)
        cice_grid.build_from_mom(mom_grid.path, mom_grid.mask_path)
        self.ds = xr.open_dataset(self.path, decode_cf=False)
        self.kmt_ds = xr.open_dataset(self.kmt_path, decode_cf=False)


# pytest doesn't support class fixtures, so we need these two constructor funcs
@pytest.fixture
def mom_grid(tmp_path):
    return MomGrid(tmp_path)


@pytest.fixture
def cice_grid(mom_grid, tmp_path):
    return CiceGrid(mom_grid, tmp_path)


@pytest.fixture
def test_grid_ds(mom_grid):
    # this generates the expected answers

    ds = mom_grid.ds

    test_grid = xr.Dataset()
    # corners of the cice grid are NE corner
    test_grid["ulat"] = deg2rad(ds.y.isel(nxp=slice(2, None, 2), nyp=slice(2, None, 2)))
    test_grid["ulon"] = deg2rad(ds.x.isel(nxp=slice(2, None, 2), nyp=slice(2, None, 2)))

    # centers of cice grid
    test_grid["tlat"] = deg2rad(ds.y.isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2)))
    test_grid["tlon"] = deg2rad(ds.x.isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2)))

    # length of top edge of cells
    test_grid["htn"] = ds.dx.isel(nyp=slice(2, None, 2)).coarsen(nx=2).sum() * 100
    # length of right edge of cells
    test_grid["hte"] = ds.dy.isel(nxp=slice(2, None, 2)).coarsen(ny=2).sum() * 100

    # angle at u point
    test_grid["angle"] = deg2rad(ds.angle_dx.isel(nyp=slice(2, None, 2), nxp=slice(2, None, 2)))
    # angle a t points
    test_grid["angleT"] = deg2rad(ds.angle_dx.isel(nyp=slice(1, None, 2), nxp=slice(1, None, 2)))

    # area of cells
    test_grid["tarea"] = mom_grid.ds.area.coarsen(ny=2).sum().coarsen(nx=2).sum()

    # uarea is area of a cell centred around the u point
    # we need to wrap in latitude and fold on longitude to calculate this
    area_wrapped = mom_grid.ds.area
    area_wrapped = xr.concat([ds.area.isel(nx=slice(1, None)), ds.area.isel(nx=0)], dim="nx")

    top_row = xr.concat([ds.area.isel(ny=-1, nx=slice(-2, 0, -1)), ds.area.isel(ny=-1, nx=[-1, 0])], dim="nx")

    area_folded = xr.concat([area_wrapped.isel(ny=slice(1, None)), top_row], dim="ny")

    test_grid["uarea"] = area_folded.coarsen(ny=2).sum().coarsen(nx=2).sum()

    return test_grid


# ----------------
# the tests in earnest:


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_cice_var_list(cice_grid, test_grid_ds):
    # Test : Are there missing vars in cice_grid?
    assert set(test_grid_ds.variables).difference(cice_grid.ds.variables) == set()


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_cice_grid(cice_grid, test_grid_ds):
    # Test : Is the data the same as the test_grid
    for jVar in test_grid_ds.variables:
        assert_allclose(cice_grid.ds[jVar], test_grid_ds[jVar], rtol=1e-13, verbose=True, err_msg=f"{jVar} mismatch")


def test_cice_kmt(mom_grid, cice_grid):
    # Test : does the mask match
    mask = mom_grid.mask_ds.mask
    kmt = cice_grid.kmt_ds.kmt

    assert_allclose(mask, kmt, rtol=1e-13, verbose=True, err_msg="mask mismatch")


def test_cice_grid_attributes(cice_grid):
    # Test: do the expected attributes to exist in the cice ds
    cf_attributes = {
        "ulat": {"standard_name": "latitude", "units": "radians"},
        "ulon": {"standard_name": "longitude", "units": "radians"},
        "tlat": {"standard_name": "latitude", "units": "radians"},
        "tlon": {"standard_name": "longitude", "units": "radians"},
        "uarea": {
            "standard_name": "cell_area",
            "units": "m^2",
            "grid_mapping": "crs",
            "coordinates": "ulat ulon",
        },
        "tarea": {
            "standard_name": "cell_area",
            "units": "m^2",
            "grid_mapping": "crs",
            "coordinates": "tlat tlon",
        },
        "angle": {
            "standard_name": "angle_of_rotation_from_east_to_x",
            "units": "radians",
            "grid_mapping": "crs",
            "coordinates": "ulat ulon",
        },
        "angleT": {
            "standard_name": "angle_of_rotation_from_east_to_x",
            "units": "radians",
            "grid_mapping": "crs",
            "coordinates": "tlat tlon",
        },
        "htn": {"units": "cm", "coordinates": "ulat tlon", "grid_mapping": "crs"},
        "hte": {"units": "cm", "coordinates": "tlat ulon", "grid_mapping": "crs"},
    }

    for iVar in cf_attributes.keys():
        print(cice_grid.ds[iVar])

        for jAttr in cf_attributes[iVar].keys():
            assert cice_grid.ds[iVar].attrs[jAttr] == cf_attributes[iVar][jAttr]


def test_crs_exist(cice_grid):
    # Test: has the crs been added ?
    # todo: open with GDAL and rioxarray and confirm they find the crs?
    assert hasattr(cice_grid.ds, "crs")
    assert hasattr(cice_grid.kmt_ds, "crs")


def test_inputs_logged(cice_grid, mom_grid):
    # Test: have the source data been logged ?

    for ds in [cice_grid.ds, cice_grid.kmt_ds]:
        assert hasattr(ds, "inputfile"), "inputfile attribute missing"
        assert hasattr(ds, "inputfile_md5"), "inputfile md5sum attribute missing"

        sys_md5 = run(["md5sum", ds.inputfile], capture_output=True, text=True)
        sys_md5 = sys_md5.stdout.split(" ")[0]
        assert ds.inputfile_md5 == sys_md5, f"inputfile md5sum attribute incorrect, {ds.inputfile_md5} != {sys_md5}"

    assert (
        cice_grid.ds.inputfile == mom_grid.path
    ), "inputfile attribute incorrect ({cice_grid.ds.inputfile} != {mom_grid.path})"
    assert (
        cice_grid.kmt_ds.inputfile == mom_grid.mask_path
    ), "mask inputfile attribute incorrect ({cice_grid.kmt_ds.inputfile} != {mom_grid.mask_path})"
