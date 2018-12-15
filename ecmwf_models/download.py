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
Module for Downloading ECMWF ERA Interim and ERA5 data in grib and netcdf format.
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
import xarray as xr
import pandas as pd
from datedown.fname_creator import create_dt_fpath
import shutil
import numpy as np


def download_era(start, end, parameters, target, product='ERA-Interim', format='grib1',
                 grid_size=None, timesteps=[0, 6, 12, 18], landmask = True):
    """
    Download era 5 data

    Parameters
    ----------
    start : date
        start date
    end : date
        end date
    parameters : list
        parameter ids, see wiki
    target : str
        path at which to save the downloaded grib file
    product : str, optional
        Name of the model, "ERA-interim" (default) or "ERA5"
    format: str, optional
        format of the downloaded data, netcdf or grib1 (default)
    grid_size: [float,float], optional
        size of the grid in form (lon, lat), which the data is resampled to
        If None is passed the minimum grid for the accoring product is chosen
    timesteps: list
        list of times for which data is downloaded
    landmask: bool
        If True, also download the land/sea mask
    """
    server = ECMWFDataServer()
    param_strings = []

    if product == 'ERA-Interim':
        dataset = 'interim'
        dataclass = 'ei'
    elif product == 'ERA5':
        dataset = 'era5'
        dataclass = 'ea'
    else:
        raise ValueError('Unknown ECMWF product. Use "ecmwf_download -h" too show supported data sets')

    if landmask and 172 not in parameters:
        parameters.append(172)

    for parameter in parameters:
        param_strings.append("%d.128" % parameter)

    timestep_strings = []
    for timestep in timesteps:
        timestep_strings.append("%02d" % timestep)

    param_string = '/'.join(param_strings)
    timestep_string = '/'.join(timestep_strings)
    date_string = "%s/to/%s" % (start.strftime("%Y-%m-%d"),
                                end.strftime("%Y-%m-%d"))

    grid_size = "%f/%f" % (grid_size[0], grid_size[1]) if grid_size else None

    # ATTENTION: When downloading netcdf files steps and times must not overlap!!
    # see: https://software.ecmwf.int/wiki/display/CKB/What+to+do+with+ECCODES+ERROR+%3A+Try+using+the+-T+option
    dl_params = {"class": dataclass, "dataset": dataset, "expver": "1", "stream": "oper", "type": "an", "levtype": "sfc",
                 "param": param_string, "date": date_string, "time": timestep_string, "step": "0", "grid": grid_size,
                 "format": format, "target": target}

    if not grid_size:
        if format == 'netcdf':
            if product == 'ERA5':
                grid_size = "%f/%f" % (0.3,0.3)
            else:
                grid_size = "%f/%f" % (0.75,0.75)
            dl_params['grid'] = grid_size
        else:
            del dl_params['grid']
    else:
        if (any(size < 0.75 for size in grid_size) and product == 'ERA-Interim') or \
           (any(size < 0.3 for size in grid_size) and product == 'ERA5'):
            raise Warning('Custom grid smaller than original ERA data. See https://software.ecmwf.int/wiki/display/CKB/Does+downloading+data+at+higher+resolution+improve+the+output')

    server.retrieve(dl_params)



def save_ncs_from_nc(input_nc, output_path, product_name,
                     filename_templ='{product}_{gridsize}_%Y%m%d_%H%M.nc'):
    """
    takes monthly netcdf files as downloaded by the function above and saves each time step
    in a separate file

    Parameters
    ----------
    input_nc : string
        filepath of the downloaded .nc file
    output_path : string
        where to save the resulting netcdf files
    product_name : string
        name of the ECMWF model (for filename generation)
    local_subdirs : list, optional
        List of subfolders for organizing downloaded data
    filename_templ : string, optional
        template for naming each separated nc file
    """
    localsubdirs = ['%Y', '%j']

    nc_in = xr.open_dataset(input_nc, mask_and_scale=True)
    latdiff = np.abs(np.round(np.ediff1d(nc_in.latitude.values),3))[0]
    londiff = np.abs(np.round(np.ediff1d(nc_in.longitude.values),3))[0]
    gridsize = '%s_%s' % (str(latdiff), str(londiff))

    filename_templ = filename_templ.format(product=product_name,
                                           gridsize=gridsize)
    for time in nc_in.time.values:
        subset = nc_in.sel(time=time)

        timestamp = pd.Timestamp(time).to_pydatetime()
        filepath = create_dt_fpath(timestamp,
                                      root=output_path,
                                      fname=filename_templ,
                                      subdirs=localsubdirs)
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        subset.to_netcdf(filepath)
    nc_in.close()


def save_gribs_from_grib(input_grib, output_path, product_name,
                         filename_templ="{product}_OPER_0001_AN_%Y%m%d_%H%M.grb"):
    """
    takes monthly grib files as downloaded by the function above and saves each time step
    in a separate file

    Parameters
    ----------
    input_nc : string
        filepath of the downloaded .grb file
    output_path : string
        where to save the resulting grib files
    product_name : string
        name of the ECMWF model (for filename generation)
    local_subdirs : list, optional
        List of subfolders for organizing downloaded data
    filename_templ : string, optional
        template for naming each separated nc file
    """
    localsubdirs = ['%Y', '%j']
    grib_in = pygrib.open(input_grib)

    grib_in.seek(0)
    for grb in grib_in:
        template = filename_templ
        param_id = grb['marsParam']
        #N = grb['N']
        step = grb['startStep']
        filedate = datetime(grb['year'], grb['month'], grb['day'], grb['hour'])

        template = template.format(product=product_name)
                                   #param_id=param_id,
                                   #N=N)

        filepath = create_dt_fpath(filedate,
                                   root=output_path,
                                   fname=template,
                                   subdirs=localsubdirs)
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        grb_out = open(filepath, 'ab')

        grb_out.write(grb.tostring())
        grb_out.close()
    grib_in.close()


