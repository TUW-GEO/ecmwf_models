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

"""
Common grid definitions for ECMWF model reanalysis products (regular gridded)
"""

import numpy as np
from pygeogrids.grids import BasicGrid
from netCDF4 import Dataset
import os

def get_grid_resolution(lats, lons):
    lats = np.unique(lats)
    lons = np.unique(lons)
    lats_res, lons_res = [], []

    for i, j in zip(lats[:-1], lats[1:]):
        lats_res.append(np.abs(np.abs(j)-np.abs(i)))
    lats_res = np.round(np.array(lats_res), 3)
    if not all(lats_res == lats_res[0]):
        raise ValueError('Grid not regular')
    else:
        lat_res = lats_res[0]

    for i, j in zip(lons[:-1], lons[1:]):
        lons_res.append(np.abs(np.abs(j)-np.abs(i)))
    lons_res = np.round(np.array(lons_res), 3)
    if not all(lons_res == lons_res[0]):
        raise ValueError('Grid not regular')
    else:
        lon_res = lons_res[0]
    return float(lat_res), float(lon_res)

def ERA5_RegularImgLandGrid(res_lat=0.25, res_lon=0.25):
    """
    Uses the 0.25 DEG ERA5 land mask to create a land grid of the same size,
    which also excluded Antarctica.
    """
    try:
        ds = Dataset(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                  'era5', 'land_definition_files',
                                  'landmask_{dlat}_{dlon}.nc'.format(
                                      dlat=res_lat, dlon=res_lon)))
    except FileNotFoundError as e:
        print('Land definition for this grid resolution not yet available. Please create and add it.')
        raise e

    global_grid = ERA_RegularImgGrid(res_lat, res_lon)

    land_mask = ds.variables['land'][:].flatten().filled(0.) == 1.
    land_points = np.ma.masked_array(global_grid.get_grid_points()[0], ~land_mask)

    land_grid = global_grid.subgrid_from_gpis(land_points[~land_points.mask].filled().astype('int'))

    return land_grid.to_cell_grid(5., 5.)

def ERA_RegularImgGrid(res_lat=0.25, res_lon=0.25):
    """
    Create ECMWF regular cell grid

    Parameters
    ----------
    res_lat : float, optional (default: 0.25)
        Resolution in Y direction
    res_lon : float, optional (default: 0.25)
        Resolution in X direction

    Returns
    ----------
    CellGrid : pygeogrids.CellGrid
        Regular, global CellGrid with 5DEG*5DEG cells
    """
    # np.arange is not precise...
    f_lon = (1. / res_lon)
    f_lat = (1. / res_lat)
    res_lon = res_lon * f_lon
    res_lat = res_lat * f_lat
    lon = np.arange(0., 360. * f_lon, res_lon)
    lat = np.arange(90. * f_lat, -90 * f_lat - res_lat, -1 * res_lat)
    lons_gt_180 = np.where(lon > (180. * f_lon))
    lon[lons_gt_180] = lon[lons_gt_180] - (360. *f_lon)

    lon, lat = np.meshgrid(lon, lat)

    glob_basic_grid = BasicGrid(lon.flatten() / f_lon, lat.flatten()  / f_lat)
    glob_cell_grid = glob_basic_grid.to_cell_grid(cellsize=5.)

    return glob_cell_grid

def ERA_IrregularImgGrid(lons, lats):
    lons_gt_180 = np.where(lons > 180.0)
    lons[lons_gt_180] = lons[lons_gt_180] - 360
    return BasicGrid(lons.flatten(), lats.flatten()).to_cell_grid(cellsize=5.)