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
"""
Test module for image to time series conversion.
"""

import os
import glob
import tempfile
import numpy as np
import numpy.testing as nptest
import subprocess
import shutil
from pathlib import Path
import xarray as xr
import yaml
from datetime import datetime

from c3s_sm.misc import read_summary_yml

from ecmwf_models.era5.reshuffle import Reshuffler
from ecmwf_models import ERATs

inpath = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "ecmwf_models-test-data",
    "ERA5",
)

def test_cli_reshuffle_and_update():
    testdata_path = Path(os.path.join(inpath, 'netcdf'))
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        img_path = tempdir / 'images'
        shutil.copytree(testdata_path, img_path)

        # we duplicate 1 file to check whether prioritizing final images over T images works
        ds = xr.open_dataset(testdata_path / '2010' / '001' / "ERA5_AN_20100101_0000.nc")
        ds['swvl1'].values = np.full(ds['swvl1'].values.shape, 99)
        ds.to_netcdf(img_path / '2010' / '001' / "ERA5-T_AN_20100101_0000.nc")

        ts_path = tempdir / 'ts'

        subprocess.call(["era5", "reshuffle", str(img_path), str(ts_path),
                         "--end", "2010-01-01", "-v", "swvl1,swvl2", "-l",
                         "True", "--bbox", "12.0", "46.0", "17.0", "50.0",
                         "--h_steps", "0"])

        ts_reader = ERATs(str(ts_path))
        ts = ts_reader.read(15, 48)
        assert 99 not in ts['swvl1'].values  # verify ERA5-T was NOT used!
        swvl1_values_should = np.array([0.402825], dtype=np.float32)
        nptest.assert_allclose(
            ts["swvl1"].values, swvl1_values_should, rtol=1e-5)

        ts_reader.close()

        # Manipulate settings to update with different time stamp for same day
        props = read_summary_yml(str(ts_path))
        props['img2ts_kwargs']['h_steps'] = [12]
        props['img2ts_kwargs']['startdate'] = datetime(2009, 12, 31)
        props['img2ts_kwargs']['enddate'] = datetime(2009, 12, 31)

        with open(ts_path / 'overview.yml', 'w') as f:
            yaml.dump(props, f, default_flow_style=False, sort_keys=False)

        subprocess.call(["era5", "update_ts", str(ts_path)])
        ts_reader = ERATs(str(ts_path))
        ts = ts_reader.read(15, 48)
        swvl1_values_should = np.array([0.402825, 0.390983], dtype=np.float32)
        nptest.assert_allclose(
            ts["swvl1"].values, swvl1_values_should, rtol=1e-5)

        assert 'swvl2' in ts.columns

        ts_reader.close()

def test_ERA5_reshuffle_nc():
    # test reshuffling era5 netcdf images to time series

    startdate = "2010-01-01"
    enddate = "2010-01-01"
    parameters = ["swvl1", "swvl2"]
    h_steps = [0, 12]
    landpoints = True
    bbox = (12, 46, 17, 50)

    with tempfile.TemporaryDirectory() as ts_path:
        reshuffler = Reshuffler(os.path.join(inpath, 'netcdf'), ts_path,
                                variables=parameters, h_steps=h_steps,
                                land_points=landpoints)
        reshuffler.reshuffle(startdate, enddate, bbox=bbox)

        assert (len(glob.glob(os.path.join(ts_path, "*.nc"))) == 5)
        # less files because only land points and bbox
        ds = ERATs(ts_path, ioclass_kws={"read_bulk": True})
        ts = ds.read(15, 48)
        ds.close()
        swvl1_values_should = np.array([0.402825, 0.390983], dtype=np.float32)
        nptest.assert_allclose(
            ts["swvl1"].values, swvl1_values_should, rtol=1e-5)
        swvl2_values_should = np.array([0.390512, 0.390981], dtype=np.float32)
        nptest.assert_allclose(
            ts["swvl2"].values, swvl2_values_should, rtol=1e-5)


def test_ERA5_reshuffle_grb():
    # test reshuffling era5 netcdf images to time series

    startdate = "2010-01-01"
    enddate = "2010-01-01"
    parameters = ["swvl1", "swvl2"]
    h_steps = [0, 12]
    landpoints = False
    bbox = (12, 46, 17, 50)

    with tempfile.TemporaryDirectory() as ts_path:

        reshuffler = Reshuffler(os.path.join(inpath, 'grib'), ts_path,
                                variables=parameters, h_steps=h_steps,
                                land_points=landpoints)
        reshuffler.reshuffle(startdate, enddate, bbox=bbox)

        assert len(glob.glob(os.path.join(ts_path, "*.nc"))) == 5
        ds = ERATs(ts_path, ioclass_kws={"read_bulk": True})
        ts = ds.read(15, 48)
        ds.close()
        swvl1_values_should = np.array([0.402824, 0.390979], dtype=np.float32)
        nptest.assert_allclose(
            ts["swvl1"].values, swvl1_values_should, rtol=1e-5)
        swvl2_values_should = np.array([0.390514, 0.390980], dtype=np.float32)
        nptest.assert_allclose(
            ts["swvl2"].values, swvl2_values_should, rtol=1e-5)