def download_and_move(parameters, startdate, enddate, product, format,
                      target_path, keep_original=False, grid_size=None, timesteps=[0, 6, 12, 18]):
    """
    Downloads the data from the ECMWF servers and moves them to the target path.
    This is done in 30 day increments between start and end date to be efficient with the MARS system.
    See the recommendation for doing it this way in
    https://software.ecmwf.int/wiki/display/WEBAPI/ERA-Interim+daily+retrieval+efficiency

    The files are then extracted into separate grib files per parameter and stored
    in yearly folders under the target_path.

    Parameters
    ----------
    parameters : list
        parameter ids
    startdate: datetime
        first date to download
    enddate: datetime
        last date to download
    product: str
        Name of the dataset to download (eg. ERA5, ERA-Interim)
    format: str
        format of the dataset to download (eg netcdf, grib)
    target_path: string
        path to which to copy the extracted parameter grib files
    keep_original: bool
        keep the original downloaded data
    grid_size: list
        [lon, lat] extent of the grid (regular for netcdf, at lat=0 for grib)
    timesteps: list, optional
        list of timesteps to download
    """
    td = timedelta(days=30)
    current_start = startdate

    if format not in ['netcdf', 'grib1']:
        raise ValueError("Choose 'grib1' or 'netcdf' as format")
    fextension = '.grb' if format == 'grib1' else '.nc'


    while current_start <= enddate:
        current_end = current_start + td
        if current_end >= enddate:
            current_end = enddate

        fname = current_start.strftime("%Y%m%d_")
        fname = current_end.strftime(fname + "%Y%m%d" + fextension)
        downloaded_data_path = os.path.join(target_path, 'temp_downloaded')
        if not os.path.exists(downloaded_data_path):
            os.mkdir(downloaded_data_path)
        downloaded_data = os.path.join(downloaded_data_path, fname)

        download_era(current_start, current_end, parameters, downloaded_data,
                     product, format, grid_size, timesteps=timesteps)

        if format == 'netcdf':
            save_ncs_from_nc(downloaded_data, target_path, product)
        else:
            save_gribs_from_grib(downloaded_data, target_path, product)
        if not keep_original:
            shutil.rmtree(downloaded_data_path)
        current_start = current_end + timedelta(days=1)


def mkdate(datestring):
    '''
    Turns a datetime string into a datetime object
    :param datestring: str
        input datetime string
    :return:
        datetime
    '''
    if len(datestring) == 10:
        return datetime.strptime(datestring, '%Y-%m-%d')
    if len(datestring) == 16:
        return datetime.strptime(datestring, '%Y-%m-%dT%H:%M')


def parse_args(args):
    """
    Parse command line parameters for recursive download

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Download ECMWF reanalysis model data")
    parser.add_argument("localroot",
                        help='Root of local filesystem where the data is stored.')
    parser.add_argument("parameters", metavar="parameters", type=int,
                        nargs="+",
                        help=("Parameters to convert in numerical format. e.g."
                              "39 40 41 42 for Volumetric soil water layers 1 to 4."
                              "A list of possible parameters is available at http://apps.ecmwf.int/codes/grib/param-db "
                              "or by using the 'View MARS request' option in the web based ordering system."))
    parser.add_argument("-s", "--start", type=mkdate,
                        help=("Startdate. Either in format YYYY-MM-DD or YYYY-MM-DDTHH:MM."
                              "If no data is found there then the first available date of the product is used."))
    parser.add_argument("-e", "--end", type=mkdate,
                        help=("Enddate. Either in format YYYY-MM-DD or YYYY-MM-DDTHH:MM."
                              "If not given then the current date is used."))
    parser.add_argument("-p", "--product", type=str, default='ERA-Interim',
                        help=("ECMWF product, ERA-Interim (default) or ERA5"))
    parser.add_argument("-f", "--format", type=str, default='grib',
                        help=("Downloaded data format, grib1 (default) or netcdf. "
                              "Info on GRIB: https://software.ecmwf.int/wiki/display/CKB/What+are+GRIB+files"))
    parser.add_argument("--grid_size", type=float, default=None, nargs='+',
                        help=("lon lat, Size of the grid that the data is stored to. "
                              "Must be set when downloading as 'netcdf'. "
                              "Should be at least (and is by default) (0.75,0.75) for ERA-Interim "
                              "and (0.3,0.3) for ERA5"))

    args = parser.parse_args(args)

    # set defaults that can not be handled by argparse
    if args.start is None:
        args.start = datetime(1979, 1, 1)
    if args.end is None:
        args.end = datetime.now()


    print("Downloading {} data from {} to {} into folder {}".format(args.product,
                                                                    args.start.isoformat(),
                                                                    args.end.isoformat(),
                                                                    args.localroot))
    return args


def main(args):
    args = parse_args(args)

    download_and_move(args.parameters, args.start, args.end, args.product,
                      args.format, args.localroot, grid_size=args.grid_size)


def run():
    main(sys.argv[1:])

if __name__ == '__main__':
    run()
