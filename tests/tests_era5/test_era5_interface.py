# -*- coding: utf-8 -*-

import os
import numpy.testing as nptest
from ecmwf_models.era5.img import (
    ERA5NcDs, ERA5NcImg, ERA5GrbImg, ERA5GrbDs)
import numpy as np
from datetime import datetime
from ecmwf_models.grid import ERA5_RegularImgLandGrid


def test_ERA5_nc_image_landpoints():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA5", "netcdf", "2010", "001",
        'ERA5_AN_20100101_0000.nc')
    subgrid = ERA5_RegularImgLandGrid(0.25)
    dset = ERA5NcImg(
        fname,
        parameter=['swvl1', 'swvl2'],
        mask_seapoints=True,
        array_1D=True,
        subgrid=subgrid)
    data = dset.read()
    assert data.data['swvl1'].shape == (244450,)
    assert data.data['swvl2'].shape == (244450,)
    assert data.lon.shape == (244450,)
    assert data.lat.shape == (244450,)
    metadata_should = {
        'long_name': u'Volumetric soil water layer 1',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl1']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl1']['units'] == metadata_should['units']

    metadata_should = {
        'long_name': u'Volumetric soil water layer 2',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl2']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl2']['units'] == metadata_should['units']

    # data over land
    nptest.assert_allclose(data.lon[1000], -29.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[1000], 82.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][1000], 0.41698003, rtol=1e-5)
    #boundaries
    nptest.assert_allclose(data.lat[0], 83.5)
    nptest.assert_allclose(data.lat[-1], -55.25)
    nptest.assert_allclose(data.lon[0], -36)


def test_ERA5_nc_image():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA5", "netcdf", "2010", "001",
        'ERA5_AN_20100101_0000.nc')

    dset = ERA5NcImg(fname, parameter=['swvl1', 'swvl2'], mask_seapoints=True)
    data = dset.read()
    assert data.data['swvl1'].shape == (721, 1440)
    assert data.data['swvl2'].shape == (721, 1440)
    assert data.lon.shape == (721, 1440)
    assert data.lat.shape == (721, 1440)
    metadata_should = {
        'long_name': u'Volumetric soil water layer 1',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl1']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl1']['units'] == metadata_should['units']

    metadata_should = {
        'long_name': u'Volumetric soil water layer 2',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl2']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl2']['units'] == metadata_should['units']

    # data over land
    nptest.assert_allclose(data.lon[168, 60], 15.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[168, 60], 48.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][168, 60], 0.402825, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl2'][168, 60], 0.390512, rtol=1e-5)
    # data over water
    nptest.assert_allclose(data.lon[400, 320], 80.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[400, 320], -10.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][400, 320], np.nan)
    nptest.assert_allclose(data.data['swvl2'][400, 320], np.nan)

    #boundaries
    nptest.assert_allclose(data.lat[0, 0], 90.0)
    nptest.assert_allclose(data.lat[-1, 0], -90.0)
    nptest.assert_allclose(data.lon[0, 0], 0.0)
    nptest.assert_allclose(data.lon[0, 720], 180.0)  # middle of image


