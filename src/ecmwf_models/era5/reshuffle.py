# -*- coding: utf-8 -*-

"""
Module for a command line interface to convert the ERA Interim data into a
time series format using the repurpose package
"""

import os
import pandas as pd
import sys
import argparse
import numpy as np
from datetime import time, datetime

from repurpose.img2ts import Img2Ts

from ecmwf_models.era5.interface import ERA5NcDs, ERA5GrbDs
from ecmwf_models.grid import ERA_RegularImgGrid, ERA5_RegularImgLandGrid
from ecmwf_models.utils import mkdate, parse_filetype, parse_product, str2bool

def img2ts(
        input_root,
        outputpath,
        startdate,
        enddate,
        variables,
        product=None,
        bbox=None,
        h_steps=(0, 6, 12, 18),
        land_points=False,
        imgbuffer=50,
):
    """
    Reshuffle method applied to ERA images for conversion into netcdf time
    series format.

    Parameters
    ----------
    input_root: str
        Input path where ERA image data was downloaded to.
    outputpath : str
        Output path, where the reshuffled netcdf time series are stored.
    startdate : str
        Start date, from which images are read and time series are generated.
        Format YYYY-mm-dd
    enddate : str
        End date, from which images are read and time series are generated.
        Format YYYY-mm-dd
    variables: tuple or list or str
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
    imgbuffer: int, optional (default: 200)
        How many images to read at once before writing time series.
        This number affects how many images are stored in memory and should
        be chosen according to the available amount of memory and the size of
        a single image.
    """

    startdate = pd.to_datetime(startdate).to_pydatetime().date()
    enddate = pd.to_datetime(enddate).to_pydatetime().date()

    if h_steps is None:
        h_steps = (0, 6, 12, 18)

    filetype = parse_filetype(input_root)
    product = parse_product(input_root) if not product else product

    if land_points:
        if product == "era5":
            grid = ERA5_RegularImgLandGrid(
                res_lat=0.25, res_lon=0.25, bbox=bbox)
        elif product == "era5-land":
            grid = ERA5_RegularImgLandGrid(res_lat=0.1, res_lon=0.1, bbox=bbox)
        else:
            raise NotImplementedError(
                product, "Land grid not implemented for product.")
    else:
        if product == "era5":
            grid = ERA_RegularImgGrid(res_lat=0.25, res_lon=0.25, bbox=bbox)
        elif product == "era5-land":
            grid = ERA_RegularImgGrid(res_lat=0.1, res_lon=0.1, bbox=bbox)
        else:
            raise NotImplementedError(product,
                                      "Grid not implemented for product.")

    if filetype == "grib":
        if land_points:
            raise NotImplementedError(
                "Reshuffling land points only implemented for netcdf files")

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
