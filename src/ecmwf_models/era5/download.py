# -*- coding: utf-8 -*-
"""
Module to download ERA5 from terminal in netcdf and grib format.
"""
import warnings
import os
import logging
from datetime import datetime, time, timedelta
import shutil
import cdsapi
import numpy as np
import pandas as pd

from c3s_sm.misc import read_summary_yml

from repurpose.process import parallel_process
from repurpose.misc import delete_empty_directories

from ecmwf_models.utils import (
    lookup,
    update_image_summary_file,
    default_variables,
    split_array,
    check_api_ready,
    get_first_last_image_date
)
from ecmwf_models.extract import save_ncs_from_nc, save_gribs_from_grib


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
    bbox=None,
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
    grb : bool, optional (default: False)
        Download data in grib format instead of netcdf
    bbox: Tuple[int,int,int,int], optional (default: None)
        Bounding box of the area to download
        (min_lon, min_lat, max_lon, max_lat) - wgs84.
        None will download global images.
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
        "data_format": "grib" if grb else "netcdf",
        "download_format": "unarchived",
        "variable": variables,
        "year": [str(y) for y in years],
        "month": [str(m).zfill(2) for m in months],
        "day": [str(d).zfill(2) for d in days],
        "time": [time(h, 0).strftime("%H:%M") for h in h_steps],
    }
    # name changed at some point?
    request['format'] = request['data_format']

    if bbox is not None:   # maxlat, minlon, minlat, maxlon
        request["area"] = [bbox[3], bbox[0], bbox[1], bbox[2]]

    request.update(cds_kwds)
    if product == "era5":
        request["product_type"] = ["reanalysis"]
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

    def __init__(self, logger=logging.getLogger()):
        self.download_statuscode = self.statuscode_ok
        self.logger = logger

    def handle_error_function(self, *args, **kwargs):
        message_prefix = args[0]
        message_body = args[1]
        if self.download_statuscode != self.statuscode_unavailable:
            if (message_prefix.startswith("Reason:") and
                    message_body == "Request returned no data"):
                self.download_statuscode = self.statuscode_unavailable
            else:
                self.download_statuscode = self.statuscode_error
        self.logger.error(*args, **kwargs)


