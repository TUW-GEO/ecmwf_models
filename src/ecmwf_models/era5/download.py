# -*- coding: utf-8 -*-

"""
Module to download ERA5 from terminal in netcdf and grib format.
"""

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
from datetime import datetime, timedelta, time
import shutil
import cdsapi
import calendar
import multiprocessing


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
    h_steps=[0, 6, 12, 18],
    grb=False,
    dry_run=False,
    grid=None,
    remap_method="bil",
    cds_kwds={},
    stepsize="month",
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
    keep_original: bool
        keep the original downloaded data
    h_steps: list
        List of full hours to download data at the selected dates e.g [0, 12]
    grb: bool, optional (default: False)
        Download data as grib files
    dry_run: bool
        Do not download anything, this is just used for testing the functions
    grid : dict, optional
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
    remap_method : str, optional
        Method to be used for regridding. Available methods are:
        - "bil": bilinear (default)
        - "bic": bicubic
        - "nn": nearest neighbour
        - "dis": distance weighted
        - "con": 1st order conservative remapping
        - "con2": 2nd order conservative remapping
        - "laf": largest area fraction remapping
    cds_kwds: dict, optional
        Additional arguments to be passed to the CDS API retrieve request.
    stepsize : str, optional
        Size of steps for requests, can be "month" or "day".

    Returns
    -------
    status_code: int
        0 : Downloaded data ok
        -1 : Error
        -10 : No data available for requested time period
    """
    product = product.lower()

    if variables is None:
        variables = default_variables(product=product)
    else:
        # find the dl_names
        variables = lookup(name=product, variables=variables)
        variables = variables["dl_name"].values.tolist()

    curr_start = startdate

    if dry_run:
        warnings.warn("Dry run does not create connection to CDS")
        c = None
        cds_status_tracker = None
    else:
        cds_status_tracker = CDSStatusTracker()
        c = cdsapi.Client(
            error_callback=cds_status_tracker.handle_error_function)

    all_status_codes = [] # Since we download month/month or day/day we need to
                          # collect all the status codes to return a valid
                          # status code for the whole time period
    pool = multiprocessing.Pool(1)
    while curr_start <= enddate:
        status_code = -1
        sy, sm, sd = curr_start.year, curr_start.month, curr_start.day
        y, m = sy, sm
        if stepsize == "month":
            sm_days = calendar.monthrange(sy,
                                          sm)[1]  # days in the current month
            if (enddate.year == y) and (enddate.month == m):
                d = enddate.day
            else:
                d = sm_days
        elif stepsize == "day":
            d = sd
        else:
            raise ValueError(f"Invalid stepsize: {stepsize}")

        curr_end = datetime(y, m, d)

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
                    years=[sy],
                    months=[sm],
                    days=range(sd, d + 1),
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

        curr_start = curr_end + timedelta(days=1)
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
        help=("Also keep the originally, temporarily downloaded image stack "
              "instead of deleting it after extracting single images. "
              "Default is False."),
    )
    parser.add_argument(
        "-grb",
        "--as_grib",
        type=str2bool,
        default="False",
        help=("Download data in grib format instead of netcdf. "
              "Default is False."),
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
    )
    return status_code


def run():
    status_code = main(sys.argv[1:])
    if status_code == -10:
        return_code = errno.ENODATA  # Default no data status code of 61
    else:
        return_code = status_code

    sys.exit(return_code)
