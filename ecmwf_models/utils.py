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
Utility functions for all data products in this package.
'''

import warnings
try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")

import os
from datetime import datetime
import xarray as xr
import pandas as pd
from datedown.fname_creator import create_dt_fpath
import numpy as np


def save_ncs_from_nc(input_nc, output_path, product_name,
                     filename_templ='{product}_{gridsize}_%Y%m%d_%H%M.nc'):
    """
    Split the downloaded netcdf file into daily files and add to folder structure
    necessary for reshuffling.

    Parameters
    ----------
    input_nc : str
        Filepath of the downloaded .nc file
    output_path : str
        Where to save the resulting netcdf files
    product_name : str
        Name of the ECMWF model (only for filename generation)
    filename_templ : str, optional (default: product_grid_date_time)
        Template for naming each separated nc file
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


def save_ncs(input, output_path, product_name, filename_templ='{product}_%Y%m%d_%H%M.nc'):
    """
    Split the downloaded netcdf OR grib file into daily NETCDF files and add
    to folder structure necessary for reshuffling.

    Parameters
    ----------
    input_nc : str
        Filepath of the downloaded .nc file
    output_path : str
        Where to save the resulting netcdf files
    product_name : str
        Name of the ECMWF model (only for filename generation)
    filename_templ : str, optional (default: product_grid_date_time)
        Template for naming each separated nc file
    """
    filetype = input.split('.')[-1]
    if filetype in ['grb', 'grib']:
        filetype ='grb'
        engine = 'cfgrib'
        backend_kwargs = {'errors': 'ignore'}
    else:
        filetype = 'nc'
        engine = 'scipy'
        backend_kwargs = {}

    localsubdirs = ['%Y', '%j']

    # TODO: cfgrib has problems opening files with multiple variables.
    ds = xr.open_dataset(input, engine=engine, mask_and_scale=True,
                         backend_kwargs=backend_kwargs)

    filename_templ = filename_templ.format(product=product_name)
    for time in ds.time.values:
        subset = ds.sel(time=time)

        timestamp = pd.Timestamp(time).to_pydatetime()
        filepath = create_dt_fpath(timestamp,
                                      root=output_path,
                                      fname=filename_templ,
                                      subdirs=localsubdirs)
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        subset.to_netcdf(filepath, engine='scipy')
    ds.close()


def save_gribs_from_grib(input_grib, output_path, product_name,
                         filename_templ="{product}_OPER_0001_AN_%Y%m%d_%H%M.grb"):
    """
    Split the downloaded grib file into daily files and add to folder structure
    necessary for reshuffling.

    Parameters
    ----------
    input_grib : str
        Filepath of the downloaded .grb file
    output_path : str
        Where to save the resulting grib files
    product_name : str
        Name of the ECMWF model (only for filename generation)
    filename_templ : str, optional (default: product_OPER_0001_AN_date_time)
        Template for naming each separated grb file
    """

    localsubdirs = ['%Y', '%j']
    grib_in = pygrib.open(input_grib)

    grib_in.seek(0)
    for grb in grib_in:
        template = filename_templ
        filedate = datetime(grb['year'], grb['month'], grb['day'], grb['hour'])

        template = template.format(product=product_name)

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


def mkdate(datestring):
    '''
    Turns a datetime string into a datetime object

    Parameters
    -----------
    datestring: str
        Input datetime string

    Returns
    -----------
    datetime : datetime
        Converted string
    '''

    if len(datestring) == 10:
        return datetime.strptime(datestring, '%Y-%m-%d')
    if len(datestring) == 16:
        return datetime.strptime(datestring, '%Y-%m-%dT%H:%M')

def parse_filetype(inpath):
    """
    Tries to find out the file type by searching for
    grib or nc files two subdirectories into the passed input path.
    If function fails, grib is assumed.

    Parameters
    ----------
    inpath: str
        Input path where ERA data was downloaded to

    Returns
    -------
    filetype : str
        File type string.
    """
    onedown = os.path.join(inpath, os.listdir(inpath)[0])
    twodown = os.path.join(onedown, os.listdir(onedown)[0])

    filelist = []
    for path, subdirs, files in os.walk(twodown):
        for name in files:
            filename, extension = os.path.splitext(name)
            filelist.append(extension)

    if '.nc' in filelist and '.grb' not in filelist:
        return 'netcdf'
    elif '.grb' in filelist and '.nc' not in filelist:
        return 'grib'
    else:
        # if file type cannot be detected, guess grib
        return 'grib'


if __name__ == '__main__':
    path = '/home/wpreimes/shares/home/code/ecmwf_models/tests/ecmwf_models-test-data/download/era5_example_downloaded_raw.nc'
    out = '/data-read/USERS/wpreimes/test/era'
    save_ncs(path, out, 'ERAINT')
