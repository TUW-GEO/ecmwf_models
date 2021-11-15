# -*- coding: utf-8 -*-

"""
Module to download ERA Interim from terminal.
"""

from ecmwfapi import ECMWFDataServer
import argparse
import sys
from datetime import datetime, timedelta
import shutil
import os
import warnings

from ecmwf_models.utils import (
    load_var_table,
    save_ncs_from_nc,
    save_gribs_from_grib,
    lookup,
    mkdate,
    str2bool
)


def default_variables() -> list:
    "These variables are being downloaded, when None are passed by the user"
    lut = load_var_table(name="ERAINT")
    defaults = lut.loc[lut["default"] == 1]["dl_name"].values
    return defaults.tolist()


def download_eraint(
    target_path,
    start,
    end,
    variables,
    grid_size=None,
    type="fc",
    h_steps=(0, 6, 12, 18),
    grb=False,
    dry_run=False,
    steps=(0,),
):
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
    h_steps: tuple, optional (default: (0, 6, 12, 18))
        List of full hours to download data at the selected dates
    grb: bool, optional (default: False)
        Download data as grb files instead of nc files
    dry_run: bool
        Do not download anything, this is just used for testing the functions
    """
    if dry_run:
        warnings.warn("Dry run does not create connection to ECMWF")
        server = None
    else:
        server = ECMWFDataServer()

    param_strings = []

    dataset = "interim"
    dataclass = "ei"

    for variable in variables:
        param_strings.append(str(variable))

    timestep_strings = []
    for timestep in h_steps:
        timestep_strings.append("%02d" % timestep)

    param_string = "/".join(param_strings)
    timestep_string = "/".join(timestep_strings)
    date_string = "%s/to/%s" % (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
    )

    grid_size = "%f/%f" % (grid_size[0], grid_size[1]) if grid_size else None

    step = "/".join([str(s) for s in steps])
    # ATTENTION: When downloading netcdf files steps and times
    # must not overlap!! see:
    # https://software.ecmwf.int/wiki/display/CKB/What+to+do+with+ECCODES+ERROR+%3A+Try+using+the+-T+option  # noqa: E501

    dl_params = {
        "class": dataclass,
        "dataset": dataset,
        "expver": "1",
        "stream": "oper",
        "type": type,
        "levtype": "sfc",
        "param": param_string,
        "date": date_string,
        "time": timestep_string,
        "step": step,
        "grid": grid_size,
        "format": "grib1" if grb else "netcdf",
        "target": target_path,
    }

    if not grid_size:
        if not grb:
            grid_size = "%f/%f" % (0.75, 0.75)
            dl_params["grid"] = grid_size
        else:
            del dl_params["grid"]
    else:
        if any(size < 0.75 for size in grid_size):
            raise Warning(
                "Custom grid smaller than original ERA Interim resolution. "
                "See https://software.ecmwf.int/wiki/display/CKB/"
                "Does+downloading+data+at+higher+resolution+improve+the+output"  # noqa: E501
            )
    if not dry_run:
        server.retrieve(dl_params)


def download_and_move(
    target_path,
    startdate,
    enddate,
    variables=None,
    keep_original=False,
    grid_size=None,
    type="an",
    h_steps=(0, 6, 12, 18),
    steps=(0,),
    grb=False,
    dry_run=False,
):
    """
    Downloads the data from the ECMWF servers and moves them to the target
    path. This is done in 30 days increments between start and end date to
    be efficient with the MARS system.
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
        List of variable ids to pass to the client, if None are passed,
        the default variable ids will be downloaded.
    keep_original: bool, optional (default: False)
        Keep the original downloaded data
    grid_size: list, optional (default: None)
        [lon, lat] extent of the grid (regular for netcdf, at lat=0 for grib)
        If None is passed, the default grid size for the data product is used.
    type : str, optional (default: 'an')
        Data stream, model to download data for (fc=forecase)
    h_steps: list, optional (default: [0, 6, 12, 18])
        List of full hours to download data at the selected dates
    grb: bool, optional (default: False)
        Download data as grib files instead of netcdf files
    dry_run: bool
        Do not download anything, this is just used for testing the functions
    """
    product = "eraint"
    if variables is None:
        variables = default_variables()
    else:
        # find the dl_names
        variables = lookup(name=product, variables=variables)
        variables = variables["dl_name"].values.tolist()

    td = timedelta(days=30)
    current_start = startdate

    while current_start <= enddate:
        current_end = current_start + td
        if current_end >= enddate:
            current_end = enddate

        fname = "{start}_{end}.{ext}".format(
            start=current_start.strftime("%Y%m%d"),
            end=current_end.strftime("%Y%m%d"),
            ext="grb" if grb else "nc",
        )

        downloaded_data_path = os.path.join(target_path, "temp_downloaded")
        if not os.path.exists(downloaded_data_path):
            os.mkdir(downloaded_data_path)

        dl_file = os.path.join(downloaded_data_path, fname)

        download_eraint(
            dl_file,
            current_start,
            current_end,
            variables,
            grid_size=grid_size,
            h_steps=h_steps,
            type=type,
            steps=steps,
            grb=grb,
            dry_run=dry_run,
        )

        if grb:
            save_gribs_from_grib(dl_file, target_path, product.upper())
        else:
            save_ncs_from_nc(dl_file, target_path, product.upper())

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
        description="Download ERA Interim data (6H) between two dates. "
        "Before this program can be used, you have to register at ECMWF "
        "and setup your .ecmwfapirc file as described here: "
        "https://confluence.ecmwf.int//display/WEBAPI/Access+ECMWF+Public+Datasets#AccessECMWFPublicDatasets-key"  # noqa: E501
    )
    parser.add_argument(
        "localroot",
        help="Root of local filesystem where the downloaded data is stored.",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=mkdate,
        default=datetime(1979, 1, 1),
        help=(
            "Startdate in format YYYY-MM-DD. "
            "If no data is found there then the first available date of "
            "the product is used."
        ),
    )
    parser.add_argument(
        "-e",
        "--end",
        type=mkdate,
        default=datetime.now(),
        help=(
            "Enddate in format YYYY-MM-DD. "
            "If not given then the current date is used."
        ),
    )
    parser.add_argument(
        "-var",
        "--variables",
        metavar="variables",
        type=str,
        default=None,
        nargs="+",
        help=(
            "Name of variables to download. "
            "A list of possible IDs is available at "
            "https://github.com/TUW-GEO/ecmwf_models/tree/master/ecmwf_models/erainterim/eraint_lut.csv "  # noqa: E501
            "or by using the 'View MARS request' option in the web based "
            "ordering system."
        ),
    )
    parser.add_argument(
        "-keep",
        "--keep_original",
        type=str2bool,
        default="False",
        help=(
            "Keep the originally, temporally downloaded file as it is "
            "instead of deleting it afterwards"
        ),
    )
    parser.add_argument(
        "-grb",
        "--as_grib",
        type=str2bool,
        default="False",
        help=(
            "Download data in grib1 format instead of the default "
            "netcdf format"
        ),
    )
    parser.add_argument(
        "--h_steps",
        type=int,
        default=None,
        nargs="+",
        help=("Manually change the temporal resolution of donwloaded images"),
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        nargs="+",
        help=("Manually change the steps"),
    )
    parser.add_argument(
        "--type",
        type=str,
        default="an",
        help=("Manually set the data stream, e.g. 'an' (default) or 'fc'"),
    )
    parser.add_argument(
        "--grid_size",
        type=float,
        default=None,
        nargs="+",
        help=(
            "lon lat. Size of the grid that the data is stored to. "
            "Should be at least (and is by default) "
            "(0.75, 0.75) for ERA-Interim "
        ),
    )

    args = parser.parse_args(args)

    print("ERA Interim data is deprecated. Use ERA5 instead.")
    print(
        "Downloading ERA Interim {} data from {} to {} into folder {}".format(
            "grib" if args.as_grib is True else "netcdf",
            args.start.isoformat(),
            args.end.isoformat(),
            args.localroot,
        )
    )

    return args


def main(args):
    args = parse_args(args)

    download_and_move(
        target_path=args.localroot,
        startdate=args.start,
        enddate=args.end,
        variables=args.variables,
        keep_original=args.keep_original,
        grid_size=args.grid_size,
        h_steps=args.h_steps,
        type=args.type,
        grb=args.as_grib,
    )


def run():
    main(sys.argv[1:])
