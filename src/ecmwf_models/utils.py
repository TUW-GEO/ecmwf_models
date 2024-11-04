# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2019, TU Wien
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
Utility functions for all data products in this package.
"""
import os
import warnings
from datetime import datetime
import pandas as pd
import numpy as np
from netCDF4 import Dataset
from collections import OrderedDict
from parse import parse
import yaml

from ecmwf_models.extract import save_gribs_from_grib
from repurpose.misc import find_first_at_depth

from ecmwf_models.globals import (DOTRC, CDS_API_URL, IMG_FNAME_TEMPLATE,
                                  IMG_FNAME_DATETIME_FORMAT,
                                  SUPPORTED_PRODUCTS)


def parse_product(inpath: str) -> str:
    """
    Tries to find out what product is stored in the path. This is done based
    on the name of the first file in the path that is found.

    Parameters
    ----------
    inpath: str
        Input path where ERA data was downloaded to. Contains annual folders.

    Returns
    -------
    product : str
        Product name
    """
    props = img_infer_file_props(inpath)

    if "era5-land" in props['product'].lower():
        return "era5-land"  # also era5-land-t
    elif "era5" in props['product'].lower():
        return "era5"  # also era5-t
    else:
        raise ValueError(
            f"Could not derive product name from data in {inpath}")


def parse_filetype(inpath: str) -> str:
    """
    Tries to find out the file type by parsing filenames in the passed
    directory.

    Parameters
    ----------
    inpath: str
        Input path where ERA data was downloaded to. Contains annual folders.

    Returns
    -------
    product : str
        Product name
    """
    props = img_infer_file_props(inpath)
    if props['ext'] == 'grb':
        return 'grib'
    else:
        return 'netcdf'


def load_var_table(name="era5", lut=False):
    """
    Load the variables table for supported variables to download.

    Parameters
    ----------
    lut : bool, optional (default: False)
        If set to true only names are loaded, so that they can be used
        for a LUT otherwise the full table is loaded
    """
    name = name.lower()
    if name == "era5":
        era_vars_csv = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "era5", "era5_lut.csv")
    elif name == "era5-land":
        era_vars_csv = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "era5",
            "era5-land_lut.csv",
        )
    else:
        raise ValueError(name, "No LUT for the selected dataset found.")

    if lut:
        dat = pd.read_csv(era_vars_csv)[["dl_name", "long_name", "short_name"]]
    else:
        dat = pd.read_csv(era_vars_csv)

    return dat


def lookup(name, variables):
    """
    Search the passed elements in the lookup table, if one does not exists,
    print a Warning
    """
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
                f"Passed variable {var} is not a supported variable.")

    return lut.loc[selected, :]


def get_default_params(name="era5"):
    """
    Read only lines that are marked as default variable in the csv file

    Parameters
    ----------
    name : str
        Name of the product to get the default parameters for
    """
    vars = load_var_table(name, lut=False)
    return vars.loc[vars.default == 1.0]


def default_variables(product="era5", format='dl_name'):
    """
    These variables are being downloaded, when None are passed by the user

    Parameters
    ---------
    product : str, optional (default: 'era5')
        Name of the era5 product to read the default variables for.
        Either 'era5' or 'era5-land'.
    format: str, optional (default: 'dl_name')
        'dl_name' for name as in the downloaded image data
        'short_name' for short name
        'long_name' for long name
    """
    lut = load_var_table(name=product)
    defaults = lut.loc[lut["default"] == 1][format].values
    return defaults.tolist()


def make_era5_land_definition_file(
    data_file,
    out_file,
    data_file_y_res=0.25,
    ref_var="lsm",
    threshold=0.5,
    exclude_antarctica=True,
):
    """
    Create a land grid definition file from a variable within a downloaded,
    regular (netcdf) era5 file.

    Parameters
    ----------
    data_file : str
        Path to the downloaded file that contains the image that is used as the
        reference for creating the land definition file.
    out_file: str
        Full output path to the land definition file to create.
    data_file_y_res : float, optional (default: 0.25)
        The resolution of the data file in latitude direction.
    ref_var: str, optional (default: 'lsm')
        A variable in the data_file that is the reference for the
        land definition.
        By default, we use the land-sea-mask variable.
    threshold: float, optional (default: 0.5)
        Threshold value below which a point is declared water,
        and above (or equal) which it is declared a land-point.
        If None is passed, then a point is declared a land point
        if it is not masked (numpy masked array) in the reference variable.
    exclude_antarctica: bool, optional (default: True)
        Cut off the definition file at -60° Lat to exclude Land Points
        in Antarctica.
    """
    lat_name, lon_name = "latitude", "longitude"
    ds_in = Dataset(data_file)
    ds_out = Dataset(out_file, "w", format="NETCDF4")

    for dim_name in ds_in.dimensions.keys():
        ds_out.createDimension(dim_name, size=ds_in.dimensions[dim_name].size)
        ds_out.createVariable(dim_name, "float32", (dim_name,), zlib=True)
        ds_out.variables[dim_name][:] = ds_in.variables[dim_name][:]

    ref = ds_in.variables[ref_var]

    land_mask = np.zeros(ref.shape)

    if np.isnan(threshold):
        land_mask[~ref[:].mask] = 1.0
    else:
        land_mask[ref[:] >= threshold] = 1.0

    # drop values below -60° Lat
    if exclude_antarctica:
        cut_off_lat = -60.0
        index_thres_lat = ((180.0 / data_file_y_res) + 1) - (
            (90.0 + cut_off_lat) / data_file_y_res)
        land_mask[int(index_thres_lat):, :] = np.nan
    else:
        cut_off_lat = None

    ds_out.createVariable("land", "float32", (lat_name, lon_name), zlib=True)
    ds_out.variables["land"][:] = land_mask

    land_attrs = OrderedDict([
        ("units", "(0,1)"),
        ("long_name", "Land-sea mask"),
        ("based_on_variable", ref_var),
        ("standard_name", "land_binary_mask"),
        ("threshold_land_>=", str(threshold)),
        ("cut_off_at", str(cut_off_lat)),
    ])

    for attr, val in land_attrs.items():
        ds_out.variables["land"].setncattr(attr, val)

    ds_in.close()
    ds_out.close()


def split_array(array, chunk_size):
    """
    Split an array into chunks of a given size.

    Parameters
    ----------
    array : array-like
        Array to split into chunks
    chunk_size : int
        Size of each chunk

    Returns
    -------
    chunks : list
        List of chunks
    """
    chunks = []
    for i in range(0, len(array), chunk_size):
        chunks.append(array[i:i + chunk_size])
    return chunks


def check_api_ready() -> bool:
    """
    Verify that the API is ready to be used. Otherwise raise an Error.

    Returns:
    --------
    api_ready: bool
        True if api is ready
    """
    if not os.path.isfile(DOTRC):
        key = os.environ.get('CDSAPI_KEY')
        if "CDSAPI_URL" not in os.environ:
            os.environ['CDSAPI_URL'] = CDS_API_URL

        if key is None:
            raise ValueError(
                'Neither CDSAPI_KEY variable nor .cdsapirc file found, '
                'download will not work! '
                'Please create a .cdsapirc file with your API key. '
                'See: https://cds.climate.copernicus.eu/how-to-api')
        else:
            return True
    else:
        if "CDSAPI_URL" in os.environ:
            os.environ.pop("CDSAPI_URL")  # Use URL from file
        return True


def img_infer_file_props(img_root_path: str,
                         fntempl: str = IMG_FNAME_TEMPLATE,
                         start_from_last=False) -> dict:
    """
    Parse file names to retrieve properties from fntempl.
    Does not open any files.

    Parameters
    ----------
    img_root_path: str
        Root directory where annual directories are located
    fntempl: str, optional
        Filename template to parse filenames with
    start_from_last: bool, optional
        Use the last available file instead of the first one.
    """
    fname = find_first_at_depth(img_root_path, 2, reverse=start_from_last)

    if fname is None:
        raise ValueError(f"No matching files for chosen template found in "
                         f"the directory {img_root_path}")
    else:
        file_args = parse(fntempl, fname)
        return file_args.named


def get_first_last_image_date(path, start_from_last=True):
    """
    Parse files in the given directory (or any subdir) using the passed
    filename template. props will contain all fields specified in the template.
    the `datetime` field is required and used to determine the last image date.

    Parameters
    ----------
    path: str
        Path to the directory containing the image files
    start_from_last: bool, optional (default: True')
        Get date from last available file instead of the first available one.

    Returns
    -------
    date: str
        Parse date from the last found image file that matches `fntempl`.
    """
    try:
        props = img_infer_file_props(
            path, fntempl=IMG_FNAME_TEMPLATE, start_from_last=start_from_last)
        dt = datetime.strptime(props['datetime'], IMG_FNAME_DATETIME_FORMAT)
        dt = datetime(dt.year, dt.month, dt.day)
    except ValueError:
        raise ValueError('Could not infer date from filenames. '
                         'Check filename template.')

    return str(dt)


def update_image_summary_file(data_path: str,
                              other_props: dict = None,
                              out_file=None):
    """
    Summarize image metadata as yml file

    Parameters
    ----------
    data_path: str
        Root path to the image archive
    other_props: dict, optional (default: None)
        Other properties to write into the yml file. E.g. download
        options to enable time series update.
    out_file: str, optional (default: None)
        Path to summary file. File will be created/updated.
        If not specified, then `data_path` is used. If a file already exists,
        it will be overwritten.
    """
    try:
        first_image_date = get_first_last_image_date(
            data_path, start_from_last=False)
        last_image_date = get_first_last_image_date(
            data_path, start_from_last=True)
    except ValueError:
        warnings.warn(f"Could not infer date from filenames in {data_path}")
        return

    props = img_infer_file_props(data_path, start_from_last=False)
    _ = props.pop("datetime")
    props['period_from'] = str(pd.to_datetime(first_image_date).date())
    props['period_to'] = str(pd.to_datetime(last_image_date).date())

    props['last_update'] = str(datetime.now())

    props['download_settings'] = {}

    if other_props is not None:
        for k, v in other_props.items():
            props['download_settings'][k] = v

    if out_file is None:
        out_file = os.path.join(data_path, f"overview.yml")

    with open(out_file, 'w') as f:
        yaml.dump(props, f, default_flow_style=False)


def assert_product(product: str) -> str:
    if product not in SUPPORTED_PRODUCTS:
        raise ValueError(f"Got product {product} but expected one of "
                         f"{SUPPORTED_PRODUCTS}")
    return product
