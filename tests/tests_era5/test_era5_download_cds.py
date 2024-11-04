"""
Tests actually downloading data from the CDS
"""

import os
import tempfile
import unittest
from datetime import datetime
import subprocess

from ecmwf_models.era5.img import ERA5NcImg
from ecmwf_models.utils import check_api_ready

try:
    check_api_ready()
    api_ready = True
except ValueError:
    api_ready = False

class DownloadTest(unittest.TestCase):

    # these tests only run if a username and pw are set in the environment
    # variables. To manually set them: `export USERNAME="my_username"` etc.

    @unittest.skipIf(
        os.environ.get('CDSAPI_KEY') is None and not api_ready,
        'CDSAPI_KEY not found.'
    )
    def test_cli_download(self):

        with tempfile.TemporaryDirectory() as dl_path:
            startdate = enddate = "2023-01-01"

            args = [
                dl_path, '-s', startdate, '-e', enddate,
                '-v', 'swvl1', '--h_steps', '0',
                '--bbox', "-10", "30", "60", "90",
            ]

            subprocess.call(['era5', 'download'] + args)

            # # For debugging don't use subprocess
            # from ecmwf_models.era5.download import download_and_move
            # download_and_move(dl_path, startdate, enddate,
            #                   variables=['swvl1'],
            #                   h_steps=[0], bbox=[-10, 30, 60, 90])

            out_path = os.path.join(dl_path, '2023', '001')
            assert (os.path.exists(out_path))
            imgs = os.listdir(out_path)
            assert len(imgs) == 1

            ds = ERA5NcImg(os.path.join(out_path, imgs[0]), parameter='swvl1')
            img = ds.read(datetime(2023, 1, 1))
            assert img.data['swvl1'].shape == (241, 281)
