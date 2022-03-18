# -*- coding: utf-8 -*-
"""
Common grid definitions for ECMWF model reanalysis products (regular gridded)
"""

import numpy as np
from pygeogrids.grids import BasicGrid, CellGrid
from netCDF4 import Dataset
import os
from typing import Tuple


def get_grid_resolution(lats: np.ndarray, lons: np.ndarray) -> (float, float):
    """
    try to derive the grid resolution from given coords.
    """
    lats = np.unique(lats)
    lons = np.unique(lons)
    lats_res, lons_res = [], []

    for i, j in zip(lats[:-1], lats[1:]):
        lats_res.append(np.abs(np.abs(j) - np.abs(i)))
    lats_res = np.round(np.array(lats_res), 3)
    if not all(lats_res == lats_res[0]):
        raise ValueError("Grid not regular")
    else:
        lat_res = lats_res[0]

    for i, j in zip(lons[:-1], lons[1:]):
        lons_res.append(np.abs(np.abs(j) - np.abs(i)))
    lons_res = np.round(np.array(lons_res), 3)
    if not all(lons_res == lons_res[0]):
        raise ValueError("Grid not regular")
    else:
        lon_res = lons_res[0]

    return float(lat_res), float(lon_res)


def ERA5_RegularImgLandGrid(
    res_lat: float = 0.25,
    res_lon: float = 0.25,
    bbox: Tuple[float, float, float, float] = None,
) -> CellGrid:
    """
    Uses the 0.25 DEG ERA5 land mask to create a land grid of the same size,
    which also excluded Antarctica.

    Parameters
    ----------
    res_lat: float, optional (default: 0.25)
        Grid resolution (in degrees) in latitude direction.
    res_lon: float, optional (default: 0.25)
        Grid resolution (in degrees) in longitude direction.
    bbox: tuple, optional (default: None)
        (min_lon, min_lat, max_lon, max_lat) - wgs84
        bbox to cut the global grid to.
    """
    try:
        ds = Dataset(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "era5",
                "land_definition_files",
                f"landmask_{res_lat}_{res_lon}.nc",
            ))
    except FileNotFoundError:
        raise FileNotFoundError(
            "Land definition for this grid resolution not yet available. "
            "Please create and add it.")

    global_grid = ERA_RegularImgGrid(res_lat, res_lon, bbox=None)

    land_mask = ds.variables["land"][:].flatten().filled(0.0) == 1.0
    land_points = np.ma.masked_array(global_grid.get_grid_points()[0],
                                     ~land_mask)

    land_grid = global_grid.subgrid_from_gpis(
        land_points[~land_points.mask].filled().astype("int"))

    land_grid = land_grid.to_cell_grid(5.0, 5.0)

    if bbox is not None:
        gpis = land_grid.get_bbox_grid_points(
            lonmin=bbox[0], latmin=bbox[1], lonmax=bbox[2], latmax=bbox[3])
        land_grid = land_grid.subgrid_from_gpis(gpis)

    return land_grid


def ERA_RegularImgGrid(
    res_lat: float = 0.25,
    res_lon: float = 0.25,
    bbox: Tuple[float, float, float, float] = None,
) -> CellGrid:
    """
    Create regular cell grid for bounding box with the selected
    resolution.

    Parameters
    ----------
    res_lat: float, optional (default: 0.25)
        Grid resolution (in degrees) in latitude direction.
    res_lon: float, optional (default: 0.25)
        Grid resolution (in degrees) in longitude direction.
    bbox: tuple, optional (default: None)
        (min_lon, min_lat, max_lon, max_lat) - wgs84
        bbox to cut the global grid to.

    Returns
    ----------
    CellGrid : CellGrid
        Regular, CellGrid with 5DEG*5DEG cells for the passed bounding box.
    """

    # np.arange is not precise...
    f_lon = 1.0 / res_lon
    f_lat = 1.0 / res_lat
    res_lon = res_lon * f_lon
    res_lat = res_lat * f_lat
    lon = np.arange(0.0, 360.0 * f_lon, res_lon)
    lat = np.arange(90.0 * f_lat, -90 * f_lat - res_lat, -1 * res_lat)
    lons_gt_180 = np.where(lon > (180.0 * f_lon))
    lon[lons_gt_180] = lon[lons_gt_180] - (360.0 * f_lon)

    lon, lat = np.meshgrid(lon, lat)

    glob_basic_grid = BasicGrid(lon.flatten() / f_lon, lat.flatten() / f_lat)
    glob_cell_grid = glob_basic_grid.to_cell_grid(cellsize=5.0)

    if bbox is not None:
        gpis = glob_cell_grid.get_bbox_grid_points(
            lonmin=bbox[0], latmin=bbox[1], lonmax=bbox[2], latmax=bbox[3])
        glob_cell_grid = glob_cell_grid.subgrid_from_gpis(gpis)

    return glob_cell_grid


def ERA_IrregularImgGrid(
    lons: np.ndarray,
    lats: np.ndarray,
    bbox: Tuple[float, float, float, float] = None,
) -> CellGrid:
    """
    Create a irregular grid from the passed coordinates.
    """
    lons_gt_180 = np.where(lons > 180.0)
    lons[lons_gt_180] = lons[lons_gt_180] - 360
    grid = BasicGrid(lons.flatten(), lats.flatten())\
        .to_cell_grid(cellsize=5.0)

    if bbox is not None:
        gpis = grid.get_bbox_grid_points(
            lonmin=bbox[0], latmin=bbox[1], lonmax=bbox[2], latmax=bbox[3])
        grid = grid.subgrid_from_gpis(gpis)

    return grid
