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

def reshuffle(input_root, outputpath,
              startdate, enddate,
              parameters, land_points=False,
              imgbuffer=50):
    """
    Reshuffle method applied to ERA-Interim data.

    Parameters
    ----------
    input_root: string
        input path where era interim data was downloaded
    outputpath : string
        Output path.
    startdate : datetime
        Start date.
    enddate : datetime
        End date.
    parameters: list
        parameters to read and convert
    landpoints: bool
        reshuffle land points only (not implemented yet)
    imgbuffer: int, optional
        How many images to read at once before writing time series.
    """
    filetype = get_filetype(input_root)
    if filetype == 'grib':
        input_dataset = ERAGrbDs(input_root, parameters, expand_grid=False)
    elif filetype == 'netcdf':
        input_dataset = ERANcDs(input_root, parameters, subgrid=False, array_1D=True)
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
    Parse command line parameters for conversion from image to timeseries

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Convert ERA data into time series format.")
    parser.add_argument("dataset_root",
                        help='Root of local filesystem where the data is stored.')
    parser.add_argument("timeseries_root",
                        help='Root of local filesystem where the timeseries should be stored.')
    parser.add_argument("start", type=mkdate,
                        help=("Startdate. Either in format YYYY-MM-DD or YYYY-MM-DDTHH:MM."))
    parser.add_argument("end", type=mkdate,
                        help=("Enddate. Either in format YYYY-MM-DD or YYYY-MM-DDTHH:MM."))
    parser.add_argument("parameters", metavar="parameters",
                        nargs="+",
                        help=("Short name of paramteres to reshuffle. e.g."
                              "swvl1 swvl2 swvl3 swvl4, for Volumetric soil water layers 1 to 4."
                              "A list of possible parameters is available at http://apps.ecmwf.int/codes/grib/param-db"
                              "or by using the 'View MARS request' option in the web based ordering system."))

    parser.add_argument("--imgbuffer", type=int, default=50,
                        help=("How many images to read at once. Bigger numbers make the "
                              "conversion faster but consume more memory."))
    args = parser.parse_args(args)

    print("Converting data from {} to {} into folder {}.".format(args.start.isoformat(),
                                                                 args.end.isoformat(),
                                                                 args.timeseries_root))
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


