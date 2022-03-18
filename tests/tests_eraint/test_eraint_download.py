# -*- coding: utf-8 -*-
'''
Tests for transferring downloaded data to netcdf or grib files
'''

from ecmwf_models.erainterim.download import download_and_move

import os
import shutil
from datetime import datetime
from tempfile import TemporaryDirectory


def test_dry_download_nc_eraint():

    with TemporaryDirectory() as dl_path:

        dldir = os.path.join(dl_path, 'temp_downloaded')
        os.makedirs(dldir, exist_ok=True)

        thefile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '..', "ecmwf_models-test-data", "download",
                               "eraint_example_downloaded_raw.nc")
        shutil.copyfile(thefile, os.path.join(dl_path, 'temp_downloaded',
                                              '20000101_20000101.nc'))

        startdate = enddate = datetime(2000, 1, 1)

        download_and_move(
            dl_path,
            startdate,
            enddate,
            variables=['swvl1', 'swvl2', 'lsm'],
            keep_original=False,
            h_steps=[0, 12],
            grb=False,
            dry_run=True)

        assert (os.listdir(dl_path) == ['2000'])
        assert (os.listdir(os.path.join(dl_path, '2000')) == ['001'])
        assert(len(os.listdir(os.path.join(dl_path, '2000', '001'))) == 2)

        should_dlfiles = [
            'ERAINT_AN_20000101_0000.nc',
            'ERAINT_AN_20000101_1200.nc',
        ]

        assert (len(os.listdir(os.path.join(dl_path, '2000',
                                            '001'))) == len(should_dlfiles))

        assert (sorted(os.listdir(os.path.join(
            dl_path, '2000', '001'))) == sorted(should_dlfiles))


def test_dry_download_grb_eraint():

    with TemporaryDirectory() as dl_path:

        dldir = os.path.join(dl_path, 'temp_downloaded')
        os.makedirs(dldir, exist_ok=True)

        thefile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '..', "ecmwf_models-test-data", "download",
                               "eraint_example_downloaded_raw.grb")
        shutil.copyfile(thefile, os.path.join(dl_path, 'temp_downloaded',
                                              '20000101_20000101.grb'))

        startdate = enddate = datetime(2000, 1, 1)

        download_and_move(
            dl_path,
            startdate,
            enddate,
            variables=['swvl1', 'swvl2', 'lsm'],
            keep_original=False,
            h_steps=[0, 6, 12, 18],
            grb=True,
            dry_run=True)

        assert (os.listdir(dl_path) == ['2000'])
        assert (os.listdir(os.path.join(dl_path, '2000')) == ['001'])
        assert(len(os.listdir(os.path.join(dl_path, '2000', '001'))) == 2)

        should_dlfiles = [
            'ERAINT_AN_20000101_0000.grb',
            'ERAINT_AN_20000101_1200.grb',
        ]
        assert (len(os.listdir(os.path.join(dl_path, '2000',
                                            '001'))) == len(should_dlfiles))

        assert (sorted(os.listdir(os.path.join(
            dl_path, '2000', '001'))) == sorted(should_dlfiles))
