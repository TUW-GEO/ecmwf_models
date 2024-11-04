# -*- coding: utf-8 -*-
"""
Common grid definitions for ECMWF model reanalysis products (regular gridded)
"""

import numpy as np
from pygeogrids.grids import CellGrid, gridfromdims
import os
from typing import Tuple
import xarray as xr


def trafo_lon(lon):
    """
    0...360 -> 0...180...-180

    Parameters
    ----------
    lon: np.array
        Longitude array

    Returns
    -------
    lon_transformed: np.array
        Transformed longitude array
    """
    lons_gt_180 = np.where(lon > 180.)
    lon[lons_gt_180] = lon[lons_gt_180] - 360.0
    return lon


def safe_arange(start, stop, step):
    """
    Like numpy.arange, but floating point precision is kept.
    Compare: `np.arange(0, 100, 0.01)[-1]` vs `safe_arange(0, 100, 0.01)[-1]`

    Parameters
    ----------
    start: float
        Start of interval
    stop: float
        End of interval (not included)
    step: float
        Stepsize

    Returns
    -------
    arange: np.array
        Range of values in interval at the given step size / sampling
    """
    f_step = (1. / float(step))
    vals = np.arange(
        float(start) * f_step,
        float(stop) * f_step,
        float(step) * f_step)
    return vals / f_step


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
    resolution: float = 0.25,
    bbox: Tuple[float, float, float, float] = None,
) -> CellGrid:
    """
    Uses the 0.25 DEG ERA5 land mask to create a land grid of the same size,
    which also excluded Antarctica.

    Parameters
    ----------
    resolution: float, optional (default: 0.25)
        Grid resolution in degrees. Either 0.25 (ERA5) or 0.1 (ERA5-Land)
    bbox: tuple, optional (default: None)
        WGS84 (min_lon, min_lat, max_lon, max_lat)
        Values must be between -180 to 180 and -90 to 90
        bbox to cut the global grid to

    Returns
    -------
    landgrid: CellGrid
        ERA Land grid at the given resolution, cut to the given bounding box
    """
    if resolution not in [0.25, 0.1]:
        raise ValueError("Unsupported resolution. Choose one of 0.25 or 0.1")
    try:
        ds = xr.open_dataset(
            os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "era5",
                "land_definition_files",
                f"landmask_{resolution}_{resolution}.nc",
            ))["land"]
        ds = ds.assign_coords({'longitude': trafo_lon(ds['longitude'].values)})
        if bbox is not None:
            ds = ds.sel(latitude=slice(bbox[3], bbox[1]))
            ds = ds.isel(
                longitude=np.where(((ds['longitude'].values >= bbox[0])
                                    & (ds['longitude'].values <= bbox[2])))[0])

        land_mask = np.array(ds.values == 1.0)

    except FileNotFoundError:
        raise FileNotFoundError(
            "Land definition for this grid resolution not yet available. "
            "Please create and add it.")

    full_grid = ERA_RegularImgGrid(resolution, bbox=bbox)

    land_gpis = full_grid.get_grid_points()[0][land_mask.flatten()]
    land_grid = full_grid.subgrid_from_gpis(land_gpis)

    return land_grid


def ERA_RegularImgGrid(
    resolution: float = 0.25,
    bbox: Tuple[float, float, float, float] = None,
) -> CellGrid:
    """
    Create regular cell grid for bounding box with the selected
    resolution.

    Parameters
    ----------
    resolution: float, optional (default: 0.25)
        Grid resolution (in degrees) in both directions.
        Either 0.25 (ERA5) or 0.1 (ERA5-Land)
    bbox: tuple, optional (default: None)
        (min_lon, min_lat, max_lon, max_lat)
        wgs84 (Lon -180 to 180)
        bbox to cut the global grid to.

    Returns
    ----------
    CellGrid : CellGrid
        Regular, CellGrid with 5DEG*5DEG cells for the passed bounding box.
    """
    # to get precise coordinates...
    lon = safe_arange(-180, 180, resolution)
    lat = safe_arange(-90, 90 + resolution, resolution)[::-1]

    # ERA grid LLC point has Lon=0
    lon = np.roll(lon, int(len(lon) * 0.5))
    grid = gridfromdims(lon, lat, origin='top')

    grid = grid.to_cell_grid(cellsize=5.0)

    if bbox is not None:
        # could be simpler if pygeogrids kept the gpi order...
        subgpis = grid.get_bbox_grid_points(
            latmin=bbox[1], latmax=bbox[3], lonmin=bbox[0], lonmax=bbox[2])
        sel = np.where(np.isin(grid.activegpis, subgpis))
        subgpis = grid.activegpis[sel]
        sublats, sublons = grid.activearrlat[sel], grid.activearrlon[sel]
        shape = (np.unique(sublats).size, np.unique(sublons).size)
        grid = CellGrid(sublons, sublats, grid.gpi2cell(subgpis), subgpis,
                        shape=shape)

    return grid
