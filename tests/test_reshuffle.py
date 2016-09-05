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
from ecmwf_models.interface import ERAinterimTs


def test_reshuffle():

    inpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "test_data")
    ts_path = tempfile.mkdtemp()
    startdate = "2000-01-01"
    enddate = "2000-01-02"
    parameters = ["39", "40"]

    args = [inpath, ts_path, startdate, enddate] + parameters
    main(args)
    assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 2589
    ds = ERAinterimTs(ts_path)
    ts = ds.read_ts(45, 15)
    ts_39_values_should = np.array([0.17183685,  0.17189026,  0.17173004,
                                    0.17175293,  0.17183685, 0.17189026,
                                    0.17171478,  0.1717453], dtype=np.float32)
    nptest.assert_allclose(ts['39'].values, ts_39_values_should)
    ts_40_values_should = np.array([0.17861938,  0.17861176,  0.17866516,
                                    0.17865753,  0.1786499, 0.17864227,
                                    0.17868042,  0.17867279], dtype=np.float32)
    nptest.assert_allclose(ts['40'].values, ts_40_values_should)
