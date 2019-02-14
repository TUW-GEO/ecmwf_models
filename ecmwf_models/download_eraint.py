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
Module to download ERA Interim from terminal.
'''

from ecmwfapi import ECMWFDataServer
import argparse
import sys
import warnings
try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")
import os
from datetime import datetime, timedelta
import shutil
from ecmwf_models.download import save_ncs_from_nc, save_gribs_from_grib, mkdate



def default_variables():
    'These variables are being downloaded, when None are passed by the user'
    variables = [39, 40, 41, 42, 172]

    return variables


def download_eraint(target_path, start, end, variables, grid_size=None,
                    h_steps=[0, 6, 12, 18], netcdf=False, dry_run=False):
    """
    Download era interim data

    Parameters
    ----------
    target_path : str
        path at which to save the downloaded grib file
    start : date
        start date
    end : date
        end date
    variables : list
        parameter ids, see wiki
    product : str, optional
        Name of the model, "ERA-interim" (default) or "ERA5"
    grid_size: [float,float], optional
        size of the grid in form (lon, lat), which the data is resampled to
        If None is passed the minimum grid for the accoring product is chosen
    h_steps: list, optional (default: [0, 6, 12, 18])
        List of full hours to download data at the selected dates
    netcdf: bool, optional (default: False)
        Download data as netcdf files instead of grib files
    dry_run: bool
        Do not download anything, this is just used for testing the functions
    """
    server = ECMWFDataServer()
    param_strings = []

    dataset = 'interim'
    dataclass = 'ei'


    for variable in variables:
        param_strings.append("%d.128" % variable)

    timestep_strings = []
    for timestep in h_steps:
        timestep_strings.append("%02d" % timestep)

    param_string = '/'.join(param_strings)
    timestep_string = '/'.join(timestep_strings)
    date_string = "%s/to/%s" % (start.strftime("%Y-%m-%d"),
                                end.strftime("%Y-%m-%d"))

    grid_size = "%f/%f" % (grid_size[0], grid_size[1]) if grid_size else None

    # ATTENTION: When downloading netcdf files steps and times must not overlap!!
    # see: https://software.ecmwf.int/wiki/display/CKB/What+to+do+with+ECCODES+ERROR+%3A+Try+using+the+-T+option
    dl_params = {"class": dataclass, "dataset": dataset, "expver": "1",
                 "stream": "oper", "type": "an", "levtype": "sfc",
                 "param": param_string, "date": date_string,
                 "time": timestep_string, "step": "0", "grid": grid_size,
                 "format": 'netcdf' if netcdf else 'grib1',
                 "target": target_path}

    if not grid_size:
        if netcdf:
            grid_size = "%f/%f" % (0.75,0.75)
            dl_params['grid'] = grid_size
        else:
            del dl_params['grid']
    else:
        if any(size < 0.75 for size in grid_size):
            raise Warning('Custom grid smaller than original ERA Interim resolution. '
                          'See https://software.ecmwf.int/wiki/display/CKB/Does+downloading+data+at+higher+resolution+improve+the+output')
    if not dry_run:
        server.retrieve(dl_params)



def download_and_move(target_path, startdate, enddate, variables=None,
                      land_sea_mask=True, keep_original=False, grid_size=None,
                      h_steps=[0, 6, 12, 18], netcdf=False, dry_run=False):
    """
    Downloads the data from the ECMWF servers and moves them to the target path.
    This is done in 30 days increments between start and end date to be efficient
    with the MARS system.
    See the recommendation for doing it this way in
    https://software.ecmwf.int/wiki/display/WEBAPI/ERA-Interim+daily+retrieval+efficiency

    The files are then extracted into separate grib/nc files and stored in
    yearly folders under the target_path.

    Parameters
    ----------
    target_path: str
        Path to which to copy the extracted parameter files
    startdate: datetime
        First date to download
    enddate: datetime
        Last date to download
    variables : list, optional (default: None)
        List of variable ids to pass to the client, if None are passed, the default
        variable ids will be downloaded.
    land_sea_mask : bool, optional (default: True)
        Add the variable for a land sea mask to the parameters
    keep_original: bool, optional (default: False)
        Keep the original downloaded data
    grid_size: list, optional (default: None)
        [lon, lat] extent of the grid (regular for netcdf, at lat=0 for grib)
        If None is passed, the default grid size for the data product is used.
    h_steps: list, optional (default: [0, 6, 12, 18])
        List of full hours to download data at the selected dates
    netcdf: bool, optional (default: False)
        Download data as netcdf files instead of grib files
    dry_run: bool
        Do not download anything, this is just used for testing the functions
    """
    variables = variables if variables is not None else default_variables()

    if land_sea_mask and (172 not in variables):
        variables.append(172)

    td = timedelta(days=30)
    current_start = startdate

    while current_start <= enddate:
        current_end = current_start + td
        if current_end >= enddate:
            current_end = enddate

        fname = '{start}_{end}.{ext}'.format(start=current_start.strftime("%Y%m%d"),
                                             end=current_end.strftime("%Y%m%d"),
                                             ext='nc' if netcdf else 'grb')

        downloaded_data_path = os.path.join(target_path, 'temp_downloaded')
        if not os.path.exists(downloaded_data_path):
            os.mkdir(downloaded_data_path)

        dl_file = os.path.join(downloaded_data_path, fname)

        download_eraint(dl_file, current_start, current_end, variables,
                                    grid_size=grid_size, h_steps=h_steps,
                                    netcdf=netcdf, dry_run=dry_run)

        if netcdf:
            save_ncs_from_nc(dl_file, target_path, 'ERAINT')
        else:
            save_gribs_from_grib(dl_file, target_path, 'ERAINT')

        if not keep_original:
            shutil.rmtree(downloaded_data_path)
        current_start = current_end + timedelta(days=1)



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
        description="Download ERA Interimg reanalysis data (6H) between two dates. "
                    "Before this program can be used, you have to register at ECMWF "
                    "and setup your .ecmwfapirc file as described here: "
                    "https://confluence.ecmwf.int//display/WEBAPI/Access+ECMWF+Public+Datasets#AccessECMWFPublicDatasets-key")
    parser.add_argument("localroot",
                        help='Root of local filesystem where the downloaded data is stored.')
    parser.add_argument("-s", "--start", type=mkdate, default=datetime(1979, 1, 1),
                        help=("Startdate in format YYYY-MM-DD. "
                              "If no data is found there then the first available date of the product is used."))
    parser.add_argument("-e", "--end", type=mkdate, default=datetime.now(),
                        help=("Enddate in format YYYY-MM-DD. "
                              "If not given then the current date is used."))
    parser.add_argument("-var", "--variables", metavar="variables", type=int, default=None,
                        nargs="+",
                        help=("Variable IDs to download "
                              "(default IDs: 39, 40, 41, 42, 172, corresponding to the top 4 levels of soil moisture "
                              "and the land-sea mask) » "
                              "A list of possible IDs is available at http://apps.ecmwf.int/codes/grib/param-db "
                              "or by using the 'View MARS request' option in the web based ordering system."))
    parser.add_argument("-nc", "--netcdf", type=bool, default=False,
                        help=("Download data in netcdf format instead of the default grib format (experimental)"))
    parser.add_argument("--grid_size", type=float, default=None, nargs='+',
                        help=("lon lat. Size of the grid that the data is stored to. "
                              "Should be at least (and is by default) (0.75, 0.75) for ERA-Interim "))

    args = parser.parse_args(args)


    print("Downloading ERA Interim data from {} to {} into {}".
        format(args.start.isoformat(), args.end.isoformat(), args.localroot))

    return args


def main(args):
    args = parse_args(args)

    download_and_move(args.localroot, args.start, args.end, args.variables,
                      keep_original=False, grid_size=args.grid_size,
                      h_steps=[0, 6, 12, 18], netcdf=args.netcdf)


def run():
    main(sys.argv[1:])

if __name__ == '__main__':
    download_and_move(target_path='/home/wolfgang/data-write/eraINT',
                      variables=[39,40], startdate=datetime(1990,1,30),
                      enddate=datetime(1990,2,1), netcdf=True)