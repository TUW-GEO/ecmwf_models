# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2016, TU Wien
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Tests for reading the data.
'''

import os
from datetime import datetime
import numpy.testing as nptest
from ecmwf_models.interface import ERANcImg, ERANcDs, ERAGrbImg, ERAGrbDs, ERATs


def test_ERAInterim_image():
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_data", "ERA-Interim", "grib", "2000", "001",
                         "ERA-Interim_OPER_0001_AN_20000101_0000.grb")

    dset = ERAGrbImg(fname, 'swvl1')
    data = dset.read()
    assert data.data['swvl1'].shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata['swvl1'] == metadata_should
    nptest.assert_allclose(data.data['swvl1'][34, 23], 0.30950284004211426)
    nptest.assert_allclose(data.lat[0, 0], 89.46282157)
    nptest.assert_allclose(data.lon[0, 0], 0)
    nptest.assert_allclose(data.lon[0, 256], 179.99956164383)


def test_ERAInterim_image_no_expand():
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_data", "ERA-Interim", "grib", "2000", "001",
                         "ERA-Interim_OPER_0001_AN_20000101_0000.grb")

    dset = ERAGrbImg(fname, 'swvl1', expand_grid=False)
    data = dset.read()
    assert data.data['swvl1'].shape == (88838,)
    assert data.lon.shape == (88838,)
    assert data.lat.shape == (88838,)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata['swvl1'] == metadata_should
    nptest.assert_allclose(data.lat[0], 89.46282157)
    nptest.assert_allclose(data.lon[0], 0)


def test_ERAInterim_dataset_one_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data", "ERA-Interim", "grib")
    ds = ERAGrbDs(root_path, 'swvl1')
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['swvl1'].shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata['swvl1'] == metadata_should
    nptest.assert_allclose(data.data['swvl1'][34, 23], 0.30950284004211426)
    nptest.assert_allclose(data.lat[0, 0], 89.46282157)


def test_ERAInterim_dataset_one_var_no_expand():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data", "ERA-Interim", "grib")
    ds = ERAGrbDs(root_path, 'swvl1', expand_grid=False)
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['swvl1'].shape == (88838,)
    assert data.lon.shape == (88838,)
    assert data.lat.shape == (88838,)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata['swvl1'] == metadata_should
    nptest.assert_allclose(data.lat[0], 89.46282157)


def test_ERAInterim_dataset_two_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data", "ERA-Interim", "grib")
    ds = ERAGrbDs(root_path, ['swvl1', 'swvl2'] )
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['swvl1'].shape == (256, 512)
    assert data.data['swvl2'].shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
    assert data.timestamp == datetime(2000, 1, 1, 0, 0)
    metadata_should = {'swvl1': {'long_name': u'Volumetric soil water layer 1',
                              'units': u'm**3 m**-3',
                              'depth': u'0-7 cm'},
                       'swvl2': {'long_name': u'Volumetric soil water layer 2',
                              'units': u'm**3 m**-3',
                              'depth': u'7-28 cm'}, }
    assert data.metadata == metadata_should
    nptest.assert_allclose(data.data['swvl1'][34, 23], 0.30950284004211426)
    nptest.assert_allclose(data.data['swvl2'][34, 23], 0.3094451427459717)
    nptest.assert_allclose(data.lat[0, 0], 89.46282157)


def test_ERAInterim_iter_dataset_two_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data", "ERA-Interim", "grib")
    tstamps_should = [datetime(2000, 1, 1),
                      datetime(2000, 1, 1, 6),
                      datetime(2000, 1, 1, 12),
                      datetime(2000, 1, 1, 18)]
    with ERAGrbDs(root_path, ['swvl1', 'swvl2']) as ds:
        for data, tstamp_should in zip(ds.iter_images(datetime(2000, 1, 1), datetime(2000, 1, 1)),
                                       tstamps_should):
            assert data.data['swvl1'].shape == (256, 512)
            assert data.data['swvl2'].shape == (256, 512)
            assert data.lon.shape == (256, 512)
            assert data.lat.shape == (256, 512)
            assert data.timestamp == tstamp_should
            metadata_should = {'swvl1': {'long_name': u'Volumetric soil water layer 1',
                                      'units': u'm**3 m**-3',
                                      'depth': u'0-7 cm'},
                               'swvl2': {'long_name': u'Volumetric soil water layer 2',
                                      'units': u'm**3 m**-3',
                                      'depth': u'7-28 cm'}, }
            assert data.metadata == metadata_should
            nptest.assert_allclose(data.lat[0, 0], 89.46282157)

##################################################################################

def test_ERA5_image():
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_data", "ERA5", "netcdf", "2010", "001",
                         'ERA5_0.3_0.3_20100101_0000.nc')

    dset = ERANcImg(fname, 'swvl1')
    data = dset.read()
    assert data.data['swvl1'].shape == (601, 1200)
    assert data.lon.shape == (601, 1200)
    assert data.lat.shape == (601, 1200)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3'}
    assert data.metadata['swvl1']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl1']['units'] == metadata_should['units']
    nptest.assert_allclose(data.data['swvl1'][139, 45], 0.411516, rtol=1e-6)
    nptest.assert_allclose(data.lat[0, 0], 90)
    nptest.assert_allclose(data.lon[0, 0], 0)
    nptest.assert_allclose(data.lon[0, 600], -180, rtol=1e-5)


def test_ERA5_image_no_expand():
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_data", "ERA5", "netcdf", "2010", "001",
                         'ERA5_0.3_0.3_20100101_0000.nc')

    dset = ERANcImg(fname, 'swvl1', array_1D=True)
    data = dset.read()
    assert data.data['swvl1'].shape == (601*1200,)
    assert data.lon.shape == (601*1200,)
    assert data.lat.shape == (601*1200,)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3'}
    assert data.metadata['swvl1']['long_name'] == metadata_should['long_name']
    assert data.metadata['swvl1']['units'] == metadata_should['units']
    nptest.assert_allclose(data.data['swvl1'][55 * 1200 + 347], 0.3263698, rtol=1e-6)
    nptest.assert_allclose(data.lat[0], 90)
    nptest.assert_allclose(data.lat[-1], -90)
    nptest.assert_allclose(data.lon[0], 0)
    nptest.assert_allclose(data.lon[600], -180)


def test_ERA5_dataset_two_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data", "ERA5", "netcdf")
    ds = ERANcDs(root_path, ['swvl1', 'swvl2'])
    data = ds.read(datetime(2010, 1, 1, 0))
    assert data.data['swvl1'].shape == (601, 1200)
    assert data.data['swvl2'].shape == (601, 1200)
    assert data.lon.shape == (601, 1200)
    assert data.lat.shape == (601, 1200)
    assert data.timestamp == datetime(2010, 1, 1, 0, 0)
    metadata_should = {'swvl1': {'long_name': u'Volumetric soil water layer 1',
                                 'units': u'm**3 m**-3'},
                       'swvl2': {'long_name': u'Volumetric soil water layer 2',
                                 'units': u'm**3 m**-3'}}
    for var in ['swvl1', 'swvl2']:
        assert data.metadata[var]['long_name'] == metadata_should[var]['long_name']
        assert data.metadata[var]['units'] == metadata_should[var]['units']

    nptest.assert_allclose(data.data['swvl1'][139, 45], 0.411516, rtol=1e-6)
    nptest.assert_allclose(data.data['swvl2'][139, 45], 0.413387, rtol=1e-6)
    nptest.assert_allclose(data.lat[0, 0], 90)
    nptest.assert_allclose(data.lon[0, 0], 0)
    nptest.assert_allclose(data.lon[0, 600], -180, rtol=1e-5)


def test_ERA5_dataset_two_var_no_expand():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data", "ERA5", "netcdf")
    ds = ERANcDs(root_path, ['swvl1', 'swvl2'], array_1D=True)
    data = ds.read(datetime(2010, 1, 1, 0))
    assert data.data['swvl1'].shape == (601*1200,)
    assert data.data['swvl2'].shape == (601*1200,)
    assert data.lon.shape == (601*1200,)
    assert data.lat.shape == (601*1200,)
    assert data.timestamp == datetime(2010, 1, 1, 0, 0)
    metadata_should = {'swvl1': {'long_name': u'Volumetric soil water layer 1',
                                 'units': u'm**3 m**-3'},
                       'swvl2': {'long_name': u'Volumetric soil water layer 2',
                                 'units': u'm**3 m**-3'}}
    for var in ['swvl1', 'swvl2']:
        assert data.metadata[var]['long_name'] == metadata_should[var]['long_name']
        assert data.metadata[var]['units'] == metadata_should[var]['units']

    nptest.assert_allclose(data.data['swvl1'][55 * 1200 + 347], 0.3263698, rtol=1e-6)
    nptest.assert_allclose(data.data['swvl2'][55 * 1200 + 347], 0.3269657, rtol = 1e-6)
    nptest.assert_allclose(data.lat[0], 90)
    nptest.assert_allclose(data.lon[0], 0)
    nptest.assert_allclose(data.lon[int(data.lon.size/2)], -180, rtol=1e-5)



def test_ERA5_iter_dataset_two_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data", "ERA5", "netcdf")
    tstamps_should = [datetime(2010, 1, 1),
                      datetime(2010, 1, 1, 6),
                      datetime(2010, 1, 1, 12),
                      datetime(2010, 1, 1, 18)]
    with ERANcDs(root_path, ['swvl1', 'swvl2']) as ds:
        for data, tstamp_should in zip(ds.iter_images(datetime(2010, 1, 1), datetime(2010, 1, 1)),
                                       tstamps_should):
            assert data.data['swvl1'].shape == (601, 1200)
            assert data.data['swvl2'].shape == (601, 1200)
            assert data.lon.shape == (601, 1200)
            assert data.lat.shape == (601, 1200)
            assert data.timestamp == tstamp_should
            metadata_should = {'swvl1': {'long_name': u'Volumetric soil water layer 1',
                                         'units': u'm**3 m**-3'},
                               'swvl2': {'long_name': u'Volumetric soil water layer 2',
                                         'units': u'm**3 m**-3'}}
            for var in ['swvl1', 'swvl2']:
                assert data.metadata[var]['long_name'] == metadata_should[var]['long_name']
                assert data.metadata[var]['units'] == metadata_should[var]['units']
            nptest.assert_allclose(data.lat[0, 0], 90)

