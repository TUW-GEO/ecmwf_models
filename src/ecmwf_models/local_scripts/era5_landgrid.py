# -*- coding: utf-8 -*-

'''
Module description
'''
# TODO # (+) 

# NOTES # -

from netCDF4 import Dataset
import matplotlib as mpl
import numpy as np
from collections import OrderedDict
mpl.use("Qt5Agg")


def make_era5_land_definition_file(lsm_file=r"C:\Temp\era5_grid\ERA5_AN_20100101_0000.nc",
                                   out_file=r"C:\Temp\era5_landgrid\landgrid.nc"):
    lsm_var = 'lsm'

    ds = Dataset(lsm_file)

    # drop the unncessary stuff
    for var in ds.variables:
        if (var != lsm_var) and var not in list(ds.dims.keys()) + ['time']:
            print(var)
            ds = ds.drop(var)

    lsm = ds.variables[lsm_var]
    lsm.values[lsm.values>=0.5]=1.
    lsm.values[lsm.values<0.5]=0.

    # drop values below -56° Lat
    lsm.values[601:,:] = np.nan


    lsm.attrs = OrderedDict([('units', '(0,1)'),('long_name', 'Land-sea mask'),
                             ('standard_name', 'land_binary_mask'),
                             ('threshold_land', '>=0.5')])

    ds = ds.rename({'lsm': 'land'})

    ds.to_netcdf(out_file, encoding={var: {'zlib': True, 'complevel': 9} for var in ds.variables})



make_era5_land_definition_file()