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
import numpy.testing as nptest
from ecmwf_models import ERAInterimImg


def test_ERAInterim_image():
    fname = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_data", "era_interim",
                         "39.128_EI_OPER_0001_AN_N128_20000101_0000_0.grb")

    dset = ERAInterimImg(fname)
    data = dset.read()
    assert data.data.shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)
    nptest.assert_allclose(data.data[34, 23], 0.30950284004211426)
    nptest.assert_allclose(data.lon[0, 0], 89.46282157)
