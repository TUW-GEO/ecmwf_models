import click
from datetime import datetime

from ecmwf_models.era5.download import (download_and_move,
                                        download_record_extension)
from ecmwf_models.utils import (default_variables)

from ecmwf_models.era5.reshuffle import Reshuffler, extend_ts


@click.command(
    "download",
    context_settings={
        'show_default': True,
        'help_option_names': ['-h', '--help']
    },
    short_help="Download ERA5 reanalysis image data between two "
    "dates from the Copernicus Climate Data Store (CDS). "
    "Before this program can be used, you have to "
    "register an account at CDS, and should setup a `.cdsapirc` "
    "file as described here: "
    "https://cds.climate.copernicus.eu/how-to-api")
@click.argument("PATH", type=click.Path(writable=True))
@click.option(
    '--start',
    '-s',
    type=click.STRING,
    default=str(datetime(1979, 1, 1)),
    help="First date of the period to download data for. Format: YYYY-MM-DD")
@click.option(
    '--end',
    '-e',
    type=click.STRING,
    default=str(datetime.now().date()),
    help="Last date of the period to download data for. Format: YYYY-MM-DD")
@click.option(
    '--variables',
    '-v',
    type=click.STRING,
    default=','.join(default_variables('era5', 'short_name')),
    help="Name of variables to download. To download multiple variables pass "
    "comma-separated names (e.g. `-v swvl1,stl1`). "
    "For all available variables see the docs. ")
@click.option(
    "-k",
    "--keep_original",
    type=click.BOOL,
    default=False,
    help="To keep the original image stacks as downloaded from CDS, "
    "instead of deleting them after extracting individual images, pass "
    "`--keep_original True`")
@click.option(
    "-grb",
    "--as_grib",
    type=click.BOOL,
    default=False,
    help="To download data in grib format instead of netcdf pass "
    "`--as_grib True`.")
@click.option(
    "--h_steps",
    type=str,
    default="0,6,12,18",
    help="Temporal sampling of downloaded images. To download multiple time "
    "stamps or each day, pass comma-separated values. "
    "Pass a set of full hours here, like '--h_steps 0,12' to download "
    "two images for each day, at 0:00 and 12:00 respectively. "
    "By default, we download 6-hourly images starting at 0:00 UTC, "
    "(i.e. `--h_steps 0,6,12,18`")
@click.option(
    '--bbox',
    nargs=4,
    type=click.FLOAT,
    default=None,
    help="4 NUMBERS | min_lon min_lat max_lon max_lat. "
    "Set Bounding Box (lower left and upper right corner) "
    "of area to download (WGS84). Default is global.")
@click.option(
    "--keep_prelim",
    type=click.BOOL,
    default=True,
    help="The last 1-2 month of data are usually 'preliminary' (labelled as "
    "'ERA5-T' and 'ERA5-Land-T') and might be changed if an issue is "
    "detected. When this option is deactivated (`--keep_prelim False`), "
    "only the final data will be kept, while the ERA5-T data is discarded "
    "after download. By default, we also keep preliminary files, but they "
    "get a different file name as the final data.")
@click.option(
    "--max_request_size",
    type=int,
    default=1000,
    help="Maximum number of requests to pass to the CDS API. "
    "The default is 1000, but what is allowed, depends on server "
    "settings. Server settings may change at some point. Change "
    "accordingly here in case that 'the request is too large'. "
    "A smaller number will results in smaller download chunks (slower).")
@click.option(
    "--cds_token",
    type=click.STRING,
    default=None,
    help="To identify with the CDS. Required only if no `.cdsapirc` file "
    "exists in the home directory (see documentation). "
    "You can find your token/key on your CDS user profile page. "
    "Alternatively, you can also set an environment variable "
    "`CDSAPI_KEY` with your token.")
