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
from ecmwf_models.download_eraint import download_and_move as download_and_move_ei
from ecmwf_models.download_era5 import download_and_move as download_and_move_era5

import os
import tempfile
import shutil
from datetime import datetime

def test_dry_download_era5():

    dl_path = tempfile.mkdtemp()
    dl_path = os.path.join(dl_path, 'era5')
    os.mkdir(dl_path)
    os.mkdir(os.path.join(dl_path, 'temp_downloaded'))

    thefile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
              "ecmwf_models-test-data", "download", "era5_example_downloaded_raw.nc")
    shutil.copyfile(thefile, os.path.join(dl_path, 'temp_downloaded', '20100101_20100101.nc'))

    startdate = enddate = datetime(2010,1,1)

    download_and_move_era5(dl_path, startdate, enddate, ['volumetric_soil_water_layer_1'],
                           keep_original=False, h_steps=[0, 6, 12, 18],
                           netcdf=True, dry_run=True)

    assert(os.listdir(dl_path) == ['2010'])
    assert(os.listdir(os.path.join(dl_path, '2010')) == ['001'])
    assert(len(os.listdir(os.path.join(dl_path, '2010', '001'))) == 4)

    should_dlfiles = ['ERA5_5.0_5.0_20100101_0000.nc',
                      'ERA5_5.0_5.0_20100101_0600.nc',
                      'ERA5_5.0_5.0_20100101_1200.nc',
                      'ERA5_5.0_5.0_20100101_1800.nc']

    assert(os.listdir(os.path.join(dl_path, '2010', '001')) == should_dlfiles)

    shutil.rmtree(dl_path)


def test_dry_download_eraint():
    ''' This does not download anything but checks if the code runs through'''
    dl_path = tempfile.mkdtemp()
    dl_path = os.path.join(dl_path, 'eraint')
    os.mkdir(dl_path)
    os.mkdir(os.path.join(dl_path, 'temp_downloaded'))

    thefile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
              "ecmwf_models-test-data", "download", "eraint_example_downloaded_raw.grb")
    shutil.copyfile(thefile, os.path.join(dl_path, 'temp_downloaded', '20000101_20000101.grb'))

    startdate = enddate = datetime(2000,1,1)

    download_and_move_ei(dl_path, startdate, enddate, [39],
                      keep_original=False, grid_size=None,
                      h_steps=[0, 6, 12, 18], netcdf=False, dry_run=True)

    assert(os.listdir(dl_path) == ['2000'])
    assert(os.listdir(os.path.join(dl_path, '2000')) == ['001'])
    assert(len(os.listdir(os.path.join(dl_path, '2000', '001'))) == 4)

    should_dlfiles = ['ERAINT_OPER_0001_AN_20000101_0000.grb',
                      'ERAINT_OPER_0001_AN_20000101_0600.grb',
                      'ERAINT_OPER_0001_AN_20000101_1200.grb',
                      'ERAINT_OPER_0001_AN_20000101_1800.grb']

    assert(os.listdir(os.path.join(dl_path, '2000', '001')) == should_dlfiles)

    shutil.rmtree(dl_path)

if __name__ == '__main__':
    test_dry_download_era5()