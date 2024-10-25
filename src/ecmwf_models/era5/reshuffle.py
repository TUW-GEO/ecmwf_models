# -*- coding: utf-8 -*-

"""
Image to time series conversion tools.
"""
import warnings

import os
import pandas as pd
import numpy as np
from datetime import time, datetime, timedelta

from repurpose.img2ts import Img2Ts
from c3s_sm.misc import update_ts_summary_file, read_summary_yml

from ecmwf_models.era5.reader import ERA5NcDs, ERA5GrbDs
from ecmwf_models.grid import ERA_RegularImgGrid, ERA5_RegularImgLandGrid
from ecmwf_models.utils import parse_filetype, parse_product, get_first_last_image_date

def extend_ts(ts_path, **img2ts_kwargs):
    """
    Append any new data from the image path to the time series data.
    This function is only applied to time series file that were created
    using the img2ts function.
    This will use the start from the previously written metadata,
    and process only parameters that are already present in the time series
    files.

    Parameters
    ----------
    ts_path: str
        Directory containing time series files to extend. It is also
        expected that there is a `overview.yml` file in this directory.
    img2ts_kwargs:
        All kwargs are optional, if they are not given, we use them from the
        previously created `overview.yml` file. If they are passed here,
        they will override the values from the yml file.
    """
    if not os.path.isfile(os.path.join(ts_path, 'overview.yml')):
        raise FileNotFoundError(
            "No overview.yml file found in the passed directory. "
            "This file is required to use the same settings to extend an "
            "existing record. NOTE: Use the `era5 download` or "
            "`era5land download` programs first."
        )

    ts_props = read_summary_yml(ts_path)

    for k, v in ts_props['img2ts_kwargs'].items():
        if k not in img2ts_kwargs:
            if k == 'startdate':
                old_enddate = pd.to_datetime(
                    ts_props["img2ts_kwargs"]["enddate"]).to_pydatetime()
                startdate = old_enddate + timedelta(days=1)
                img2ts_kwargs['startdate'] = startdate
            elif k in ['enddate', 'outputpath']:  # fields from yml to ignore
                continue
            else:
                img2ts_kwargs[k] = v

    if 'enddate' not in img2ts_kwargs:
        img2ts_kwargs['enddate'] = None   # All available images

    img2ts(outputpath=ts_path, **img2ts_kwargs)


def img2ts(
        input_root,
        outputpath,
        startdate,
        enddate=None,
        variables=None,
        product=None,
        bbox=None,
        h_steps=(0, 6, 12, 18),
        land_points=False,
        imgbuffer=50,
):
    """
    Reshuffle method applied to ERA images for conversion into netcdf time
    series format.
    Note: ERA5 and ERA5-Land files are preferred over their T-counterpart,
    in case that multiple files for a time stamp are present!

    Parameters
    ----------
    input_root: str
        Input path where ERA image data was downloaded to.
    outputpath : str
        Output path, where the reshuffled netcdf time series are stored.
    startdate : str
        Start date, from which images are read and time series are generated.
        Format YYYY-mm-dd
    enddate : str, optional (default: None)
        End date, from which images are read and time series are generated.
        Format YYYY-mm-dd. If None is passed, then the last available image
        date is used.
    variables: tuple or str
        Variables to read from the passed images and convert into time
        series format.
    product : str, optional (default: None)
        Either era5 or era5-land, if None is passed we guess the product from
        the downloaded image files.
    bbox: tuple optional (default: None)
        (min_lon, min_lat, max_lon, max_lat) - wgs84.
        To load only a subset of the global grid / file.
    h_steps : list or tuple, optional (default: (0, 6, 12, 18))
        Hours at which images are read for each day and used for reshuffling,
        therefore this defines the sub-daily temporal resolution of the time
        series that are generated.
    land_points: bool, optional (default: False)
        Reshuffle only land points. Uses the ERA5 land mask to create a land
        grid.
        The land grid is fixed to 0.25*0.25 or 0.1*0.1 deg for now.
    imgbuffer: int, optional (default: 50)
        How many images to read at once before writing time series.
        This number affects how many images are stored in memory and should
        be chosen according to the available amount of memory and the size of
        a single image.
    """
    startdate = pd.to_datetime(startdate).to_pydatetime().date()

    if enddate is None:
        enddate = get_first_last_image_date(input_root)

    enddate = pd.to_datetime(enddate).to_pydatetime().date()

    if startdate > enddate:
        warnings.warn(
            f"Start date {startdate} is greater than end date {enddate}. Abort."
        )
        return

    filetype = parse_filetype(input_root)
    product: str = parse_product(input_root) if product is None else product

    if land_points:
        if product == "era5":
            grid = ERA5_RegularImgLandGrid(
                resolution=0.25, bbox=bbox)
        elif product == "era5-land":
            grid = ERA5_RegularImgLandGrid(resolution=0.1, bbox=bbox)
        else:
            raise NotImplementedError(
                product, "Land grid not implemented for product.")
    else:
        if product.lower() in ['era5-land', 'era5-land-t']:
            grid = ERA_RegularImgGrid(resolution=0.1, bbox=bbox)
        elif product.lower() in ['era5', 'era5-t']:
            grid = ERA_RegularImgGrid(resolution=0.25, bbox=bbox)
        else:
            raise NotImplementedError(product,
                                      "Grid not implemented for product.")

    if filetype == "grib":
        input_dataset = ERA5GrbDs(
            root_path=input_root,
            parameter=variables,
            subgrid=grid,
            array_1D=True,
            h_steps=h_steps,
            product=product,
            mask_seapoints=False,
        )
    elif filetype == "netcdf":
        input_dataset = ERA5NcDs(
            root_path=input_root,
            parameter=variables,
            subgrid=grid,
            array_1D=True,
            h_steps=h_steps,
            product=product,
            mask_seapoints=False,
        )
    else:
        raise Exception("Unknown file format")

    if not os.path.exists(outputpath):
        os.makedirs(outputpath)

    global_attr = {f"product": f"{product.upper()} (from {filetype})"}

    # get time series attributes from first day of data.
    first_date_time = datetime.combine(startdate, time(h_steps[0], 0))

    # get time series attributes from first day of data.
    data = input_dataset.read(first_date_time)
    ts_attributes = data.metadata

    props = {'product': product, 'filetype': filetype,
             'last_update': datetime.now()}

    kwargs = {
        'input_root': input_root,
        'outputpath': outputpath,
        'variables': None if variables is None else list(variables),
        'land_points': land_points,
        'startdate': startdate,
        'enddate': enddate,
        'h_steps': h_steps,
        'bbox': None if bbox is None else list(bbox),
        'imgbuffer': imgbuffer
    }

    props["img2ts_kwargs"] = kwargs

    reshuffler = Img2Ts(
        input_dataset=input_dataset,
        outputpath=outputpath,
        startdate=str(startdate),
        enddate=str(enddate),
        input_grid=grid,
        imgbuffer=imgbuffer,
        cellsize_lat=5.0,
        cellsize_lon=5.0,
        ts_dtypes=np.dtype("float32"),
        global_attr=global_attr,
        zlib=True,
        unlim_chunksize=1000,
        ts_attributes=ts_attributes,
        backend='multiprocessing',
        n_proc=1,
    )

    reshuffler.calc()

    update_ts_summary_file(outputpath, props)

