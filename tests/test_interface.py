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
from ecmwf_models import ERAInterimImg
from ecmwf_models import ERAInterimDs


def test_ERAInterim_image():
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_data", "ei_2000",
                         "39.128_EI_OPER_0001_AN_N128_20000101_0000_0.grb")

    dset = ERAInterimImg(fname)
    data = dset.read()
    assert data.data.shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata == metadata_should
    nptest.assert_allclose(data.data[34, 23], 0.30950284004211426)
    nptest.assert_allclose(data.lat[0, 0], 89.46282157)
    nptest.assert_allclose(data.lon[0, 0], 0)
    nptest.assert_allclose(data.lon[0, 256], 179.99956164383)


def test_ERAInterim_image_no_expand():
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_data", "ei_2000",
                         "39.128_EI_OPER_0001_AN_N128_20000101_0000_0.grb")

    dset = ERAInterimImg(fname, expand_grid=False)
    data = dset.read()
    assert data.data.shape == (88838,)
    assert data.lon.shape == (88838,)
    assert data.lat.shape == (88838,)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata == metadata_should
    nptest.assert_allclose(data.lat[0], 89.46282157)
    nptest.assert_allclose(data.lon[0], 0)


def test_ERAInterim_dataset_one_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data")
    ds = ERAInterimDs('39', root_path)
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['39'].shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata['39'] == metadata_should
    nptest.assert_allclose(data.data['39'][34, 23], 0.30950284004211426)
    nptest.assert_allclose(data.lat[0, 0], 89.46282157)


def test_ERAInterim_dataset_one_var_no_expand():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data")
    ds = ERAInterimDs('39', root_path, expand_grid=False)
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['39'].shape == (88838,)
    assert data.lon.shape == (88838,)
    assert data.lat.shape == (88838,)
    metadata_should = {'long_name': u'Volumetric soil water layer 1',
                       'units': u'm**3 m**-3', 'depth': u'0-7 cm'}
    assert data.metadata['39'] == metadata_should
    nptest.assert_allclose(data.lat[0], 89.46282157)


def test_ERAInterim_dataset_two_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data")
    ds = ERAInterimDs(['39', '40'], root_path)
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['39'].shape == (256, 512)
    assert data.data['40'].shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
    assert data.timestamp == datetime(2000, 1, 1, 0, 0)
    metadata_should = {'39': {'long_name': u'Volumetric soil water layer 1',
                              'units': u'm**3 m**-3',
                              'depth': u'0-7 cm'},
                       '40': {'long_name': u'Volumetric soil water layer 2',
                              'units': u'm**3 m**-3',
                              'depth': u'7-28 cm'}, }
    assert data.metadata == metadata_should
    nptest.assert_allclose(data.data['39'][34, 23], 0.30950284004211426)
    nptest.assert_allclose(data.data['40'][34, 23], 0.3094451427459717)
    nptest.assert_allclose(data.lat[0, 0], 89.46282157)


def test_ERAInterim_iter_dataset_two_var():
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "test_data")
    tstamps_should = [datetime(2000, 1, 1),
                      datetime(2000, 1, 1, 6),
                      datetime(2000, 1, 1, 12),
                      datetime(2000, 1, 1, 18)]
    with ERAInterimDs(['39', '40'], root_path) as ds:
        for data, tstamp_should in zip(ds.iter_images(datetime(2000, 1, 1), datetime(2000, 1, 1)),
                                       tstamps_should):
            assert data.data['39'].shape == (256, 512)
            assert data.data['40'].shape == (256, 512)
            assert data.lon.shape == (256, 512)
            assert data.lat.shape == (256, 512)
            assert data.timestamp == tstamp_should
            metadata_should = {'39': {'long_name': u'Volumetric soil water layer 1',
                                      'units': u'm**3 m**-3',
                                      'depth': u'0-7 cm'},
                               '40': {'long_name': u'Volumetric soil water layer 2',
                                      'units': u'm**3 m**-3',
                                      'depth': u'7-28 cm'}, }
            assert data.metadata == metadata_should
            nptest.assert_allclose(data.lat[0, 0], 89.46282157)