def cli_download_era5(path, start, end, variables, keep_original, as_grib,
                      h_steps, bbox, keep_prelim, max_request_size, cds_token):
    """
    Download ERA5 image data within the chosen period. NOTE: Before using this
    program, create a CDS account and set up a `.cdsapirc` file as described
    here: https://cds.climate.copernicus.eu/how-to-api

    \b
    Required Parameters
    -------------------
    > PATH: string (required)
          Root of local filesystem where the downloaded data will be stored.
          Make sure to set up the CDS API for your account as described at
          https://cds.climate.copernicus.eu/how-to-api
    """
    # The docstring above is slightly different to the normal python one to
    # display it properly on the command line.

    h_steps = [int(h.strip()) for h in h_steps.split(',')]
    variables = [str(v.strip()) for v in variables.split(',')]

    status_code = download_and_move(
        target_path=path,
        startdate=start,
        enddate=end,
        product="era5",
        variables=variables,
        h_steps=h_steps,
        grb=as_grib,
        bbox=bbox,
        keep_original=keep_original,
        stepsize='month',
        n_max_request=max_request_size,
        keep_prelim=keep_prelim,
        cds_token=cds_token,
    )

    return status_code


@click.command(
    "download",
    context_settings={
        'show_default': True,
        'help_option_names': ['-h', '--help']
    },
    short_help="Download ERA5 reanalysis image data between two "
    "dates from the Copernicus Climate Data Store (CDS). "
    "Before this program can be used, you have to "
    "register an account at CDS, and should setup a `.cdsapirc` "
    "file as described here: "
    "https://cds.climate.copernicus.eu/how-to-api")
@click.argument("PATH", type=click.Path(writable=True))
@click.option(
    '--start',
    '-s',
    type=click.STRING,
    default=str(datetime(1979, 1, 1)),
    help="First date of the period to download data for. Format: YYYY-MM-DD")
@click.option(
    '--end',
    '-e',
    type=click.STRING,
    default=str(datetime.now().date()),
    help="Last date of the period to download data for. Format: YYYY-MM-DD")
@click.option(
    '--variables',
    '-v',
    type=click.STRING,
    default=','.join(default_variables('era5-land',
                                       'short_name')),
    help="Name of variables to download. To download multiple variables pass "
    "comma-separated names (e.g. `-v swvl1,stl1`). "
    "For all available variables see the docs. ")
@click.option(
    "-k",
    "--keep_original",
    type=click.BOOL,
    default=False,
    help="To keep the original image stacks as downloaded from CDS, "
    "instead of deleting them after extracting individual images, pass "
    "`--keep_original True`")
@click.option(
    "-grb",
    "--as_grib",
    type=click.BOOL,
    default=False,
    help="To download data in grib format instead of netcdf pass "
    "`--as_grib True`.")
@click.option(
    "--h_steps",
    type=click.STRING,
    default='0,6,12,18',
    help="Temporal sampling of downloaded images. To download multiple time "
    "stamps or each day, pass comma-separated values. "
    "Pass a set of full hours here, like '--h_steps 0,12' to download "
    "two images for each day, at 0:00 and 12:00 respectively. "
    "By default, we download 6-hourly images starting at 0:00 UTC, "
    "(i.e. `--h_steps 0,6,12,18`")
@click.option(
    "--keep_prelim",
    type=click.BOOL,
    default=True,
    help="The last 1-2 month of data are usually 'preliminary' (labelled as "
    "'ERA5-T' and 'ERA5-Land-T') and might be changed if an issue is "
    "detected. When this option is deactivated (`--keep_prelim False`), "
    "only the final data will be kept, while the ERA5-T data is discarded "
    "after download. By default, we also keep preliminary files, but they "
    "get a different file name as the final data.")
@click.option(
    "--max_request_size",
    type=int,
    default=1000,
    help="Maximum number of requests to pass to the CDS API. "
    "The default is 1000, but what is allowed, depends on server "
    "settings. Server settings may change at some point. Change "
    "accordingly here in case that 'the request is too large'. "
    "A smaller number will results in smaller download chunks (slower).")
@click.option(
    "--cds_token",
    type=click.STRING,
    default=None,
    help="To identify with the CDS. Required only if no `.cdsapirc` file "
    "exists in the home directory (see documentation). "
    "You can find your token/key on your CDS user profile page. "
    "Alternatively, you can also set an environment variable "
    "`CDSAPI_KEY` with your token.")
