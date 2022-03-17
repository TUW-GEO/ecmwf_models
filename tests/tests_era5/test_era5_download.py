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

from ecmwf_models.era5.download import download_and_move, save_ncs_from_nc
from ecmwf_models.utils import CdoNotFoundError, cdo_available

import os
import shutil
from datetime import datetime
import numpy as np
import xarray as xr
import pytest
import tempfile

grid = {
    "gridtype": "lonlat",
    "xsize": 720,
    "ysize": 360,
    "xfirst": -179.75,
    "yfirst": 89.75,
    "xinc": 0.5,
    "yinc": -0.5
}


@pytest.mark.skipif(cdo_available, reason="CDO is installed")
def test_download_with_cdo_not_installed():
    with pytest.raises(CdoNotFoundError):
        with tempfile.TemporaryDirectory() as out_path:
            infile = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..',
                "ecmwf_models-test-data", "download",
                "era5_example_downloaded_raw.nc")
            save_ncs_from_nc(
                infile, out_path, 'ERA5', grid=grid, keep_original=True)


def test_dry_download_nc_era5():
    with tempfile.TemporaryDirectory() as dl_path:
        dl_path = os.path.join(dl_path, 'era5')
        os.mkdir(dl_path)
        os.mkdir(os.path.join(dl_path, 'temp_downloaded'))

        thefile = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            "ecmwf_models-test-data", "download",
            "era5_example_downloaded_raw.nc")
        shutil.copyfile(
            thefile,
            os.path.join(dl_path, 'temp_downloaded', '20100101_20100101.nc'))

        startdate = enddate = datetime(2010, 1, 1)

        download_and_move(
            dl_path,
            startdate,
            enddate,
            variables=['swvl1', 'swvl2', 'lsm'],
            keep_original=False,
            h_steps=[0, 12],
            grb=False,
            dry_run=True)

        assert (os.listdir(dl_path) == ['2010'])
        assert (os.listdir(os.path.join(dl_path, '2010')) == ['001'])
        assert (len(os.listdir(os.path.join(dl_path, '2010', '001'))) == 2)

        should_dlfiles = [
            'ERA5_AN_20100101_0000.nc', 'ERA5_AN_20100101_1200.nc'
        ]

        assert (sorted(os.listdir(os.path.join(
            dl_path, '2010', '001'))) == sorted(should_dlfiles))

        assert (os.listdir(dl_path) == ['2010'])
        assert (os.listdir(os.path.join(dl_path, '2010')) == ['001'])
        assert (len(os.listdir(os.path.join(dl_path, '2010', '001'))) == 2)


def test_dry_download_grb_era5():
    with tempfile.TemporaryDirectory() as dl_path:
        dl_path = os.path.join(dl_path, 'era5')
        os.mkdir(dl_path)
        os.mkdir(os.path.join(dl_path, 'temp_downloaded'))

        thefile = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            "ecmwf_models-test-data", "download",
            "era5_example_downloaded_raw.grb")
        shutil.copyfile(
            thefile,
            os.path.join(dl_path, 'temp_downloaded', '20100101_20100101.grb'))

        startdate = enddate = datetime(2010, 1, 1)

        download_and_move(
            dl_path,
            startdate,
            enddate,
            variables=['swvl1', 'swvl2', 'lsm'],
            keep_original=False,
            h_steps=[0, 12],
            grb=True,
            dry_run=True)

        assert (os.listdir(dl_path) == ['2010'])
        assert (os.listdir(os.path.join(dl_path, '2010')) == ['001'])
        assert (len(os.listdir(os.path.join(dl_path, '2010', '001'))) == 2)

        should_dlfiles = [
            'ERA5_AN_20100101_0000.grb', 'ERA5_AN_20100101_1200.grb'
        ]

        assert (sorted(os.listdir(os.path.join(
            dl_path, '2010', '001'))) == sorted(should_dlfiles))


@pytest.mark.skipif(not cdo_available, reason="CDO is not installed")
def test_download_nc_era5_regridding():
    with tempfile.TemporaryDirectory() as dl_path:
        dl_path = os.path.join(dl_path, 'era5')
        os.mkdir(dl_path)
        os.mkdir(os.path.join(dl_path, 'temp_downloaded'))

        thefile = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..',
            "ecmwf_models-test-data", "download",
            "era5_example_downloaded_raw.nc")
        shutil.copyfile(
            thefile,
            os.path.join(dl_path, 'temp_downloaded', '20100101_20100101.nc'))

        startdate = enddate = datetime(2010, 1, 1)
        download_and_move(
            dl_path,
            startdate,
            enddate,
            variables=['swvl1', 'swvl2', 'lsm'],
            keep_original=False,
            h_steps=[0, 12],
            grb=False,
            dry_run=True,
            grid=grid)

        assert (os.listdir(dl_path) == ['2010'])
        assert (os.listdir(os.path.join(dl_path, '2010')) == ['001'])
        assert (len(os.listdir(os.path.join(dl_path, '2010', '001'))) == 2)

        should_dlfiles = [
            'ERA5_AN_20100101_0000.nc', 'ERA5_AN_20100101_1200.nc'
        ]

        assert (sorted(os.listdir(os.path.join(
            dl_path, '2010', '001'))) == sorted(should_dlfiles))

        for f in os.listdir(os.path.join(dl_path, "2010", "001")):
            ds = xr.open_dataset(os.path.join(dl_path, "2010", "001", f))
            assert dict(ds.dims) == {"lon": 720, "lat": 360}
            assert np.all(np.arange(89.75, -90, -0.5) == ds.lat)
            assert np.all(np.arange(-179.75, 180, 0.5) == ds.lon)

if __name__ == '__main__':
    test_dry_download_nc_era5()