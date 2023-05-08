"""
Tests actually downloading data from the CDS
"""

import os
import tempfile

from ecmwf_models.era5.download import main
from ecmwf_models.era5.interface import ERA5NcImg
import unittest
from datetime import datetime
import pytest


class DownloadTest(unittest.TestCase):

    # these tests only run if a username and pw are set in the environment
    # variables. To manually set them: `export USERNAME="my_username"` etc.
    @unittest.skipIf(
        os.environ.get('CDSAPI_KEY') is None,
        'CDSAPI_KEY not found. Make sure the environment variable exists.'
    )
    @pytest.mark.wget
    def test_full_download(self):

        home = os.path.expanduser('~')

        with open(os.path.join(home, '.cdsapirc'), 'w') as f:
            f.write("url: https://cds.climate.copernicus.eu/api/v2\n")
            f.write(f"key: {os.environ.get('CDSAPI_KEY')}")

        with tempfile.TemporaryDirectory() as dl_path:
            startdate = enddate = "2023-01-01"

            args = [
                dl_path, '-s', startdate, '-e', enddate, '-p', 'ERA5',
                '-var', 'swvl1', '--h_steps', '0'
            ]

            main(args)

            out_path = os.path.join(dl_path, '2023', '001')
            assert(os.path.exists(out_path))
            imgs = os.listdir(out_path)
            assert len(imgs) == 1

            ds = ERA5NcImg(os.path.join(out_path, imgs[0]), parameter='swvl1')
            img = ds.read(datetime(2023, 1, 1))
            assert img.data['swvl1'].shape == (721, 1440)
