import pytest
import xarray as xr
from numpy.testing import assert_allclose
from numpy import deg2rad

#im not sure how micael is importing om3utils?
import sys
import os
my_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(my_dir, '..'))

from om3utils.cice_grid import cice_grid_from_mom
from ocean_model_grid_generator.ocean_grid_generator import main as ocean_grid_generator

import warnings 

class MomGrid:

    """Generate a sample tripole grid to use as test data"""

    path = 'ocean_hgrid.nc' 
    mask_path = 'ocean_mask.nc' 

    def __init__(self):
        # generate an tripolar grid as test data
        args = {
            'inverse_resolution': 0.25 , #4 degree grid
            'no_south_cap': True,
            'ensure_nj_even': True,
            'match_dy': ["bp", "so", "p125sc", ""],
            'gridfilename': 'ocean_hgrid.nc'
        }

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category = RuntimeWarning)
            ocean_grid_generator(**args) #generates ocean_hgrid.nc

        self.ds = xr.open_dataset(self.path)

        # an ocean mask with a random mask 
        self.mask_ds = xr.Dataset()
        self.mask_ds['mask']=((self.ds.area.coarsen(ny=2).sum().coarsen(nx=2).sum())>5e9)
        self.mask_ds.to_netcdf(self.mask_path)

class CiceGrid:
    """Make the CICE grid, using script under test"""

    path = 'grid.nc'
    kmt_path = 'kmt.nc'
    def __init__(self, mom_grid):
        # the data under test
        cice_grid = cice_grid_from_mom() 
        cice_grid.run(mom_grid.path, mom_grid.mask_path)
        self.ds = xr.open_dataset(self.path,decode_cf=False)
        self.kmt_ds = xr.open_dataset(self.kmt_path, decode_cf=False)

def make_test_grid(mom_grid_ds):
    # this generates the expected answers

    test_grid = xr.Dataset()
    # corners of the cice grid are NE corner
    test_grid['ulat']=deg2rad(mom_grid_ds.y.isel(nxp=slice(2,None,2), nyp=slice(2,None,2)))
    test_grid['ulon']=deg2rad(mom_grid_ds.x.isel(nxp=slice(2,None,2), nyp=slice(2,None,2)))

    # centers of cice grid
    test_grid['tlat']=deg2rad(mom_grid_ds.y.isel(nxp=slice(1,None,2), nyp=slice(1,None,2)))
    test_grid['tlon']=deg2rad(mom_grid_ds.x.isel(nxp=slice(1,None,2), nyp=slice(1,None,2)))

    # length of top edge of cells
    test_grid['htn']=(mom_grid_ds.dx.isel(nyp=slice(2,None,2)).coarsen(nx=2).sum()*100)
    # length of right edge of cells
    test_grid['hte']=mom_grid_ds.dy.isel(nxp=slice(2,None,2)).coarsen(ny=2).sum()*100

    # angle at u point
    test_grid['angle']=deg2rad(mom_grid_ds.angle_dx.isel(nyp=slice(2,None,2), nxp=slice(2,None,2)))
    # angle a t points
    test_grid['angleT']=deg2rad(mom_grid_ds.angle_dx.isel(nyp=slice(1,None,2), nxp=slice(1,None,2)))

    # area of cells
    test_grid['tarea']=mom_grid_ds.area.coarsen(ny=2).sum().coarsen(nx=2).sum()

    # uarea is area of a cell centred around the u point
    # we need to wrap in latitude and fold on longitude to calculate this
    area_wrapped = mom_grid_ds.area
    area_wrapped = xr.concat([
        mom_grid_ds.area.isel(nx=slice(1,None)),
        mom_grid_ds.area.isel(nx=0)
    ], dim='nx')

    top_row = xr.concat([
        mom_grid_ds.area.isel(ny=-1, nx=slice(-2,0,-1)),
        mom_grid_ds.area.isel(ny=-1, nx=[-1,0])
    ], dim='nx')

    area_folded = xr.concat([
        area_wrapped.isel(ny=slice(1,None)),
        top_row
    ], dim='ny')

    test_grid['uarea'] = area_folded.coarsen(ny=2).sum().coarsen(nx=2).sum()

    return test_grid

@pytest.fixture
def mom_grid():
    return MomGrid()

@pytest.fixture
def cice_grid(mom_grid):
    return CiceGrid(mom_grid)

@pytest.mark.filterwarnings('ignore::DeprecationWarning')
def test_cice_grid(mom_grid, cice_grid):
    #to-do: run at high res?

    test_grid_ds = make_test_grid(mom_grid.ds)

    #Test1 : Are there missing vars in cice_grid?
    assert(set(test_grid_ds.variables).difference(cice_grid.ds.variables) == set() )

    #Test2 : Is the data correct
    for jVar in test_grid_ds.variables:
    
        anom = (cice_grid.ds[jVar].values-test_grid_ds[jVar].values)

        print(f'{jVar} anom min: {anom.min()}, anom max: {anom.max()}')

        assert_allclose(
            cice_grid.ds[jVar],
            test_grid_ds[jVar],
            rtol=1e-13,
            verbose=True,
            err_msg=f'{jVar} mismatch'
        )        

    pass

def test_cice_kmt(mom_grid, cice_grid):
    mask = mom_grid.mask_ds.mask
    kmt = cice_grid.kmt_ds.kmt

    assert_allclose(
            mask,
            kmt,
            rtol=1e-13,
            verbose=True,
            err_msg=f'mask mismatch'
        )     
    
    pass

def test_cice_grid_attributes(cice_grid):

    #expected attributes to exist in the ds
    cf_attributes = {
        'ulat': {'standard_name':'latitude', 'units':'radians'},
        'ulon': {'standard_name':'longitude', 'units':'radians'},
        'tlat': {'standard_name':'latitude', 'units':'radians'},
        'tlon': {'standard_name':'longitude', 'units':'radians'},
        'uarea': {'standard_name':'cell_area', 'units':'m^2', 'grid_mapping': 'crs','coordinates':'ulat ulon',},
        'tarea': {'standard_name':'cell_area', 'units':'m^2', 'grid_mapping': 'crs','coordinates':'tlat tlon',},
        'angle': {'standard_name':'angle_of_rotation_from_east_to_x', 'units':'radians', 'grid_mapping': 'crs','coordinates':'ulat ulon'},
        'angleT': {'standard_name':'angle_of_rotation_from_east_to_x', 'units':'radians', 'grid_mapping': 'crs','coordinates':'tlat tlon'},
        'htn': {'units':'cm', 'coordinates':'ulat tlon','grid_mapping':'crs'},
        'hte': {'units':'cm', 'coordinates':'tlat ulon','grid_mapping':'crs'}
    }

    for iVar in cf_attributes.keys():
        print(cice_grid.ds[iVar])
            
        for jAttr in cf_attributes[iVar].keys():
            assert cice_grid.ds[iVar].attrs[jAttr] == cf_attributes[iVar][jAttr]


def test_crs_exist(cice_grid):
    # todo: open with GDAL and rioxarray and confirm they find the crs?
    assert hasattr(cice_grid.ds, 'crs')
