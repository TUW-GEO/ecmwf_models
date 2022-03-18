# -*- coding: utf-8 -*-

import os
import numpy.testing as nptest
from ecmwf_models.erainterim.interface import (ERAIntGrbImg, ERAIntNcImg,
                                               ERAIntGrbDs, ERAIntNcDs)
import numpy as np
from datetime import datetime


def test_ERAInt_nc_image():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA-Interim", "netcdf", "2000", "001",
        'ERAINT_AN_20000101_0000.nc')

    dset = ERAIntNcImg(
        fname, parameter=['swvl1', 'swvl2'], mask_seapoints=True)
    data = dset.read()
    assert data.data['swvl1'].shape == (241, 480)
    assert data.data['swvl2'].shape == (241, 480)
    assert data.lon.shape == (241, 480)
    assert data.lat.shape == (241, 480)
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
    nptest.assert_allclose(data.lon[100, 64], 48.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[100, 64], 15.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][100, 64], 0.17185359, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl2'][100, 64], 0.17981644, rtol=1e-5)
    # data over water
    nptest.assert_allclose(data.lon[136, 108], 81.0, rtol=1e-5)
    nptest.assert_allclose(data.lat[136, 108], -12.0, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][136, 108], np.nan)
    nptest.assert_allclose(data.data['swvl2'][136, 108], np.nan)

    #boundaries
    nptest.assert_allclose(data.lat[0, 0], 90.0)
    nptest.assert_allclose(data.lat[-1, 0], -90.0)
    nptest.assert_allclose(data.lon[0, 0], 0.0)
    nptest.assert_allclose(data.lon[0, 240], 180.0)  # middle of image


def test_ERAInt_nc_image_1d():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA-Interim", "netcdf", "2000", "001",
        'ERAINT_AN_20000101_0000.nc')

    dset = ERAIntNcImg(
        fname,
        parameter=['swvl1', 'swvl2'],
        mask_seapoints=True,
        array_1D=True)
    data = dset.read()
    assert data.data['swvl1'].shape == (241 * 480,)
    assert data.data['swvl2'].shape == (241 * 480,)
    assert data.lon.shape == (241 * 480,)
    assert data.lat.shape == (241 * 480,)
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
    nptest.assert_allclose(data.lon[100 * 480 + 64], 48.0)
    nptest.assert_allclose(data.lat[100 * 480 + 64], 15.0)
    nptest.assert_allclose(
        data.data['swvl1'][100 * 480 + 64], 0.17185359, rtol=1e-5)
    nptest.assert_allclose(
        data.data['swvl2'][100 * 480 + 64], 0.17981644, rtol=1e-5)
    # data over water
    nptest.assert_allclose(data.lon[136 * 480 + 108], 81.0)
    nptest.assert_allclose(data.lat[136 * 480 + 108], -12.0)
    nptest.assert_allclose(data.data['swvl1'][136 * 480 + 108], np.nan)
    nptest.assert_allclose(data.data['swvl2'][136 * 480 + 108], np.nan)

    #boundaries
    nptest.assert_allclose(data.lat[0], 90.0)
    nptest.assert_allclose(data.lat[-1], -90.0)
    nptest.assert_allclose(data.lon[0], 0.0)
    nptest.assert_allclose(data.lon[len(data.lon) // 2],
                           180.0)  # middle of image


def test_ERAInt_grb_image():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA-Interim", "grib", "2000", "001",
        'ERAINT_AN_20000101_0000.grb')

    dset = ERAIntGrbImg(
        fname,
        parameter=['swvl1', 'swvl2'],
        mask_seapoints=True,
        array_1D=False)
    data = dset.read()
    assert data.data['swvl1'].shape == (256, 512)
    assert data.data['swvl2'].shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
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
    nptest.assert_allclose(data.data['swvl1'][106, 68], 0.171760559)
    nptest.assert_allclose(data.data['swvl2'][106, 68], 0.178138732)
    nptest.assert_allclose(data.lon[106, 68], 47.81238356, rtol=1e-5)
    nptest.assert_allclose(data.lat[106, 68], 15.08768995, rtol=1e-5)
    # data over water
    nptest.assert_allclose(data.lon[145, 115], 80.85917808219178, rtol=1e-5)
    nptest.assert_allclose(data.lat[145, 115], -12.280678058301, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][145, 115], np.nan)
    nptest.assert_allclose(data.data['swvl2'][145, 115], np.nan)

    # boundaries
    nptest.assert_allclose(data.lat[0, 0], 89.46282157)
    nptest.assert_allclose(data.lat[-1, 0], -89.4628215685774)
    nptest.assert_allclose(data.lon[0, 0], 0.0)
    nptest.assert_allclose(data.lon[0, 256],
                           179.99956164383)  # middle of image


