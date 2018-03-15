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
This module contains grid definitions for regular gridded ECMWF data products (netcdf format)
'''

import numpy as np
from pygeogrids.grids import BasicGrid

def get_grid_resolution(lats, lons):
    lats = np.unique(lats)
    lons = np.unique(lons)
    lats_res, lons_res = [], []

    for i,j in zip(lats[:-1], lats[1:]):
        lats_res.append(np.abs(np.abs(j)-np.abs(i)))
    lats_res = np.round(np.array(lats_res), 3)
    if not all(lats_res == lats_res[0]):
        raise Exception('Grid not regular')
    else:
        lat_res = lats_res[0]

    for i,j in zip(lons[:-1], lons[1:]):
        lons_res.append(np.abs(np.abs(j)-np.abs(i)))
    lons_res = np.round(np.array(lons_res), 3)
    if not all(lons_res == lons_res[0]):
        raise Exception('Grid not regular')
    else:
        lon_res = lons_res[0]
    return lat_res, lon_res



def ERA_RegularImgGrid(res_lat=0.3, res_lon=0.3):
    '''
    ECMWF 0.25deg cell grid.
    :return: global QDEG-CellGrid
    '''
    lon = np.arange(0, 360 - res_lon / 2, res_lon)
    lat = np.arange(90, -1 * 90 - res_lat / 2, -1 * res_lat)
    lons_gt_180 = np.where(lon > 180.0)
    lon[lons_gt_180] = lon[lons_gt_180] - 360

    lon, lat = np.meshgrid(lon, lat)

    return BasicGrid(lon.flatten(), lat.flatten()).to_cell_grid(cellsize=5.)


def ECMWF025LandGrid():
    #TODO: add function to generate TS from land points only, use land mask (param: 172) to detect land points
    raise NotImplementedError

