# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2018, TU Wien
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Module for reading reshuffled ECMWF mode data in netcdf time series format
'''

import os
from pygeogrids.netcdf import load_grid
from pynetcf.time_series import GriddedNcOrthoMultiTs

class ERATs(GriddedNcOrthoMultiTs):
    '''
     Time series reader for all ERA reanalysis products in time series format.

     Parameters
     ----------
     ts_path : str
         Directory where the netcdf time series files are stored
     grid_path : str, optional (default: None)
         Path to grid file, that is used to organize the location of time
         series to read. If None is passed, grid.nc is searched for in the
         ts_path.

     Optional keyword arguments that are passed to the Gridded Base:
     ------------------------------------------------------------------------
         parameters : list, optional (default: None)
             Specific variable names to read, if None are selected, all are read.
         offsets : dict, optional (default: None)
             Offsets (values) that are added to the parameters (keys)
         scale_factors : dict, optional (default: None)
             Offset (value) that the parameters (key) is multiplied with
         ioclass_kws: dict, (optional)

             Optional keyword arguments to pass to OrthoMultiTs class:
             ----------------------------------------------------------------
                 read_bulk : boolean, optional (default: False)
                     If set to True, the data of all locations is read into memory,
                     and subsequent calls to read_ts then read from cache and
                     not from disk. This makes reading complete files faster.
                 read_dates : boolean, optional (default: False)
                     If false, dates will not be read automatically but only on
                     specific request useable for bulk reading because currently
                     the netCDF num2date routine is very slow for big datasets.
     '''

    def __init__(self, ts_path, grid_path=None, **kwargs):

        if grid_path is None:
            grid_path = os.path.join(ts_path, "grid.nc")

        grid = load_grid(grid_path)
        super(ERATs, self).__init__(ts_path, grid, **kwargs)

if __name__ == '__main__':
    inpath = '/data-read/USERS/wpreimes/era5_ts/ts_out'
    ds = ERATs(inpath)
    ts = ds.read(16, 48)