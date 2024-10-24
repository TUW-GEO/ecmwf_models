import os
import click
from datetime import datetime

from ecmwf_models.era5.download import download_and_move, download_record_extension
from ecmwf_models.utils import (
    default_variables,
    img_infer_file_props,
)

from ecmwf_models.era5.reshuffle import img2ts
from ecmwf_models.globals import IMG_FNAME_TEMPLATE

@click.command(
    "download",
    context_settings={'show_default': True},
    short_help="Download ERA5 reanalysis data images between two "
               "dates. Before this program can be used, you have to "
               "register at the CDS and setup your .cdsapirc file "
               "as described here: "
               "https://cds.climate.copernicus.eu/how-to-api")
@click.argument("PATH", type=click.Path(writable=True))
@click.option(
    '--start', '-s',
    type=click.STRING,
    default=str(datetime(1979, 1, 1)),
    help="First date of the period to download data for. Format: YYYY-MM-DD")
@click.option(
    '--end', '-e',
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
    help="Also keep the original image image stack as downloaded from CDS "
         "instead of deleting it after extracting individual images. "
         "Default is False.")
@click.option(
    "-grb",
    "--as_grib",
    type=click.BOOL,
    default=False,
    help="Download data in grib format instead of netcdf. "
         "Pass either True or False. Default is False.")
@click.option(
    "--h_steps",
    type=str,
    default="0,6,12,18",
    help="Temporal sampling of downloaded images. Multiple values are "
         "comma-separated!"
         "Pass a set of full hours here, like '--h_steps 0,12' to download "
         "two images for each day, at 0:00 and 12:00 respectively. "
         "By default, we download 6-hourly images starting at 0:00 UTC, "
         "(i.e., 0,6,12,18)")
@click.option(
    "--max_request_size",
    type=int,
    default=1000,
    help="Maximum number of requests that the CDS API allows. "
         "The default is 1000, but depends on server side settings. "
         "Server settings may change at some point. Change "
         "accordingly here in case that 'the request is too large'. "
         "A smaller number will results in smaller download chunks.")
@click.option(
    "--cds_token",
    type=click.STRING,
    default=None,
    help="To identify with the CDS. Required if no .cdsapirc file exists in "
         "the home directory (see documentation). You can find your token/key "
         "on your CDS user profile page. Alternatively, you can also set"
         "the an environment variable CDSAPI_KEY that contains your token.")
def cli_download_era5(path, start, end, variables, keep_original, as_grib,
                      h_steps, max_request_size, cds_token):
    """
    Download ERA5 image data within a chosen period. NOTE: Before using this
    program, create a CDS account and set up a `.cdsapirc` file as described
    here: https://cds.climate.copernicus.eu/how-to-api

    \b
    Required Parameters
    -------------------
    PATH: string (required)
        Root of local filesystem where the downloaded data will be stored.
        Make sure to set up the CDS API for your account as describe in
        https://cds.climate.copernicus.eu/how-to-api
    """
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
            keep_original=keep_original,
            stepsize='month',
            n_max_request=max_request_size,
            cds_token=cds_token,
        )

    return status_code


@click.command(
    "download",
    context_settings={'show_default': True},
    short_help="Download ERA5-LAND reanalysis data images between two "
               "dates. Before this program can be used, you have to "
               "register at the CDS and setup your .cdsapirc file "
               "as described here: "
               "https://cds.climate.copernicus.eu/how-to-api "
               "Alternatively, you can pass your KEY/TOKEN here using the "
               "--cds_token option.")
@click.argument("PATH", type=click.Path(writable=True))
@click.option(
    '--start', '-s',
    type=click.STRING,
    default=str(datetime(1979, 1, 1)),
    help="First date of the period to download data for. Format: YYYY-MM-DD")
@click.option(
    '--end', '-e',
    type=click.STRING,
    default=str(datetime.now().date()),
    help="Last date of the period to download data for. Format: YYYY-MM-DD")
@click.option(
    '--variables',
    '-v',
    type=click.STRING,
    default=','.join(default_variables('era5-land', 'short_name')),
    help="Name of variables to download. To download multiple variables pass "
         "comma-separated names (e.g. `-v swvl1,stl1`). "
         "For all available variables see the docs. ")
@click.option(
    "-k",
    "--keep_original",
    type=click.BOOL,
    default=False,
    help="Also keep the original image image stack as downloaded from CDS "
         "instead of deleting it after extracting individual images. "
         "Default is False.")
@click.option(
    "-grb",
    "--as_grib",
    type=click.BOOL,
    default=False,
    help="Download data in grib format instead of netcdf. "
         "Pass either True or False. Default is False.")
@click.option(
    "--h_steps",
    type=click.STRING,
    default='0,6,12,18',
    help="Temporal sampling of downloaded images. "
         "Pass a set of full hours here, like '--h_steps 0,12' to download "
         "two images for each day, at 0:00 and 12:00 respectively. "
         "By default, we download 6-hourly images starting at 0:00 UTC")
@click.option(
    "--max_request_size",
    type=int,
    default=1000,
    help="Maximum number of requests that the CDS API allows. "
         "The default is 1000, but depends on server side settings. "
         "Server settings may change at some point. Change "
         "accordingly here in case that 'the request is too large'. "
         "A smaller number will results in smaller download chunks.")
