# -*- coding: utf-8 -*-
'''
Testing the utility functions
'''

from ecmwf_models.utils import (
    str2bool,
    mkdate,
    parse_filetype,
    parse_product,
    load_var_table,
    lookup,
    get_default_params,
    make_era5_land_definition_file)
import os
from datetime import datetime
import tempfile
import numpy as np
from netCDF4 import Dataset


def test_str2bool():
    assert str2bool('true')
    assert not str2bool('false')


def test_mkdate():
    assert mkdate('2000-01-01') == datetime(2000, 1, 1)
    assert mkdate('2000-01-01T06:00') == datetime(2000, 1, 1, 6)


def test_parse_product():
    inpath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ecmwf_models-test-data",
        "ERA5", "netcdf")
    assert parse_product(inpath) == 'era5'


def test_parse_filetype():
    inpath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ecmwf_models-test-data",
        "ERA5", "netcdf")
    assert parse_filetype(inpath) == 'netcdf'


def test_load_var_table():
    table = load_var_table('era5')
    assert table.index.size == 265
    assert table.loc[
        100].dl_name == 'mean_surface_direct_short_wave_radiation_flux'
    assert table.loc[100].short_name == 'msdrswrf'

    table = load_var_table('era5-land')
    assert table.index.size == 49
    assert table.loc[45].dl_name == 'volumetric_soil_water_layer_1'
    assert table.loc[45].short_name == 'swvl1'

    table = load_var_table('eraint')
    assert table.index.size == 79
    assert table.loc[8].dl_name == 39.128
    assert table.loc[8].long_name == 'Volumetric soil water layer 1'
    assert table.loc[8].short_name == 'swvl1'


def test_lookup():
    lut = lookup('era5', ['swvl1', 'stl1'])
    assert lut.loc[254].dl_name == 'volumetric_soil_water_layer_1'
    assert lut.loc[171].dl_name == 'soil_temperature_level_1'


def test_get_default_params():
    vars = get_default_params('era5')
    assert all(vars['default'].values == 1)


def test_create_land_definition_file():
    inpath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ecmwf_models-test-data",
        "ERA5", "netcdf")
    path_desired = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'src',
        'ecmwf_models', 'era5', 'land_definition_files',
        'landmask_0.25_0.25.nc')

    data_file = os.path.join(inpath, '2010', '001', 'ERA5_AN_20100101_0000.nc')
    out_dir = tempfile.mkdtemp()
    out_file = os.path.join(out_dir, 'land_definition_out.nc')

    make_era5_land_definition_file(data_file, out_file)

    ds_actual = Dataset(out_file)
    actual = ds_actual.variables['land'][:]

    ds_desired = Dataset(path_desired)
    desired = ds_desired.variables['land'][:]

    assert np.allclose(actual, desired, equal_nan=True)