def download_and_move(
    target_path,
    startdate,
    enddate,
    product="era5",
    variables=None,
    keep_original=False,
    h_steps=(0, 6, 12, 18),
    grb=False,
    bbox=None,
    dry_run=False,
    grid=None,
    remap_method="bil",
    cds_kwds=None,
    stepsize="month",
    n_max_request=1000,
    keep_prelim=True,
    cds_token=None,
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
    product : str, optional (default: era5)
        Either era5 or era5-land
    variables : list, optional (default: None)
        Name of variables to download, see the documentation for all variable
        names. If None is chosen, then the 'default' variables are downloaded.
    keep_original: bool (default: False)
        If True, keep the original downloaded data stack as received from CDS
        after slicing individual time stamps.
    h_steps: tuple, optional (default: (0, 6, 12, 18))
        List of full hours to download data for at the selected dates e.g
        [0, 12] would download at 0:00 and 12:00. Only full hours are possible.
    grb: bool, optional (default: False)
        Download data as grib files instead of netcdf.
        Note that downloading in grib format, does not allow on-the-fly
        resampling (`grid` argument)
    bbox: Tuple[int,int,int,int], optional (default: None)
        Bounding box of the area to download
        (min_lon, min_lat, max_lon, max_lat) - wgs84.
        None will download global images.
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
        To use this option, it is necessary that CDO is installed.
    remap_method : str, optional (dafault: 'bil')
        Method to be used for regridding. Available methods are:
        - "bil": bilinear (default)
        - "bic": bicubic
        - "nn": nearest neighbour
        - "dis": distance weighted
        - "con": 1st order conservative remapping
        - "con2": 2nd order conservative remapping
        - "laf": largest area fraction remapping
    cds_kwds: dict, optional (default: None)
        Additional keyword arguments to be passed to the CDS API request.
        This might be useful in the future, when new server-side options are
        added which are not yet directly supported by this package.
    n_max_request : int, optional (default: 1000)
        Maximum size that a request can have to be processed by CDS. At the
        moment of writing this is 1000 (N_timstamps * N_variables in a request)
        but as this is a server side settings, it can change.
    keep_prelim: bool, optional (default: True)
        Keep preliminary data from ERA5T under a different file name.
        These data are not yet final and might change if an issue is detected.
        If False is chosen, then the preliminary data will be discarded and
        not stored.
    cds_token: str, optional (default: None)
        To identify with the CDS. Required if no .cdsapirc file exists in
        the home directory (see documentation). You can find your token/key
         on your CDS user profile page. Alternatively, the CDSAPI_KEY
         environment variable can be set manually instead of passing the token
         here.

    Returns
    -------
    status_code: int
        Status code summary from all requests:
        0 : All Downloaded data ok
        -1 : Error in at least one request
        -10 : No data available for requested time period
    """
    h_steps = list(h_steps)
    product = product.lower()
    cds_kwds = cds_kwds or dict()

    if variables is None:
        variables = default_variables(product=product)
    else:
        # find the dl_names
        variables = lookup(name=product, variables=variables)
        variables = variables["dl_name"].values.tolist()

    # this logger name is also used by CDS API, don't change it
    logger = logging.getLogger('cdsapi')

    if dry_run:
        warnings.warn("Dry run does not create connection to CDS")
        c = None
        cds_status_tracker = None
    else:
        if cds_token is not None:
            os.environ["CDSAPI_KEY"] = cds_token
        check_api_ready()

        os.makedirs(target_path, exist_ok=True)
        cds_status_tracker = CDSStatusTracker()
        c = cdsapi.Client(
            error_callback=cds_status_tracker.handle_error_function)

    timestamps = pd.DatetimeIndex(
        np.array([
            datetime(t.year, t.month, t.day)
            for t in pd.date_range(startdate, enddate, freq='D')
        ]))

    req_periods = split_chunk(
        timestamps,
        n_vars=len(variables),
        n_hsteps=len(h_steps),
        max_req_size=n_max_request,
        reduce=True,
        daily_request=True if stepsize == "day" else False)

    logger.info(f"Request is split into {len(req_periods)} chunks")
    logger.info(f"Target directory {target_path}")

    downloaded_data_path = os.path.join(target_path, "temp_downloaded")
    if not os.path.exists(downloaded_data_path):
        os.mkdir(downloaded_data_path)

    def _download(curr_start, curr_end):
        curr_start = pd.to_datetime(curr_start).to_pydatetime()
        curr_end = pd.to_datetime(curr_end).to_pydatetime()

        status_code = -1

        fname = "{start}_{end}.{ext}".format(
            start=curr_start.strftime("%Y%m%d"),
            end=curr_end.strftime("%Y%m%d"),
            ext="grb" if grb else "nc")

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
                    bbox=bbox,
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

        if status_code == 0 and os.path.exists(dl_file):
            if grb:
                save_gribs_from_grib(
                    dl_file,
                    target_path,
                    product_name=product.upper(),
                    keep_original=keep_original,
                    keep_prelim=keep_prelim)
            else:
                save_ncs_from_nc(
                    dl_file,
                    target_path,
                    product_name=product.upper(),
                    grid=grid,
                    remap_method=remap_method,
                    keep_original=keep_original,
                    keep_prelim=keep_prelim)

        return status_code

    # Since we download month/month or day/day we need to
    # collect all the status codes to return a valid
    # status code for the whole time period
    all_status_codes = parallel_process(
        _download,
        ITER_KWARGS={
            'curr_start': [p[0] for p in req_periods],
            'curr_end': [p[1] for p in req_periods]
        },
        logger_name='cdsapi',
        loglevel='DEBUG',
        n_proc=1,
        backend='multiprocessing')

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

    delete_empty_directories(target_path)

    dl_settings = {
        'product': product,
        'variables': variables,
        'keep_original': keep_original,
        'h_steps': h_steps,
        'grb': grb,
        'bbox': bbox,
        'grid': grid,
        'remap_method': remap_method,
        'cds_kwds': cds_kwds,
        'stepsize': stepsize,
        'n_max_request': n_max_request,
        'keep_prelim': keep_prelim,
    }

    update_image_summary_file(target_path, dl_settings)

    handlers = logger.handlers[:]

    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()
    handlers.clear()

    # if any of the sub-periods was successful we want the function to return 0
    consolidated_status_code = max(all_status_codes)
    return consolidated_status_code


def download_record_extension(path, dry_run=False, cds_token=None):
    """
    Uses information from an existing record to download additional data
    from CDS.

    Parameters
    ----------
    path: str
        Path where the image data to extend is stored. Must also contain
        a `summary.yml` file.
    dry_run: bool, optional
        Do not download anything, this is just used for testing the functions
    cds_token: str, optional (default: None)
        To identify with the CDS. Required if no `.cdsapirc` file exists in
        the home directory (see documentation). You can find your token/key
        on your CDS user profile page. Alternatively, the CDSAPI_KEY
        environment variable can be set manually instead of passing the token
        here.

    Returns
    -------
    status_code: int
        Status code summary from all requests:
        0 : All Downloaded data ok
        -1 : Error in at least one request
        -10 : No data available for requested time period
    """
    props = read_summary_yml(path)

    last_img = get_first_last_image_date(path)

    startdate = pd.to_datetime(last_img).to_pydatetime() + timedelta(days=1)

    enddate = (pd.to_datetime(datetime.now().date()).to_pydatetime()
               - timedelta(days=1))  # yesterday

    logging.info(f"Downloading record extension from {startdate} to {enddate}")
    logging.info(f"Additional settings {props['download_settings']}")

    return download_and_move(
        path,
        startdate=startdate,
        enddate=enddate,
        cds_token=cds_token,
        dry_run=dry_run,
        **props['download_settings'])
