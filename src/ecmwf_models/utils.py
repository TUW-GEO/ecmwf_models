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

import warnings
import os
from datetime import datetime
import xarray as xr
import pandas as pd
from datedown.fname_creator import create_dt_fpath
import argparse
import numpy as np
from netCDF4 import Dataset
from collections import OrderedDict

try:
    from cdo import Cdo
    cdo_available = True
except ImportError:
    cdo_available = False

try:
    import pygrib
    pygrib_available = True
except ImportError:
    pygrib_available = False


class CdoNotFoundError(ModuleNotFoundError):

    def __init__(self, msg=None):
        _default_msg = "cdo and/or python-cdo not installed. " \
                       "Use conda to install it them under Linux."
        self.msg = _default_msg if msg is None else msg


def str2bool(v):
    """
    Parse a string to True/False

    Parameters
    ---------
    v : str
        String to parse, must be part of the lists below.

    Return
    ---------
    str2bool : bool
        The parsed bool from the passed string
    """
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def save_ncs_from_nc(
    input_nc,
    output_path,
    product_name,
    filename_templ="{product}_AN_%Y%m%d_%H%M.nc",
    grid=None,
    keep_original=True,
    remap_method="bil",
):
    """
    Split the downloaded netcdf file into daily files and add to folder
    structure necessary for reshuffling.

    Parameters
    ----------
    input_nc : str
        Filepath of the downloaded .nc file
    output_path : str
        Where to save the resulting netcdf files
    product_name : str
        Name of the ECMWF model (only for filename generation)
    filename_templ : str, optional (default: "{product}_AN_%Y%m%d_%H%M.nc")
        Template for naming each separated nc file
    keep_original: bool
        keep the original downloaded data
    """
    localsubdirs = ["%Y", "%j"]

    nc_in = xr.open_dataset(input_nc, mask_and_scale=True)

    if grid is not None:
        if not cdo_available:
            raise CdoNotFoundError()

        cdo = Cdo()
        gridpath = os.path.join(output_path, "grid.txt")
        weightspath = os.path.join(output_path, "remap_weights.nc")
        if not os.path.exists(gridpath):
            with open(gridpath, "w") as f:
                for k, v in grid.items():
                    f.write(f"{k} = {v}\n")

    for time in nc_in.time.values:
        subset = nc_in.sel(time=time)
        if (abs((datetime(2022, 1, 1) - datetime.now()).days) < 90):
            warnings.warn(
                f'Data for {time} may contain experimental versions of '
                f'variables')
        if 'expver' in subset.dims:
            subset_merge = subset.sel(expver=subset['expver'].values[0])
            for e in subset['expver'].values[1:]:
                subset_merge = subset_merge.combine_first(subset.sel(expver=e))
            subset = subset_merge
        else:
            filename_templ = filename_templ.format(product=product_name)

        timestamp = pd.Timestamp(time).to_pydatetime()
        filepath = create_dt_fpath(
            timestamp,
            root=output_path,
            fname=filename_templ,
            subdirs=localsubdirs,
        )
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        if grid is not None:
            if not os.path.exists(weightspath):
                # create weights file
                getattr(cdo, "gen" + remap_method)(
                    gridpath, input=subset, output=weightspath)
            subset = cdo.remap(
                ",".join([gridpath, weightspath]),
                input=subset,
                returnXDataset=True,
            )

        # same compression for all variables
        var_encode = {"zlib": True, "complevel": 6}
        subset.to_netcdf(
            filepath, encoding={var: var_encode for var in subset.variables})

    nc_in.close()

    if not keep_original:
        os.remove(input_nc)
    if grid is not None:
        cdo.cleanTempDir()


def save_gribs_from_grib(
    input_grib,
    output_path,
    product_name,
    filename_templ="{product}_AN_%Y%m%d_%H%M.grb",
    keep_original=True,
):
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
    localsubdirs = ["%Y", "%j"]
    grib_in = pygrib.open(input_grib)

    grib_in.seek(0)
    for grb in grib_in:
        template = filename_templ
        filedate = datetime(grb["year"], grb["month"], grb["day"], grb["hour"])

        template = template.format(product=product_name)

        filepath = create_dt_fpath(
            filedate, root=output_path, fname=template, subdirs=localsubdirs)

        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        grb_out = open(filepath, "ab")

        grb_out.write(grb.tostring())
        grb_out.close()
    grib_in.close()
    if not keep_original:
        os.remove(input_grib)


def mkdate(datestring):
    """
    Turns a datetime string into a datetime object

    Parameters
    -----------
    datestring: str
        Input datetime string

    Returns
    -----------
    datetime : datetime
        Converted string
    """
    if len(datestring) == 10:
        return datetime.strptime(datestring, "%Y-%m-%d")
    if len(datestring) == 16:
        return datetime.strptime(datestring, "%Y-%m-%dT%H:%M")


def parse_product(inpath: str) -> str:
    """
    Tries to find out what product is stored in the path. This is done based
    on the name of the first file in the path that is found.

    Parameters
    ----------
    inpath: str
        Input path where ERA data was downloaded to

    Returns
    -------
    product : str
        Product name
    """
    onedown = os.path.join(inpath, os.listdir(inpath)[0])
    twodown = os.path.join(onedown, os.listdir(onedown)[0])

    for path, subdirs, files in os.walk(twodown):
        for name in files:
            filename, extension = os.path.splitext(name)
            parts = filename.split("_")

            if "ERA5-LAND" in parts:
                return "era5-land"
            elif "ERA5" in parts:
                return "era5"
            elif "ERAINT" in parts:
                return "eraint"
            else:
                continue


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

    if ".nc" in filelist and ".grb" not in filelist:
        return "netcdf"
    elif ".grb" in filelist and ".nc" not in filelist:
        return "grib"
    else:
        # if file type cannot be detected, guess grib
        return "grib"


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
    elif name == "eraint":
        era_vars_csv = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "erainterim",
            "eraint_lut.csv",
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
    raise a Warning
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
        Path to the downloaded file that cotains the image that is used as the
        reference for creating the land definition file.
    out_file: str
        Full output path to the land defintion file to create.
    data_file_y_res : float, optional (default: 0.25)
        The resolution of the data file in latitude direction.
    ref_var: str, optional (default: 'lsm')
        A variable in the data_file that is the reference for the
        land definiton.
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
