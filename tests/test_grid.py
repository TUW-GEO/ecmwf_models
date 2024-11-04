# -*- coding: utf-8 -*-
"""
Tests for grid generation
"""

from ecmwf_models.grid import (
    ERA_RegularImgGrid,
    get_grid_resolution,
    ERA5_RegularImgLandGrid,
)
import numpy as np


def test_global_subset():
    grid1 = ERA_RegularImgGrid(0.25)
    grid2 = ERA_RegularImgGrid(0.25, (-180, -90, 180, 90))
    np.testing.assert_array_equal(grid1.activegpis, grid2.activegpis)
    assert grid1 == grid2

    grid1 = ERA5_RegularImgLandGrid(0.25)
    grid2 = ERA5_RegularImgLandGrid(0.25, (-180, -90, 180, 90))
    np.testing.assert_array_equal(grid1.activegpis, grid2.activegpis)
    assert grid1 == grid2

    grid1 = ERA5_RegularImgLandGrid(0.25)
    grid2 = ERA5_RegularImgLandGrid(0.25, (-10, 60, 30, 90))
    assert grid1 != grid2


def test_ERA_regular_grid():
    reg_grid = ERA_RegularImgGrid(0.3)
    assert np.unique(reg_grid.activearrlat).size == 601
    assert np.unique(reg_grid.activearrlon).size == 1200
    assert get_grid_resolution(reg_grid.activearrlat,
                               reg_grid.activearrlon) == (
                                   0.3,
                                   0.3,
                               )

def test_ERA5_landgrid_025():
    grid = ERA5_RegularImgLandGrid(0.25)  # 0.25*0.25
    assert grid.get_grid_points()[0].size == 244450
    assert grid.find_nearest_gpi(16.25, 48.25) == (240545, 0.0)
    assert grid.gpi2cell(240545) == 1431


def test_ERA5_landgrid_01():
    grid = ERA5_RegularImgLandGrid(0.1)  # 0.1*0.1
    assert grid.get_grid_points()[0].size == 1544191
    assert grid.find_nearest_gpi(16.4, 48.1) == (1508564, 0.0)
    np.testing.assert_almost_equal(grid.gpi2lonlat(1508564)[0], 16.4)
    np.testing.assert_almost_equal(grid.gpi2lonlat(1508564)[1], 48.1)
    assert grid.gpi2cell(1508564) == 1431
