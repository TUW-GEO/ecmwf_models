# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2018, TU Wien
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
Tests for transferring downloaded data to netcdf or grib files
'''


from ecmwf_models.download import save_ncs_from_nc, save_gribs_from_grib
import os
import tempfile
import shutil
import glob

def test_ERA_ncs_from_nc():
    ncs_path = tempfile.mkdtemp()
    input_nc = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "test_data", "ERA5", "example_downloaded_raw.nc")
    save_ncs_from_nc(input_nc, ncs_path, 'ERA5')

    assert len(glob.glob(os.path.join(ncs_path, "2010", "001", "*.nc"))) == 4
    files = sorted(os.listdir(os.path.join(ncs_path, "2010", "001")))
    for f,t in zip(files, ['00', '06', '12', '18']):
        assert f == 'ERA5_5.0_5.0_20100101_%s00.nc' % t
    shutil.rmtree(ncs_path)

def test_ERA_gribs_from_grib():
    grbs_path = tempfile.mkdtemp()
    input_grb = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "test_data", "ERA-Interim", "example_downloaded_raw.grb")
    save_gribs_from_grib(input_grb, grbs_path, 'ERA-Interim')

    assert len(glob.glob(os.path.join(grbs_path, "2000", "001", "*.grb"))) == 4
    files = sorted(os.listdir(os.path.join(grbs_path, "2000", "001")))
    for f,t in zip(files, ['00', '06', '12', '18']):
        assert f == 'ERA-Interim_OPER_0001_AN_20000101_%s00.grb' % t
    shutil.rmtree(grbs_path)
