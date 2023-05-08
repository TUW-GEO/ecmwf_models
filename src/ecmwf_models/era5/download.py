# -*- coding: utf-8 -*-
"""
Module to download ERA5 from terminal in netcdf and grib format.
"""
import pandas as pd

from ecmwf_models.utils import (
    load_var_table,
    lookup,
    save_gribs_from_grib,
    save_ncs_from_nc,
    mkdate,
    str2bool,
)
import warnings
import errno
import argparse
import sys
import os
import logging
from datetime import datetime, time
import shutil
import cdsapi
import multiprocessing
import numpy as np


def default_variables(product="era5"):
    """
    These variables are being downloaded, when None are passed by the user

    Parameters
    ---------
    product : str, optional (default: 'era5')
        Name of the era5 product to read the default variables for.
        Either 'era5' or 'era5-land'.
    """
    lut = load_var_table(name=product)
    defaults = lut.loc[lut["default"] == 1]["dl_name"].values
    return defaults.tolist()


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


def split_chunk(timestamps,
                n_vars,
                n_hsteps,
                max_req_size=1000,
                reduce=False,
                daily_request=False):
    """
    Split the passed time stamps into chunks for a valid request. One chunk
    can at most hold data for one month or one day, but cannot be larger than
    the maximum request size.

    Parameters
    ----------
    timestamps: pd.DatetimeIndex
        List of daily timestamps to split into chunks
    n_vars: int
        Number of variables in each request.
    max_req_size: int, optional (default: 1000)
        Maximum size of a request that the CDS API can handle
    reduce: bool, optional (default: False)
        Return only the start and end of each subperiod instead of all
        time stamps.
    daily_request: bool, optional (default: False)
        Only submit daily requests, otherwise monthly requests are allowed
        (if the max_req_size is not reached).

    Returns
    -------
    chunks: list
        List of start and end dates that contain a chunk that the API can
        handle.
    """
    n = int(max_req_size / n_vars / n_hsteps)

    def yield_chunk():
        for _, chunk_year in timestamps.groupby(timestamps.year).items():
            for _, chunk_month in chunk_year.groupby(chunk_year.month).items():
                if daily_request:
                    for _, chunk_day in chunk_month.groupby(
                            chunk_month.day).items():
                        yield chunk_day
                else:
                    yield chunk_month

    # each chunk contains either time stamps for one month, or for less,
    # if the request of one month would be too large.
    all_chunks = []
    for chunk in yield_chunk():
        if len(chunk) > n:
            chunks = split_array(chunk, n)
        else:
            chunks = np.array([chunk])
        for chunk in chunks:
            if reduce:
                all_chunks.append(np.array([chunk[0], chunk[-1]]))
            else:
                all_chunks.append(chunk)

    return all_chunks


def download_era5(
    c,
    years,
    months,
    days,
    h_steps,
    variables,
    target,
    grb=False,
    product="era5",
    dry_run=False,
    cds_kwds={},
):
    """
    Download era5 reanalysis data for single levels of a defined time span

    Parameters
    ----------
    c : cdsapi.Client
        Client to pass the request to
    years : list
        Years for which data is downloaded ,e.g. [2017, 2018]
    months : list
        Months for which data is downloaded, e.g. [4, 8, 12]
    days : list
        Days for which data is downloaded (range(31)=All days)
        e.g. [10, 20, 31]
    h_steps: list
        List of full hours to download data at the selected dates e.g [0, 12]
    variables : list, optional (default: None)
        List of variables to pass to the client, if None are passed, the
        default variables will be downloaded.
    target : str
        File name, where the data is stored.
    geb : bool, optional (default: False)
        Download data in grib format
    product : str
        ERA5 data product to download, either era5 or era5-land
    dry_run: bool, optional (default: False)
        Do not download anything, this is just used for testing the
        functionality
    cds_kwds: dict, optional
        Additional arguments to be passed to the CDS API retrieve request.

    Returns
    ---------
    success : bool
        Return True after downloading finished
    """

    if dry_run:
        return

    request = {
        "format": "grib" if grb else "netcdf",
        "variable": variables,
        "year": [str(y) for y in years],
        "month": [str(m).zfill(2) for m in months],
        "day": [str(d).zfill(2) for d in days],
        "time": [time(h, 0).strftime("%H:%M") for h in h_steps],
    }
    request.update(cds_kwds)
    if product == "era5":
        request["product_type"] = "reanalysis"
        c.retrieve("reanalysis-era5-single-levels", request, target)
    elif product == "era5-land":
        c.retrieve("reanalysis-era5-land", request, target)
    else:
        raise ValueError(
            product, "Unknown product, choose either 'era5' or 'era5-land'")

    return True


class CDSStatusTracker:
    """
    Track the status of the CDS download by using the CDS callback functions
    """

    statuscode_ok = 0
    statuscode_error = -1
    statuscode_unavailable = 10

    def __init__(self):
        self.download_statuscode = self.statuscode_ok

    def handle_error_function(self, *args, **kwargs):
        message_prefix = args[0]
        message_body = args[1]
        if self.download_statuscode != self.statuscode_unavailable:
            if (message_prefix.startswith("Reason:") and
                    message_body == "Request returned no data"):
                self.download_statuscode = self.statuscode_unavailable
            else:
                self.download_statuscode = self.statuscode_error
        logging.error(*args, **kwargs)