@click.option(
    "--cds_token",
    type=click.STRING,
    default=None,
    help="To identify with the CDS. Required if no .cdsapirc file exists in "
         "the home directory (see documentation). You can find your token/key "
         "on your CDS user profile page. Alternatively, you can also set"
         "the an environment variable CDSAPI_KEY that contains your token.")
def cli_download_era5land(path, start, end, variables, keep_original, as_grib,
                          h_steps, max_request_size, cds_token):
    """
    Download ERA5-Land image data within a chosen period. NOTE: Before using this
    program, create a CDS account and set up a `.cdsapirc` file as described
    here: https://cds.climate.copernicus.eu/how-to-api

    \b
    Required Parameters
    -------------------
    PATH: string (required)
        Root of local filesystem where the downloaded data will be stored.
        Make sure to set up the CDS API for your account as describe in
        https://cds.climate.copernicus.eu/how-to-api
    """
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
            cds_token=cds_token
        )

    return status_code


@click.command(
    "update_img",
    context_settings={'show_default': True},
    short_help="Extend an existing set of images by downloading new data.")
@click.argument("path", type=click.Path(writable=True))
@click.option(
    "--cds_token",
    type=click.STRING,
    default=None,
    help="To identify with the CDS. Required if no .cdsapirc file exists in "
         "the home directory (see documentation). You can find your token/key "
         "on your CDS user profile page. Or set your token under the "
         "CDSAPI_KEY environment variable")
def cli_update_img(path, cds_token=None):
    """
    Extend a locally existing ERA record by downloading new files that
    don't yet exist locally.
    This will find the latest available local file, and download all
    available extensions.
    NOTE: Use the `era5 download` or `era5land download` program first do
    create a local record to update with this function.

    \b
    Required Parameters
    -------------------
    PATH: string
        Path where previously downloaded C3S SM images are stored. There must
        be a file `overview.yml` which contains the download settings.
        Make sure to set up the CDS API for your account as describe in
        https://cds.climate.copernicus.eu/how-to-api,
    """
    # The docstring above is slightly different to the normal python one to
    # display it properly on the command line.

    download_record_extension(path, cds_token=cds_token)


@click.command(
    "reshuffle",
    context_settings={'show_default': True},
    short_help="Convert downloaded ERA5/ERA5-Land image data into time series.")
@click.argument("IMG_PATH", type=click.Path(readable=True))
@click.argument("TS_PATH", type=click.Path(writable=True))
@click.argument("START", type=click.STRING)
@click.argument("END", type=click.STRING)
@click.option(
    '--variables',
    '-v',
    type=click.STRING,
    default=None,
    help="Subset of variables to convert. Pass comma separated names"
         "to select multiple variables (short names, as in the input images, "
         "e.g. `-v swvl1,stl1`). If not specified, all variables from the first"
         "image file are used.")
@click.option(
    '--land_points', '-l', is_flag=True, show_default=True,
    default=False,
    help="Store only time series for points that are over land. "
         "Default is False.")
@click.option(
    '--bbox',
    nargs=4,
    type=click.FLOAT,
    help="4 NUMBERS | min_lon min_lat max_lon max_lat. "
         "Set Bounding Box (lower left and upper right corner) "
         "of area to reshuffle (WGS84). [default: -180 -90 180 90]")
@click.option(
    "--h_steps",
    type=str,
    default="0,6,12,18",
    nargs=1,
    help="Full hour time stamps to include in time series. To select multiple,"
         "pass comma-separated values here, e.g. '--h_steps 0,12' will only "
         "include data from images at 0:00 and 12:00 UTC and ignore all other "
         "available time stamps."
         "By default, we include data for every 6th hour each day.")
@click.option(
    '--imgbuffer',
    '-b',
    type=click.INT,
    default=50,
    help="NUMBER | Number of images to read into memory at once before "
         "conversion to time series. A larger buffer means faster "
         "processing but requires more memory.")
def cli_reshuffle(img_path, ts_path, start, end, variables, land_points, bbox,
                  h_steps, imgbuffer):
    """
    Convert downloaded ERA5 or ERA5-Land image data into a time series format.

    \b
    Required Parameters
    -------------------
    IMG_PATH: string (required)
        Root of local filesystem where the downloaded image data is stored.
    TS_PATH: string (required)
        Root of local filesystem where the time series should be stored.
    START: string (required)
        Date of the first image to include in the conversion. Format: YYYY-MM-DD
    END: string (required)
        Date of the last image to include in the conversion. Format: YYYY-MM-DD
    """

    h_steps = [int(h.strip()) for h in h_steps.split(',')]
    variables = [str(v.strip()) for v in variables.split(',')]

    print(f"Converting ERA5/ERA5-Land images in period {start} to {end} into "
          f"time series to {ts_path}.")

    img2ts(
        input_root=img_path,
        outputpath=ts_path,
        startdate=start,
        enddate=end,
        variables=variables,
        bbox=bbox,
        h_steps=h_steps,
        land_points=land_points,
        imgbuffer=imgbuffer,
        product=None,  # Infer product from files
    )

@click.group(short_help="ERA5 Command Line Programs imported from the "
                        "`ecmwf_models` pip package.")
def era5():
    pass


era5.add_command(cli_download_era5)
era5.add_command(cli_reshuffle)


@click.group(short_help="ERA5-Land Command Line Programs imported from the "
                        "`ecmwf_models` pip package.")
def era5land():
    pass


era5land.add_command(cli_download_era5land)
era5land.add_command(cli_reshuffle)