def test_ERAInt_grb_image_1d():
    fname = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA-Interim", "grib", "2000", "001",
        'ERAINT_AN_20000101_0000.grb')

    dset = ERAIntGrbImg(
        fname,
        parameter=['swvl1', 'swvl2'],
        mask_seapoints=True,
        array_1D=True)
    data = dset.read()
    assert data.data['swvl1'].shape == (256 * 512,)
    assert data.data['swvl2'].shape == (256 * 512,)
    assert data.lon.shape == (256 * 512,)
    assert data.lat.shape == (256 * 512,)
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
    nptest.assert_allclose(data.lon[106 * 512 + 68], 47.81238356, rtol=1e-5)
    nptest.assert_allclose(data.lat[106 * 512 + 68], 15.08768995, rtol=1e-5)
    nptest.assert_allclose(
        data.data['swvl1'][106 * 512 + 68], 0.171760559, rtol=1e-5)
    nptest.assert_allclose(
        data.data['swvl2'][106 * 512 + 68], 0.178138732, rtol=1e-5)
    # data over water
    nptest.assert_allclose(data.lon[145 * 512 + 115], 80.8591780, rtol=1e-5)
    nptest.assert_allclose(data.lat[145 * 512 + 115], -12.280678058, rtol=1e-5)
    nptest.assert_allclose(data.data['swvl1'][145 * 512 + 115], np.nan)
    nptest.assert_allclose(data.data['swvl2'][145 * 512 + 115], np.nan)

    #boundaries
    nptest.assert_allclose(data.lat[0], 89.46282157)
    nptest.assert_allclose(data.lat[-1], -89.4628215685774)
    nptest.assert_allclose(data.lon[0], 0.0)
    nptest.assert_allclose(data.lon[256], 179.99956164383)  # middle of image


def test_ERAInt_nc_ds():
    root_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA-Interim", "netcdf")

    tstamps_should = [datetime(2000, 1, 1), datetime(2000, 1, 1, 12)]

    ds = ERAIntNcDs(
        root_path,
        parameter=['swvl1', 'swvl2'],
        array_1D=True,
        mask_seapoints=True,
        h_steps=[0, 12])

    for data, tstamp_should in zip(
            ds.iter_images(datetime(2000, 1, 1), datetime(2000, 1, 1)),
            tstamps_should):
        assert data.data['swvl1'].shape == (241 * 480,)
        assert data.data['swvl2'].shape == (241 * 480,)
        assert data.lon.shape == (241 * 480,)
        assert data.lat.shape == (241 * 480,)
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
        nptest.assert_allclose(data.lon[240], 180.0)  # middle of image


def test_ERAInt_grb_ds():
    root_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..',
        "ecmwf_models-test-data", "ERA-Interim", "grib")

    tstamps_should = [datetime(2000, 1, 1), datetime(2000, 1, 1, 12)]

    ds = ERAIntGrbDs(
        root_path,
        parameter=['swvl1', 'swvl2'],
        array_1D=True,
        mask_seapoints=True,
        h_steps=[0, 12])

    for data, tstamp_should in zip(
            ds.iter_images(datetime(2000, 1, 1), datetime(2000, 1, 1)),
            tstamps_should):
        assert data.data['swvl1'].shape == (256 * 512,)
        assert data.data['swvl2'].shape == (256 * 512,)
        assert data.lon.shape == (256 * 512,)
        assert data.lat.shape == (256 * 512,)
        assert data.timestamp == tstamp_should
        metadata_should = \
            {
                'swvl1': {'long_name': u'Volumetric soil water layer 1',
                          'units': u'm**3 m**-3'},
                'swvl2': {'long_name': u'Volumetric soil water layer 2',
                          'units': u'm**3 m**-3'}
            }
        for var in ['swvl1', 'swvl2']:
            assert data.metadata[var]['long_name'] == metadata_should[var][
                'long_name']
            assert data.metadata[var]['units'] == metadata_should[var][
                'units']

        nptest.assert_allclose(data.lat[0], 89.46282157)
        nptest.assert_allclose(data.lat[-1], -89.4628215685774)
        nptest.assert_allclose(data.lon[0], 0.0)
        nptest.assert_allclose(data.lon[256],
                               179.99956164383)  # middle of image
