# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2016, TU Wien
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

'''
Module for a command line interface to convert the ERA Interim data into a
time series format using the repurpose package
'''

import os
import sys
import argparse
import numpy as np

from pygeogrids import BasicGrid

from repurpose.img2ts import Img2Ts
from ecmwf_models.interface import ERAGrbDs, ERANcDs
from ecmwf_models.download import mkdate


def get_filetype(inpath):
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

    if '.nc' in filelist and '.grb' not in filelist:
        return 'netcdf'
    elif '.grb' in filelist and '.nc' not in filelist:
        return 'grib'
    else:
        # if file type cannot be detected, guess grib
        return 'grib'

def reshuffle(input_root, outputpath, startdate, enddate, parameters,
              land_points=False, imgbuffer=50):
    """
    Reshuffle method applied to ERA images for conversion into netcdf time
    series format.

    Parameters
    ----------
    input_root: str
        Input path where ERA image data was downloaded to.
    outputpath : str
        Output path, where the reshuffled netcdf time series are stored.
    startdate : datetime
        Start date, from which images are read and time series are generated.
    enddate : datetime
        End date, from which images are read and time series are generated.
    parameters: list or str
        Variables to read from the passed images and convert into time series format.
    landpoints: bool, optional (default: False)
        Reshuffle land points only (not implemented yet)
    imgbuffer: int, optional (default: 50)
        How many images to read at once before writing time series. This number
        affects how many images are stored in memory and should be chosen according
        to the available amount of memory and the size of a single image.
    """

    if land_points:
        raise NotImplementedError

    filetype = get_filetype(input_root)

    if filetype == 'grib':
        input_dataset = ERAGrbDs(input_root, parameters, expand_grid=False)
    elif filetype == 'netcdf':
        input_dataset = ERANcDs(input_root, parameters, subgrid=None, array_1D=True)
    else:
        raise Exception('Unknown file format')

    if not os.path.exists(outputpath):
        os.makedirs(outputpath)

    global_attr = {'product': 'ECMWF Reanalysis from {}'.format(filetype)}

    # get time series attributes from first day of data.
    data = input_dataset.read(startdate)
    ts_attributes = data.metadata

    grid = BasicGrid(data.lon, data.lat)

    reshuffler = Img2Ts(input_dataset=input_dataset, outputpath=outputpath,
                        startdate=startdate, enddate=enddate, input_grid=grid,
                        imgbuffer=imgbuffer, cellsize_lat=5.0, cellsize_lon=5.0,
                        ts_dtypes=np.dtype('float32'), global_attr=global_attr,
                        zlib=True, unlim_chunksize=1000, ts_attributes=ts_attributes)
    reshuffler.calc()


def parse_args(args):
    """
    Parse command line parameters for conversion from image to time series.

    Parameters
    ----------
    args: list
        command line parameters as list of strings

    Returns
    ----------
    args : argparse.Namespace
        Parsed command line parameters
    """

    parser = argparse.ArgumentParser(
        description="Convert downloaded ERA image data into time series format.")
    parser.add_argument("dataset_root",
                        help='Root of local filesystem where the image data is stored.')
    parser.add_argument("timeseries_root",
                        help='Root of local filesystem where the time series should be stored.')
    parser.add_argument("start", type=mkdate,
                        help=("Startdate in format YYYY-MM-DD"))
    parser.add_argument("end", type=mkdate,
                        help=("Enddate in format YYYY-MM-DD"))
    parser.add_argument("variables", metavar="variables",
                        nargs="+",
                        help=("Short name of variables as stored in the images, which are reshuffled. "
                              "See documentation on image download for resp. ERA products, "
                              "for more information on variable names of the product. "))
    parser.add_argument("--imgbuffer", type=int, default=50,
                        help=("How many images to read at once. Bigger numbers make the "
                              "conversion faster but consume more memory. Choose this according to your "
                              "system and the size of a single image."))
    args = parser.parse_args(args)

    print("Converting data from {} to {} into {}."
          .format(args.start.isoformat(), args.end.isoformat(), args.timeseries_root))

    return args


def main(args):
    args = parse_args(args)

    reshuffle(args.dataset_root,
              args.timeseries_root,
              args.start,
              args.end,
              args.parameters,
              imgbuffer=args.imgbuffer)


def run():
    main(sys.argv[1:])

if __name__ == '__main__':
    run()