def test_ERA5_nc_image_1d():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA5", "netcdf", "2010", "001",
        'ERA5_AN_20100101_0000.nc')

    dset = ERA5NcImg(
        fname,
        parameter=['swvl1', 'swvl2'],
        mask_seapoints=True,
        array_1D=True)
    data = dset.read()
    assert data.data['swvl1'].shape == (721 * 1440,)
    assert data.data['swvl2'].shape == (721 * 1440,)
    assert data.lon.shape == (721 * 1440,)
    assert data.lat.shape == (721 * 1440,)
    metadata_should = {
        'long_name': u'Volumetric soil water layer 1',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl1']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl1']['units'] == metadata_should['units']

    metadata_should = {
        'long_name': u'Volumetric soil water layer 2',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl2']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl2']['units'] == metadata_should['units']

    # data over land
    nptest.assert_allclose(data.lon[168 * 1440 + 60], 15.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[168 * 1440 + 60], 48.0, rtol=1e-5)
    nptest.assert_allclose(
        data.data['swvl1'][168 * 1440 + 60], 0.402825, rtol=1e-5)
    nptest.assert_allclose(
        data.data['swvl2'][168 * 1440 + 60], 0.390512, rtol=1e-5)
    # data over water
    nptest.assert_allclose(data.lon[400 * 1440 + 320], 80.0, rtol=1e-4)
    nptest.assert_allclose(data.lat[400 * 1440 + 320], -10.0, rtol=1e-4)
    nptest.assert_allclose(data.data['swvl1'][400 * 1440 + 320], np.nan)
    nptest.assert_allclose(data.data['swvl2'][400 * 1440 + 320], np.nan)

    #boundaries
    nptest.assert_allclose(data.lat[0], 90.0)
    nptest.assert_allclose(data.lat[-1], -90.0)
    nptest.assert_allclose(data.lon[0], 0.0)
    nptest.assert_allclose(data.lon[len(data.lon) // 2],
                           180.0)  # middle of image


def test_ERA5_grb_image():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA5", "grib", "2010", "001",
        'ERA5_AN_20100101_0000.grb')

    dset = ERA5GrbImg(
        fname,
        parameter=['swvl1', 'swvl2'],
        mask_seapoints=True,
        array_1D=False)
    data = dset.read()
    assert data.data['swvl1'].shape == (721, 1440)
    assert data.data['swvl2'].shape == (721, 1440)
    assert data.lon.shape == (721, 1440)
    assert data.lat.shape == (721, 1440)
    metadata_should = {
        'long_name': u'Volumetric soil water layer 1',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl1']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl1']['units'] == metadata_should['units']

    metadata_should = {
        'long_name': u'Volumetric soil water layer 2',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl2']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl2']['units'] == metadata_should['units']

    # data over land
    nptest.assert_allclose(data.lon[168, 60], 15.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[168, 60], 48.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][168, 60], 0.402824, rtol=1e-4)
    nptest.assert_allclose(data.data['swvl2'][168, 60], 0.390514, rtol=1e-4)
    # data over water
    nptest.assert_allclose(data.lon[400, 320], 80.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[400, 320], -10.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][400, 320], np.nan)
    nptest.assert_allclose(data.data['swvl2'][400, 320], np.nan)

    # boundaries
    nptest.assert_allclose(data.lat[0, 0], 90.0)
    nptest.assert_allclose(data.lat[-1, 0], -90.0)
    nptest.assert_allclose(data.lon[0, 0], 0.0)
    nptest.assert_allclose(data.lon[0, 720], 180.0)  # middle of image


