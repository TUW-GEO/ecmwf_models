# -*- coding: utf-8 -*-
"""
Tests for grid generation
"""

from ecmwf_models.grid import (
    ERA_RegularImgGrid,
    get_grid_resolution,
    ERA_IrregularImgGrid,
    ERA5_RegularImgLandGrid,
)
import numpy as np


def test_ERA_regular_grid():
    reg_grid = ERA_RegularImgGrid(0.3, 0.3)
    assert np.unique(reg_grid.activearrlat).size == 601
    assert np.unique(reg_grid.activearrlon).size == 1200
    assert get_grid_resolution(reg_grid.activearrlat,
                               reg_grid.activearrlon) == (
                                   0.3,
                                   0.3,
                               )


def test_ERA_irregular_grid():
    # we test this with a regular grid, because it's easier
    lon = np.arange(0, 360 - 1.0 / 2, 1.0)
    lat = np.arange(90, -1 * 90 - 1.0 / 2, -1 * 1.0)
    lons, lats = np.meshgrid(lon, lat)

    grid = ERA_IrregularImgGrid(lons, lats)

    assert grid == ERA_RegularImgGrid(1.0, 1.0)


def test_ERA5_landgrid_025():
    grid = ERA5_RegularImgLandGrid(0.25, 0.25)  # 0.25*0.25
    assert grid.get_grid_points()[0].size == 244450
    assert grid.find_nearest_gpi(16.25, 48.25) == (240545, 0.0)
    assert grid.gpi2cell(240545) == 1431


def test_ERA5_landgrid_01():
    grid = ERA5_RegularImgLandGrid(0.1, 0.1)  # 0.1*0.1
    assert grid.get_grid_points()[0].size == 1544191
    assert grid.find_nearest_gpi(16.4, 48.1) == (1508564, 0.0)
    np.testing.assert_almost_equal(grid.gpi2lonlat(1508564)[0], 16.4)
    np.testing.assert_almost_equal(grid.gpi2lonlat(1508564)[1], 48.1)
    assert grid.gpi2cell(1508564) == 1431
