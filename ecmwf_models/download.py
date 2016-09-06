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
Module for Downloading ECMWF ERA Interim data.
'''

from ecmwfapi import ECMWFDataServer
import argparse
import sys

import pygrib
import os
from datetime import datetime, timedelta


def download_era_interim(start, end, parameters, target, timesteps=[0, 6, 12, 18]):
    """
    Download era interim data

    Parameters
    ----------
    start : date
        start date
    end : date
        end date
    parameters : list
        parameter ids, see wiki
    target : string
        path at which to save the downloaded grib file
    """

    server = ECMWFDataServer()

    param_strings = []
    for parameter in parameters:

        param_strings.append("%d.128" % parameter)

    timestep_strings = []
    for timestep in timesteps:
        timestep_strings.append("%02d" % timestep)

    param_string = '/'.join(param_strings)
    timestep_string = '/'.join(timestep_strings)
    date_string = "%s/to/%s" % (start.strftime("%Y%m%d"),
                                end.strftime("%Y%m%d"))

    server.retrieve({
        'dataset': "interim",
        'step': "0",
        'number': "all",
        'levtype': "sl",
        'date': date_string,
        'time': timestep_string,
        # "139.128/141.128/167.128/170.128/183.128/235.128/236.128/39.128/40.128/41.128/42.128",
        'param': param_string,
        'target': target
    })


def save_gribs_from_grib(input_grib, output_path,
                         subpaths_year=False, subpaths_template="ei_%Y"):
    """
    takes one grib file with several parameters and saves
    each message as a separate grib file

    Parameters
    ----------
    input_grib : string
        filepath of the input grib file
    output_path : string
        where to save the resulting grib files
    subpaths_year : boolean, optional
        if true the files are saved in subpaths by year
        Default False
    subpaths_template : string, optional
        template of the folder name for each year

    """
    grib_in = pygrib.open(input_grib)

    grib_in.seek(0)
    for grb in grib_in:
        param_id = grb['marsParam']
        N = grb['N']
        filedate = datetime(grb['year'], grb['month'], grb['day'],
                            grb['hour'], grb['minute'], grb['second'])

        current_out_path = output_path
        if subpaths_year:
            current_out_path = os.path.join(
                current_out_path, filedate.strftime(subpaths_template))
            if not os.path.exists(current_out_path):
                os.mkdir(current_out_path)

        step = grb['startStep']

        new_filename = "%s_EI_OPER_0001_AN_N%d_%s_%d.grb" % (
            param_id, N, filedate.strftime("%Y%m%d_%H%M"), step)
        grb_out = open(os.path.join(current_out_path, new_filename), 'wb')
        grb_out.write(grb.tostring())
        grb_out.close()
    grib_in.close()


def download_and_move(parameters, startdate, enddate,
                      target_path, timesteps=[0, 6, 12, 18]):
    """
    Downloads the data from the ECMWF servers and moves them to the target path.
    This is done in 30 day increments between start and end date to be efficient with the MARS system.
    See the recommendation for doing it this way in
    https://software.ecmwf.int/wiki/display/WEBAPI/ERA-Interim+daily+retrieval+efficiency

    The files are then extracted into separate grib files per parameter and stored
    in yearly folders under the target_path.

    Parameters
    ----------
    parameters : list
        parameter ids
    startdate: datetime
        first date to download
    enddate: datetime
        last date to download
    target_path: string
        path to which to copy the extracted parameter grib files
    timesteps: list, optional
        list of timesteps to download
    """
    td = timedelta(days=30)
    current_start = startdate
    while current_start <= enddate:
        current_end = current_start + td
        if current_end >= enddate:
            current_end = enddate

        fname = current_start.strftime("%Y%m%d_")
        fname = current_end.strftime(fname + "%Y%m%d.grb")
        downloaded_grib = os.path.join(target_path, fname)
        download_era_interim(current_start, current_end, parameters,
                             downloaded_grib, timesteps=timesteps)
        save_gribs_from_grib(downloaded_grib, target_path, subpaths_year=True)
        os.remove(downloaded_grib)

        current_start = current_end + timedelta(days=1)


def mkdate(datestring):
    if len(datestring) == 10:
        return datetime.strptime(datestring, '%Y-%m-%d')
    if len(datestring) == 16:
        return datetime.strptime(datestring, '%Y-%m-%dT%H:%M')


def parse_args(args):
    """
    Parse command line parameters for recursive download

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Convert ERA Interim data into time series format.")
    parser.add_argument("localroot",
                        help='Root of local filesystem where the data is stored.')
    parser.add_argument("parameters", metavar="parameters", type=int,
                        nargs="+",
                        help=("Parameters to convert in numerical format. e.g."
                              "39 40 41 42 for Volumetric soil water layers 1 to 4."
                              "A list of possible parameters is available at http://apps.ecmwf.int/codes/grib/param-db "
                              "or by using the 'View MARS request' option in the web based ordering system."))
    parser.add_argument("-s", "--start", type=mkdate,
                        help=("Startdate. Either in format YYYY-MM-DD or YYYY-MM-DDTHH:MM."
                              "If no data is found there then the first available date of the product is used."))
    parser.add_argument("-e", "--end", type=mkdate,
                        help=("Enddate. Either in format YYYY-MM-DD or YYYY-MM-DDTHH:MM."
                              "If not given then the current date is used."))
    args = parser.parse_args(args)
    # set defaults that can not be handled by argparse

    if args.start is None or args.end is None:
        if args.start is None:
            args.start = datetime(1979, 1, 1)
        if args.end is None:
            args.end = datetime.now()

    print("Downloading data from {} to {} into folder {}.".format(args.start.isoformat(),
                                                                  args.end.isoformat(),
                                                                  args.localroot))
    return args


def main(args):
    args = parse_args(args)

    download_and_move(
        args.parameters, args.start, args.end, args.localroot)


def run():
    main(sys.argv[1:])

if __name__ == '__main__':
    run()