def test_ERA5_grb_image_1d():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA5", "grib", "2010", "001",
        'ERA5_AN_20100101_0000.grb')

    dset = ERA5GrbImg(
        fname,
        parameter=['swvl1', 'swvl2'],
        mask_seapoints=True,
        array_1D=True)
    data = dset.read()
    assert data.data['swvl1'].shape == (721 * 1440,)
    assert data.data['swvl2'].shape == (721 * 1440,)
    assert data.lon.shape == (721 * 1440,)
    assert data.lat.shape == (721 * 1440,)
    metadata_should = {
        'long_name': u'Volumetric soil water layer 1',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl1']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl1']['units'] == metadata_should['units']

    metadata_should = {
        'long_name': u'Volumetric soil water layer 2',
        'units': u'm**3 m**-3'
    }
    assert data.metadata['swvl2']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl2']['units'] == metadata_should['units']

    # data over land
    nptest.assert_allclose(data.lon[168 * 1440 + 60], 15.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[168 * 1440 + 60], 48.0, rtol=1e-5)
    nptest.assert_allclose(
        data.data['swvl1'][168 * 1440 + 60], 0.402824, rtol=1e-4)
    nptest.assert_allclose(
        data.data['swvl2'][168 * 1440 + 60], 0.390514, rtol=1e-4)
    # data over water
    nptest.assert_allclose(data.lon[400 * 1440 + 320], 80.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[400 * 1440 + 320], -10.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][400 * 1440 + 320], np.nan)
    nptest.assert_allclose(data.data['swvl2'][400 * 1440 + 320], np.nan)

    # boundaries
    nptest.assert_allclose(data.lat[0], 90.0)
    nptest.assert_allclose(data.lat[-1], -90.0)
    nptest.assert_allclose(data.lon[0], 0.0)
    nptest.assert_allclose(data.lon[len(data.lon) // 2],
                           180.0)  # middle of image


def test_ERA5_nc_ds():
    root_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA5", "netcdf")

    tstamps_should = [datetime(2010, 1, 1), datetime(2010, 1, 1, 12)]

    ds = ERA5NcDs(
        root_path,
        parameter=['swvl1', 'swvl2'],
        array_1D=True,
        mask_seapoints=True,
        h_steps=[0, 12])

    for data, tstamp_should in zip(
            ds.iter_images(datetime(2010, 1, 1), datetime(2010, 1, 1)),
            tstamps_should):
        assert data.data['swvl1'].shape == (721 * 1440,)
        assert data.data['swvl2'].shape == (721 * 1440,)
        assert data.lon.shape == (721 * 1440,)
        assert data.lat.shape == (721 * 1440,)
        assert data.timestamp == tstamp_should
        metadata_should = {
            'swvl1': {
                'long_name': u'Volumetric soil water layer 1',
                'units': u'm**3 m**-3'
            },
            'swvl2': {
                'long_name': u'Volumetric soil water layer 2',
                'units': u'm**3 m**-3'
            }
        }
        for var in ['swvl1', 'swvl2']:
            assert data.metadata[var]['long_name'] == metadata_should[var][
                'long_name']
            assert data.metadata[var]['units'] == metadata_should[var]['units']

        nptest.assert_allclose(data.lat[0], 90.0)
        nptest.assert_allclose(data.lat[-1], -90.0)
        nptest.assert_allclose(data.lon[0], 0.0)
        nptest.assert_allclose(data.lon[720], 180.0)  # middle of image


def test_ERA5_grb_ds():
    root_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA5", "grib")

    tstamps_should = [datetime(2010, 1, 1), datetime(2010, 1, 1, 12)]

    ds = ERA5GrbDs(
        root_path,
        parameter=['swvl1', 'swvl2'],
        array_1D=True,
        mask_seapoints=True,
        h_steps=[0, 12])

    for data, tstamp_should in zip(
            ds.iter_images(datetime(2010, 1, 1), datetime(2010, 1, 1)),
            tstamps_should):
        assert data.data['swvl1'].shape == (721 * 1440,)
        assert data.data['swvl2'].shape == (721 * 1440,)
        assert data.lon.shape == (721 * 1440,)
        assert data.lat.shape == (721 * 1440,)
        assert data.timestamp == tstamp_should
        metadata_should = {
            'swvl1': {
                'long_name': u'Volumetric soil water layer 1',
                'units': u'm**3 m**-3'
            },
            'swvl2': {
                'long_name': u'Volumetric soil water layer 2',
                'units': u'm**3 m**-3'
            }
        }
        for var in ['swvl1', 'swvl2']:
            assert data.metadata[var]['long_name'] == metadata_should[var][
                'long_name']
            assert data.metadata[var]['units'] == metadata_should[var]['units']

        nptest.assert_allclose(data.lat[0], 90.0)
        nptest.assert_allclose(data.lat[-1], -90.0)
        nptest.assert_allclose(data.lon[0], 0.0)
        nptest.assert_allclose(data.lon[720], 180.0)  # middle of image

if __name__ == '__main__':
    test_ERA5_grb_image()