def cli_download_era5land(path, start, end, variables, keep_original, as_grib,
                          h_steps, keep_prelim, max_request_size, cds_token):
    """
    Download ERA5-Land image data within a chosen period.
    NOTE: Before using this program, create a CDS account and set up a
    `.cdsapirc` file as described here:
    https://cds.climate.copernicus.eu/how-to-api

    \b
    Required Parameters
    -------------------
    > PATH: string (required)
          Root of local filesystem where the downloaded data will be stored.
          Make sure to set up the CDS API for your account as described at
          https://cds.climate.copernicus.eu/how-to-api
    """
    # The docstring above is slightly different to the normal python one to
    # display it properly on the command line.

    h_steps = [int(h.strip()) for h in h_steps.split(',')]
    variables = [str(v.strip()) for v in variables.split(',')]

    status_code = download_and_move(
        target_path=path,
        startdate=start,
        enddate=end,
        product="era5-land",
        variables=variables,
        h_steps=h_steps,
        grb=as_grib,
        keep_original=keep_original,
        stepsize='month',
        n_max_request=max_request_size,
        keep_prelim=keep_prelim,
        cds_token=cds_token)

    return status_code


@click.command(
    "update_img",
    context_settings={
        'show_default': True,
        'help_option_names': ['-h', '--help']
    },
    short_help="Extend an existing set of images by downloading new data "
    "with the same settings as before."
    "NOTE: First use the `era5 download` or `era5land download` "
    "programs.")
@click.argument("path", type=click.Path(writable=True))
@click.option(
    "--cds_token",
    type=click.STRING,
    default=None,
    help="To identify with the CDS. Required only if no `.cdsapirc` file "
    "exists in the home directory (see documentation). "
    "You can find your token/key on your CDS user profile page. "
    "Alternatively, you can also set an environment variable "
    "`CDSAPI_KEY` with your token.")
def cli_update_img(path, cds_token=None):
    """
    Download new images from CDS to your existing local archive. Use the same
    settings as before.
    NOTE: First use the `era5 download` or `era5land download` programs.
    The so-created archive can then be updated using this program.

    \b
    Required Parameters
    -------------------
    > PATH: string (required)
          Path where previously downloaded images are stored. There must
          be a file `overview.yml` which contains the download settings.
          Make sure to set up the CDS API for your account as described at
          https://cds.climate.copernicus.eu/how-to-api,
    """
    # The docstring above is slightly different to the normal python one to
    # display it properly on the command line.

    download_record_extension(path, cds_token=cds_token)


@click.command(
    "reshuffle",
    context_settings={
        'show_default': True,
        'help_option_names': ['-h', '--help']
    },
    short_help="Convert previously downloaded ERA5/ERA5-Land image "
    "data into a time series format.")
@click.argument("IMG_PATH", type=click.Path(readable=True))
@click.argument("TS_PATH", type=click.Path(writable=True))
@click.option(
    '--start',
    '-s',
    type=click.STRING,
    default=None,
    help="First date of the period to reshuffle data for. By default, the "
         "first available image is used. Format: YYYY-MM-DD")
@click.option(
    '--end',
    '-e',
    type=click.STRING,
    default=None,
    help="Last date of the period to reshuffle data for. By default, the last"
         "available image is used. Format: YYYY-MM-DD")
@click.option(
    '--variables',
    '-v',
    type=click.STRING,
    default=None,
    help="Subset of variables to convert. Pass comma-separated names"
    "to select multiple variables (short names, as in the input images, "
    "e.g. `-v swvl1,stl1`). If not specified, all variables from the "
    "first image file are used.")
@click.option(
    '--land_points',
    '-l',
    type=click.BOOL,
    show_default=True,
    default=False,
    help="To store only time series for points that are over land, pass "
         "`--land_points True`. ")
