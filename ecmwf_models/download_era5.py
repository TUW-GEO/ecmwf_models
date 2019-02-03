# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2019,TU Wien
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
Module to download ERA5 from terminal.
'''

from download import save_gribs_from_grib, save_ncs_from_nc, mkdate
import argparse
import sys
import warnings
try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")

import os
from datetime import datetime, timedelta, time
import shutil
import cdsapi
import calendar


def default_variables():
    'These variables are being downloaded, when None are passed by the user'
    variables = ['evaporation', 'potential_evaporation', 'soil_temperature_level_1',
    'soil_temperature_level_2', 'soil_temperature_level_3', 'soil_temperature_level_4',
    'soil_type', 'total_precipitation', 'volumetric_soil_water_layer_1',
    'volumetric_soil_water_layer_2', 'volumetric_soil_water_layer_3', 'volumetric_soil_water_layer_4',
    'land_sea_mask']

    return variables

def download_era5(c, years, months, days, h_steps, variables, target, netcdf=False):
    '''
    Download era5 reanalysis data for single levels of a defined time span

    Parameters
    ----------
    c : cdsapi.Client
        Client to pass the request to
    years : list
        Years for which data is downloaded ,e.g. [2017, 2018]
    months : list
        Months for which data is downloaded, e.g. [1, 4, 8, 12]
    days : list
        Days for which data is downloaded (range(31)=All days) e.g. [10, 20, 31]
    variables : list, optional (default: None)
        List of variables to pass to the client, if None are passed, the default
        variables will be downloaded.
    h_steps: list
        List of full hours to download data at the selected dates e.g [0, 12]
    land_sea_mask : bool
        Also download the land sea mask variable.
    target : str
        File name, where the data is stored.
    netcdf : bool, optional (deault: False)
        (Experimental) retrieval of images in netcdf format.

    Returns
    -------

    '''

    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf' if netcdf else 'grib',
            'variable': variables,
            'year': [str(y) for y in years],
            'month': [str(m).zfill(2) for m in months],
            'day': [str(d).zfill(2) for d in days],
            'time': [time(h,0).strftime('%H:%M') for h in h_steps]
        },
        target)


def download_and_move(target_path, startdate, enddate, variables=None,
                      land_sea_mask=True, keep_original=False,
                      h_steps=[0, 6, 12, 18], netcdf=False):
    """
    Downloads the data from the ECMWF servers and moves them to the target path.
    This is done in 30 day increments between start and end date to be efficient with the MARS system.
    See the recommendation for doing it this way in
    https://software.ecmwf.int/wiki/display/WEBAPI/ERA-Interim+daily+retrieval+efficiency

    The files are then extracted into separate grib files per parameter and stored
    in yearly folders under the target_path.

    Parameters
    ----------
    target_path : str
        Path where the files are stored to
    startdate: datetime
        first date to download
    enddate: datetime
        last date to download
    variables : list, optional (default: None)
        Name of variables to download
    land_sea_mask : bool, optional (default: True)
        Add the variable for a land sea mask to the parameters
    keep_original: bool
        keep the original downloaded data
    h_steps: list
        List of full hours to download data at the selected dates e.g [0, 12]
    netcdf: bool, optional (default: False)
        Download data as netcdf files
    """

    variables = variables if variables is not None else default_variables()

    if land_sea_mask and ('land_sea_mask' not in variables):
        variables.append('land_sea_mask')

    curr_start = startdate

    c = cdsapi.Client()

    while curr_start <= enddate:
        sy, sm, sd = curr_start.year, curr_start.month, curr_start.day
        sm_days = calendar.monthrange(sy, sm)[1] # days in the current month
        y, m = sy, sm

        if (enddate.year == y) and (enddate.month == m):
            d = enddate.day
        else:
            d = sm_days

        curr_end = datetime(y, m, d)

        fname = '{start}_{end}.{ext}'.format(start=curr_start.strftime("%Y%m%d"),
                                             end=curr_end.strftime("%Y%m%d"),
                                             ext='nc' if netcdf else 'grb')

        downloaded_data_path = os.path.join(target_path, 'temp_downloaded')
        if not os.path.exists(downloaded_data_path):
            os.mkdir(downloaded_data_path)
        dl_file = os.path.join(downloaded_data_path, fname)

        download_era5(c, years=[sy], months=[sm], days=range(sd, d+1),
                      h_steps=h_steps, variables=variables, netcdf=netcdf,
                      target=dl_file)

        if netcdf:
            save_ncs_from_nc(dl_file, target_path, product_name='ERA5')
        else:
            save_gribs_from_grib(dl_file, target_path, product_name='ERA5')

        if not keep_original:
            shutil.rmtree(downloaded_data_path)

        curr_start = curr_end + timedelta(days=1)


def parse_args(args):
    """
    Parse command line parameters for recursive download

    Parameters
    ----------
    args : list
        Command line parameters as list of strings

    Returns
    ----------
    clparams : argparse.Namespace
        Parsed command line parameters
    """

    parser = argparse.ArgumentParser(
        description="Download ERA 5 reanalysis data (6H) between two dates. "
                    "Before this program can be used, you have to register at the CDS "
                    "and setup your .cdsapirc file as described here: "
                    "https://cds.climate.copernicus.eu/api-how-to")
    parser.add_argument("localroot",
                        help='Root of local filesystem where the downloaded data will be stored.')
    parser.add_argument("-s", "--start", type=mkdate, default=datetime(1979, 1, 1),
                        help=("Startdate in format YYYY-MM-DD. "
                              "If no data is found there then the first available date of the product is used."))
    parser.add_argument("-e", "--end", type=mkdate, default=datetime.now(),
                        help=("Enddate in format YYYY-MM-DD. "
                              "If not given then the current date is used."))
    parser.add_argument("-var", "--variables", metavar="variables", type=str, default=None,
                        nargs="+",
                        help=("Name of variables to download "
                              "(default variables:"
                              "     evaporation, potential_evaporation, soil_temperature_level_1, "
                              "     soil_temperature_level_2, soil_temperature_level_3, soil_temperature_level_4, "
                              "     soil_type, total_precipitation, volumetric_soil_water_layer_1, "
                              "     volumetric_soil_water_layer_2, volumetric_soil_water_layer_3, "
                              "     volumetric_soil_water_layer_4, land_sea_mask) » "
                              "See the ERA5 documentation for more variable names: "
                              "     https://confluence.ecmwf.int/display/CKB/ERA5+data+documentation"))
    parser.add_argument("-nc", "--netcdf", type=bool, default=False,
                        help=("Download data in netcdf format, instead of the default grib format (experimental)"))

    args = parser.parse_args(args)


    print("Downloading ERA5 data from {} to {} into folder {}".format(args.start.isoformat(),
                                                                      args.end.isoformat(),
                                                                      args.localroot))
    return args


def main(args):
    args = parse_args(args)

    download_and_move(args.localroot, args.start, args.end, args.variables,
                      args.netcdf)


def run():
    main(sys.argv[1:])

if __name__ == '__main__':
    download_and_move(target_path='/home/wolfgang/data-write/era5',
                      variables=None, startdate=datetime(1990,1,30),
                      enddate=datetime(1990,2,1), netcdf=True)