def download_and_move(
    target_path,
    startdate,
    enddate,
    product="era5",
    variables=None,
    keep_original=False,
    h_steps=(0, 6, 12, 18),
    grb=False,
    dry_run=False,
    grid=None,
    remap_method="bil",
    cds_kwds={},
    stepsize="month",
    n_max_request=1000,
) -> int:
    """
    Downloads the data from the ECMWF servers and moves them to the target
    path.
    This is done in 30 day increments between start and end date.

    The files are then extracted into separate grib files per parameter and
    stored in yearly folders under the target_path.

    Parameters
    ----------
    target_path : str
        Path where the files are stored to
    startdate: datetime
        first date to download
    enddate: datetime
        last date to download
    product : str, optional (default: ERA5)
        Either ERA5 or ERA5Land
    variables : list, optional (default: None)
        Name of variables to download
    keep_original: bool (default: False)
        keep the original downloaded data
    h_steps: list or tuple
        List of full hours to download data at the selected dates e.g [0, 12]
    grb: bool, optional (default: False)
        Download data as grib files
    dry_run: bool
        Do not download anything, this is just used for testing the functions
    grid : dict, optional (default: None)
        A grid on which to remap the data using CDO. This must be a dictionary
        using CDO's grid description format, e.g.::

            grid = {
                "gridtype": "lonlat",
                "xsize": 720,
                "ysize": 360,
                "xfirst": -179.75,
                "yfirst": 89.75,
                "xinc": 0.5,
                "yinc": -0.5,
            }

        Default is to use no regridding.
    remap_method : str, optional (dafault: 'bil')
        Method to be used for regridding. Available methods are:
        - "bil": bilinear (default)
        - "bic": bicubic
        - "nn": nearest neighbour
        - "dis": distance weighted
        - "con": 1st order conservative remapping
        - "con2": 2nd order conservative remapping
        - "laf": largest area fraction remapping
    cds_kwds: dict, optional (default: {})
        Additional arguments to be passed to the CDS API retrieve request.
    n_max_request : int, optional (default: 1000)
        Maximum size that a request can have to be processed by CDS. At the
        moment of writing this is 1000 (N_timstamps * N_variables in a request)
        but as this is a server side settings, it can change.

    Returns
    -------
    status_code: int
        0 : Downloaded data ok
        -1 : Error
        -10 : No data available for requested time period
    """
    h_steps = list(h_steps)
    product = product.lower()

    if variables is None:
        variables = default_variables(product=product)
    else:
        # find the dl_names
        variables = lookup(name=product, variables=variables)
        variables = variables["dl_name"].values.tolist()

    if dry_run:
        warnings.warn("Dry run does not create connection to CDS")
        c = None
        cds_status_tracker = None
    else:
        cds_status_tracker = CDSStatusTracker()
        c = cdsapi.Client(
            error_callback=cds_status_tracker.handle_error_function)

    timestamps = pd.DatetimeIndex(
        np.array([
            datetime(t.year, t.month, t.day)
            for t in pd.date_range(startdate, enddate, freq='D')
        ]))

    daily_request = True if stepsize == "day" else False
    req_periods = split_chunk(
        timestamps,
        n_vars=len(variables),
        n_hsteps=len(h_steps),
        max_req_size=n_max_request,
        reduce=True,
        daily_request=daily_request)

    # Since we download month/month or day/day we need to
    # collect all the status codes to return a valid
    # status code for the whole time period
    all_status_codes = []

    pool = multiprocessing.Pool(1)
    for curr_start, curr_end in req_periods:
        curr_start = pd.to_datetime(curr_start).to_pydatetime()
        curr_end = pd.to_datetime(curr_end).to_pydatetime()

        status_code = -1

        fname = "{start}_{end}.{ext}".format(
            start=curr_start.strftime("%Y%m%d"),
            end=curr_end.strftime("%Y%m%d"),
            ext="grb" if grb else "nc",
        )

        downloaded_data_path = os.path.join(target_path, "temp_downloaded")
        if not os.path.exists(downloaded_data_path):
            os.mkdir(downloaded_data_path)
        dl_file = os.path.join(downloaded_data_path, fname)

        finished, i = False, 0

        while (not finished) and (i < 5):  # try max 5 times
            try:
                finished = download_era5(
                    c,
                    years=[curr_start.year],
                    months=[curr_start.month],
                    days=range(curr_start.day, curr_end.day + 1),
                    h_steps=h_steps,
                    variables=variables,
                    grb=grb,
                    product=product,
                    target=dl_file,
                    dry_run=dry_run,
                    cds_kwds=cds_kwds,
                )
                status_code = 0
                break

            except Exception:  # noqa: E722
                # If no data is available we don't need to retry
                if (cds_status_tracker.download_statuscode ==
                        CDSStatusTracker.statuscode_unavailable):
                    status_code = -10
                    break

                # delete the partly downloaded data and retry
                if os.path.isfile(dl_file):
                    os.remove(dl_file)
                finished = False
                i += 1
                continue

        if status_code == 0:
            if grb:
                pool.apply_async(
                    save_gribs_from_grib,
                    args=(dl_file, target_path),
                    kwds=dict(
                        product_name=product.upper(),
                        keep_original=keep_original,
                    ),
                )
            else:
                pool.apply_async(
                    save_ncs_from_nc,
                    args=(
                        dl_file,
                        target_path,
                    ),
                    kwds=dict(
                        product_name=product.upper(),
                        grid=grid,
                        remap_method=remap_method,
                        keep_original=keep_original,
                    ),
                )

        all_status_codes.append(status_code)

    pool.close()
    pool.join()

    # remove temporary files
    if not keep_original:
        shutil.rmtree(downloaded_data_path)
    if grid is not None:
        gridpath = os.path.join(target_path, "grid.txt")
        if os.path.exists(gridpath):
            os.unlink(gridpath)
        weightspath = os.path.join(target_path, "remap_weights.nc")
        if os.path.exists(weightspath):
            os.unlink(weightspath)

    # if any of the sub-periods was successful we want the function to return 0
    consolidated_status_code = max(all_status_codes)
    return consolidated_status_code


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
        description="Download ERA 5 reanalysis data images between two "
        "dates. Before this program can be used, you have to "
        "register at the CDS and setup your .cdsapirc file "
        "as described here: "
        "https://cds.climate.copernicus.eu/api-how-to")
    parser.add_argument(
        "localroot",
        help="Root of local filesystem where the downloaded data will be "
        "stored.",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=mkdate,
        default=datetime(1979, 1, 1),
        help=("Startdate in format YYYY-MM-DD. "
              "If no data is found there then the first available date of the "
              "product is used."),
    )
    parser.add_argument(
        "-e",
        "--end",
        type=mkdate,
        default=datetime.now(),
        help=("Enddate in format YYYY-MM-DD. "
              "If not given then the current date is used."),
    )
    parser.add_argument(
        "-p",
        "--product",
        type=str,
        default="ERA5",
        help=("The ERA5 product to download. Choose either ERA5 or ERA5-Land. "
              "Default is ERA5."),
    )
    parser.add_argument(
        "-var",
        "--variables",
        metavar="variables",
        type=str,
        default=None,
        nargs="+",
        help=("Name of variables to download. If None are passed, we use the "
              "default ones from the "
              "era5_lut.csv resp. era5-land_lut.csv files in this package. "
              "See the ERA5/ERA5-LAND documentation for more variable names: "
              "     https://confluence.ecmwf.int/display/CKB/"
              "ERA5+data+documentation "
              "     https://confluence.ecmwf.int/display/CKB/"
              "ERA5-Land+data+documentation"),
    )
    parser.add_argument(
        "-keep",
        "--keep_original",
        type=str2bool,
        default="False",
        help=("Also keep the downloaded image stack as retrieved from CDS - "
              "before slicing it into single images - instead of deleting it "
              "after extracting all images. "
              "Pass either True or False. Default is False."),
    )
    parser.add_argument(
        "-grb",
        "--as_grib",
        type=str2bool,
        default="False",
        help=("Download data in grib format instead of netcdf. "
              "Pass either True or False. Default is False."),
    )
    parser.add_argument(
        "--h_steps",
        type=int,
        default=[0, 6, 12, 18],
        nargs="+",
        help=("Temporal resolution of downloaded images. "
              "Pass a set of full hours here, like '--h_steps 0 12'. "
              "By default 6H images (starting at 0:00 UTC, i.e. 0 6 12 18) "
              "will be downloaded"),
    )

    parser.add_argument(
        "--max_request_size",
        type=int,
        default=1000,
        help=("Maximum number of requests that the CDS API allows. "
              "The default is 1000, but depends on server side settings. "
              "Server settings may change at some point. Change "
              "accordingly here in case that 'the request is too large'. "
              "A smaller number will results in smaller download chunks."))

    args = parser.parse_args(args)

    print("Downloading {p} {f} files between {s} and {e} into folder {root}"
          .format(
              p=args.product,
              f="grib" if args.as_grib is True else "netcdf",
              s=args.start.isoformat(),
              e=args.end.isoformat(),
              root=args.localroot,
          ))
    return args


def main(args):
    args = parse_args(args)
    status_code = download_and_move(
        target_path=args.localroot,
        startdate=args.start,
        enddate=args.end,
        product=args.product,
        variables=args.variables,
        h_steps=args.h_steps,
        grb=args.as_grib,
        keep_original=args.keep_original,
        stepsize='month',
        n_max_request=args.max_request_size,
    )
    return status_code


def run():
    status_code = main(sys.argv[1:])
    if status_code == -10:
        return_code = errno.ENODATA  # Default no data status code of 61
    else:
        return_code = status_code

    sys.exit(return_code)