@click.option(
    '--bbox',
    nargs=4,
    type=click.FLOAT,
    default=None,
    help="4 NUMBERS | min_lon min_lat max_lon max_lat. "
    "Set Bounding Box (lower left and upper right corner) "
    "of area to reshuffle (WGS84). Default is global.")
@click.option(
    "--h_steps",
    type=click.STRING,
    default="0,6,12,18",
    help="Full hour time stamps of images to include in time series. "
    "To select multiple, pass comma-separated values here, "
    "e.g. '--h_steps 0,12' will only include data from images at "
    "0:00 and 12:00 UTC and ignore all other available time stamps."
    "By default, we include data for every 6th hour each day.")
@click.option(
    '--imgbuffer',
    '-b',
    type=click.INT,
    default=50,
    help="Number of images to read into memory at once before "
    "conversion to time series. A larger buffer means faster "
    "processing but requires more memory.")
def cli_reshuffle(img_path, ts_path, start, end, variables, land_points, bbox,
                  h_steps, imgbuffer):
    """
    Convert previously downloaded ERA5 or ERA5-Land image data into a
    time series format.

    \b
    Required Parameters
    -------------------
    > IMG_PATH: string (required)
          Directory where the downloaded image data is stored, i.e., where
          annual folders are found.
    > TS_PATH: string (required)
          Root of local filesystem where the time series should be stored.
    """

    h_steps = [int(h.strip()) for h in h_steps.split(',')]

    if variables is not None:
        variables = [str(v.strip()) for v in variables.split(',')]

    print(f"Converting ERA5/ERA5-Land images in period from "
          f"{'first available image' if start is None else start} to "
          f"{'last available image' if end is None else end} into "
          f"time series to {ts_path}.")

    reshuffler = Reshuffler(img_path, ts_path,
                            variables=variables,
                            h_steps=h_steps,
                            land_points=land_points,
                            product=None  # Infer prod automatically from files
                            )
    reshuffler.reshuffle(startdate=start, enddate=end, bbox=bbox,
                         imgbuffer=imgbuffer)


@click.command(
    "update_ts",
    context_settings={
        'show_default': True,
        'help_option_names': ['-h', '--help']
    },
    short_help="Append new image data to an existing time series archive.")
@click.argument("TS_PATH", type=click.Path(writable=True))
@click.option(
    '--imgpath',
    '-p',
    type=click.STRING,
    default=None,
    help="Manually specify where the image data to extend the time "
    "series are located. If this is not specified, we use the previously "
    "used path from the `overview.yml` file stored with the time series "
    "data.")
@click.option(
    '--imgbuffer',
    '-b',
    type=click.INT,
    default=50,
    help="Number of images to read into memory at once before "
    "conversion to time series. A larger buffer means faster "
    "processing but requires more memory.")
def cli_extend_ts(ts_path, imgpath, imgbuffer):
    """
    Append new image data to an existing time series archive. The archive must
    be created first using the `reshuffle` program. We will use the same
    settings as in the initial run (see `overview.yml` in TS_PATH) for
    consistent extensions.

    \b
    Required Parameters
    -------------------
    > TS_PATH: string (required)
          Root of local filesystem where the time series from a previous call
          of `reshuffle` are stored. New data will be appended to the existing
          files!
    """
    kwargs = dict(ts_path=ts_path, imgbuffer=imgbuffer)

    if imgpath is not None:  # otherwise use path from yml
        kwargs["input_root"] = imgpath

    extend_ts(**kwargs)


@click.group(short_help="ERA5 Command Line Programs imported from the "
             "`ecmwf_models` pip package.")
def era5():
    pass


era5.add_command(cli_download_era5)
era5.add_command(cli_update_img)
era5.add_command(cli_reshuffle)
era5.add_command(cli_extend_ts)


@click.group(short_help="ERA5-Land Command Line Programs imported from the "
             "`ecmwf_models` pip package.")
def era5land():
    pass


era5land.add_command(cli_download_era5land)
era5land.add_command(cli_update_img)
era5land.add_command(cli_reshuffle)
era5land.add_command(cli_extend_ts)
