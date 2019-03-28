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
import os
from datetime import datetime
import xarray as xr
import pandas as pd
from datedown.fname_creator import create_dt_fpath
import argparse
import numpy as np

try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")


def str2bool(v):
    '''
    Parse a string to True/False

    Parameters
    ---------
    v : str
        String to parse, must be part of the lists below.

    Return
    ---------
    str2bool : bool
        The parsed bool from the passed string
    '''
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def save_ncs_from_nc(input_nc, output_path, product_name,
                     filename_templ='{product}_AN_%Y%m%d_%H%M.nc'):
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

    filename_templ = filename_templ.format(product=product_name)

    for time in nc_in.time.values:
        subset = nc_in.sel(time=time)
        timestamp = pd.Timestamp(time).to_pydatetime()
        filepath = create_dt_fpath(timestamp,
                                   root=output_path,
                                   fname=filename_templ,
                                   subdirs=localsubdirs)
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        # same compression for all variables
        var_encode = {'zlib': True, 'complevel': 6}
        subset.to_netcdf(filepath, encoding={
                         var: var_encode for var in subset.variables})
    nc_in.close()


def save_gribs_from_grib(input_grib, output_path, product_name,
                         filename_templ="{product}_AN_%Y%m%d_%H%M.grb"):
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


def load_var_table(name='ERA5', lut=False):
    '''
    Load the variables table for supported variables to download.

    Parameters
    --------
    lut : bool, optional (default: False)
        If set to true only names are loaded, so that they can be used for a LUT
        otherwise the full table is loaded
    '''
    if name == 'ERA5':
        era_vars_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'era5', 'era5_lut.csv')
    elif name == 'ERAINT':
        era_vars_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'erainterim', 'eraint_lut.csv')
    else:
        raise ValueError('No LUT for the selected dataset found.')

    if lut:
        dat = pd.read_csv(era_vars_csv)[['dl_name', 'long_name', 'short_name']]
    else:
        dat = pd.read_csv(era_vars_csv)

    return dat


def lookup(name, variables):
    '''
    Search the passed elements in the lookup table, if one does not exists,
    raise a Warning
    '''
    lut = load_var_table(name=name, lut=True)

    selected = []
    for var in variables:
        found = False
        for row in lut.itertuples():
            if var in row:
                selected.append(row.Index)
                found = True
                break
        if found:
            continue
        else:
            raise ValueError(
                'Passed variable {} is not in the list of supported variables.'.format(var))

    return lut.loc[selected, :]


def get_default_params(name='ERA5'):
    '''
    Read only lines that are marked as default variable in the csv file

    Parameters:
    ---------
    name : str
        Name of the product to get the default parameters for
    '''
    vars = load_var_table(name, lut=False)
    return vars.loc[vars.default == 1.0]
