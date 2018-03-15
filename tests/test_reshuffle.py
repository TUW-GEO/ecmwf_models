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
Test module for image to time series conversion.
'''

import os
import glob
import tempfile
import numpy as np
import numpy.testing as nptest

from ecmwf_models.reshuffle import main
from ecmwf_models.interface import ERATs
import shutil

def test_ERAInterim_reshuffle_grb():

    inpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "test_data", "ERA-Interim", "grib")
    ts_path = tempfile.mkdtemp()
    startdate = '2000-01-01T00:00'
    enddate = '2000-01-01T18:00'
    parameters = ["swvl1", "swvl2"]

    args = [inpath, ts_path, startdate, enddate] + parameters
    main(args)
    assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 2589
    ds = ERATs(ts_path)
    ts = ds.read_ts(45, 15)
    ts_39_values_should = np.array([0.17183685,  0.17189026,  0.17173004,
                                    0.17175293], dtype=np.float32)
    nptest.assert_allclose(ts['swvl1'].values, ts_39_values_should)
    ts_40_values_should = np.array([0.17861938,  0.17861176,  0.17866516,
                                    0.17865753], dtype=np.float32)
    nptest.assert_allclose(ts['swvl2'].values, ts_40_values_should)

    shutil.rmtree(ts_path)


def test_ERA5_reshuffle_nc():

    inpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "test_data", "ERA5", "netcdf")
    ts_path = tempfile.mkdtemp()
    startdate = '2010-01-01T00:00'
    enddate = '2010-01-01T18:00'
    parameters = ["swvl1", "swvl2"]

    args = [inpath, ts_path, startdate, enddate] + parameters
    main(args)
    assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 2593
    ds = ERATs(ts_path)
    ts = ds.read_ts(15, 45)
    ts_39_values_should = np.array([0.433002,  0.428259,  0.423589,
                                    0.437551], dtype=np.float32)
    nptest.assert_allclose(ts['swvl1'].values, ts_39_values_should, rtol=1e-5)
    ts_40_values_should = np.array([0.435801,  0.434743,  0.428730,
                                    0.434220], dtype=np.float32)
    nptest.assert_allclose(ts['swvl2'].values, ts_40_values_should, rtol=1e-5)

    shutil.rmtree(ts_path)

