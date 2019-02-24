# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2018,TU Wien
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
Interface to reading ecmwf reanalysis data.
'''
import warnings
import os

try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")
from pygeobase.io_base import ImageBase, MultiTemporalImageBase
from pygeobase.object_base import Image
import numpy as np
from datetime import timedelta
from ecmwf_models.grid import ERA_RegularImgGrid, get_grid_resolution
from netCDF4 import Dataset
from datetime import datetime


class ERAIntGrbImg(ImageBase):
    """
    Reader for a single ERA Interim grib file.

    Parameters
    ----------
    filename: str
        Path to the image file to read.
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Name of parameters to read from the image file.
    mode: str, optional (default: 'r')
        Mode in which to open the file, changing this can cause data loss.
    subgrid: pygeogrids.CellGrid, optional (default:None)
        Read only data for points of this grid and not global values.
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 expand_grid=True):

        super(ERAIntGrbImg, self).__init__(filename, mode=mode)

        if type(parameter) == str:
            parameter = [parameter]
        self.parameter = parameter
        self.expand_grid = expand_grid

    def read(self, timestamp=None):
        #TODO: Replace ERA5 missing data (!=0)
        grbs = pygrib.open(self.filename)

        img = {}
        metadata = {}
        for message in grbs:
            param_name = message.short_name
            if param_name not in self.parameter: continue
            metadata[param_name] = {}
            message.expand_grid(self.expand_grid)
            img[param_name] = message.values
            lats, lons = message.latlons()
            metadata[param_name]['units'] = message['units']
            metadata[param_name]['long_name'] = message['parameterName']

            if 'levels' in message.keys():
                metadata[param_name]['depth'] = '{:} cm'.format(message['levels'])

        grbs.close()
        lons_gt_180 = np.where(lons > 180.0)
        lons[lons_gt_180] = lons[lons_gt_180] - 360


        return Image(lons, lats, img, metadata, timestamp)

    def write(self, data):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass


class ERAIntNcImg(ImageBase):
    """
    Reader for a single ERA netcdf file.

    Parameters
    ----------
    filename: str
        Path to the image file to read.
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Name of parameters to read from the image file.
    mode: str, optional (default: 'r')
        Mode in which to open the file, changing this can cause data loss.
    subgrid: pygeogrids.CellGrid, optional (default:None)
        Read only data for points of this grid and not global values.
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, array_1D=False):

        super(ERAIntNcImg, self).__init__(filename, mode=mode)

        if type(parameter) == str:
            parameter = [parameter]
        self.parameter = parameter
        self.array_1D = array_1D
        self.subgrid = subgrid

    def read(self, timestamp=None):
        #TODO: Replace ERA5 missing data (!=0)
        return_img = {}
        return_metadata = {}

        try:
            dataset = Dataset(self.filename)
        except IOError as e:
            print(e)
            print(" ".join([self.filename, "can not be opened"]))
            raise e

        res_lat, res_lon = get_grid_resolution(dataset.variables['latitude'][:],
                                               dataset.variables['longitude'][:])

        self.grid = ERA_RegularImgGrid(res_lat, res_lon) if not self.subgrid else self.subgrid

        for parameter, variable in dataset.variables.items():
            if parameter in self.parameter:
                param_metadata = {}
                param_data = {}
                for attrname in variable.ncattrs():
                    param_metadata.update(
                        {str(attrname): getattr(variable, attrname)})

                param_data = variable[:]

                param_data = param_data.flatten()

                return_img.update(
                    {str(parameter): param_data[self.grid.activegpis]})

                return_metadata.update({str(parameter): param_metadata})

                try:
                    return_img[parameter]
                except KeyError:
                    path, thefile = os.path.split(self.filename)
                    print ('%s in %s is corrupt - filling'
                           'image with NaN values' % (parameter, thefile))
                    return_img[parameter] = np.empty(
                        self.grid.n_gpi).fill(np.nan)

                    return_metadata['corrupt_parameters'].append()

        dataset.close()

        if self.array_1D:
            return Image(self.grid.activearrlon, self.grid.activearrlat,
                         return_img, return_metadata, timestamp)
        else:
            for key in return_img:
                nlat = np.unique(self.grid.activearrlat).size
                nlon = np.unique(self.grid.activearrlon).size
                return_img[key] = return_img[key].reshape((nlat, nlon))
            return Image(self.grid.activearrlon.reshape(nlat, nlon),
                         self.grid.activearrlat.reshape(nlat, nlon),
                         return_img,
                         return_metadata,
                         timestamp)

    def write(self, data):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass


class ERAIntGrbDs(MultiTemporalImageBase):
    """
    Parameters
    ----------
    root_path: string
        Root path where the data is stored
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Parameter or list of parameters to read
    expand_grid: bool, optional (default: True)
        If the reduced gaußian grid should be expanded to a full gaußian grid.
    """

    def __init__(self, root_path, parameter=['swvl1', 'swvl2'],
                 expand_grid=True):

        subpath_templ = ["%Y", "%j"]

        if type(parameter) == str:
            parameter = [parameter]

        ioclass_kws = {'parameter': parameter,
                       'expand_grid': expand_grid}

        super(ERAIntGrbDs, self).__init__(root_path, ERAIntGrbImg,
                                       fname_templ='*_{datetime}.grb',
                                       datetime_format="%Y%m%d_%H%M",
                                       subpath_templ=subpath_templ,
                                       exact_templ=False,
                                       ioclass_kws=ioclass_kws)


    def tstamps_for_daterange(self, start_date, end_date):
        """
        Get datetimes in 6H resolution between 2 dates

        Parameters
        ----------
        start_date: datetime
            Start datetime
        end_date: datetime
            End datetime
        """

        img_offsets = np.array([timedelta(hours=0),
                                timedelta(hours=6),
                                timedelta(hours=12),
                                timedelta(hours=18)])

        timestamps = []
        diff = end_date - start_date
        for i in range(diff.days + 1):
            daily_dates = start_date + timedelta(days=i) + img_offsets
            timestamps.extend(daily_dates.tolist())

        return timestamps


class ERAIntNcDs(MultiTemporalImageBase):
    """
    Class for reading ERA 5 images in nc format.

    Parameters
    ----------
    root_path: str
        Root path where image data is stored
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Parameter or list of parameters to read from image files
    subpath_templ: list, optional (default: ["%Y", "%j"])
        List of strings that specifies a sub-path depending on date. If the
        data is e.g. stored in day-of-year files in yearly folders.
    subgrid: pygeogrids.CellGrid, optional (default:None)
        Read only data for points of this grid and not global values.
    array_1D: bool, optional (default:False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(self, root_path, parameter=['swvl1', 'swvl2'], subgrid=None,
                 array_1D=False):

        subpath_templ = ["%Y", "%j"]

        if type(parameter) == str:
            parameter = [parameter]

        ioclass_kws = {'parameter': parameter,
                       'subgrid': subgrid,
                       'array_1D': array_1D}

        super(ERAIntNcDs, self).__init__(root_path, ERAIntNcImg,
                                      fname_templ='*_{datetime}.nc',
                                      datetime_format="%Y%m%d_%H%M",
                                      subpath_templ=subpath_templ,
                                      exact_templ=False,
                                      ioclass_kws=ioclass_kws)

    def tstamps_for_daterange(self, start_date, end_date):
        """
        Get datetimes in 6H resolution between 2 dates

        Parameters
        ----------
        start_date: datetime
            Start datetime
        end_date: datetime
            End datetime
        """

        img_offsets = np.array([timedelta(hours=0),
                                timedelta(hours=6),
                                timedelta(hours=12),
                                timedelta(hours=18)])

        timestamps = []
        diff = end_date - start_date
        for i in range(diff.days + 1):
            daily_dates = start_date + timedelta(days=i) + img_offsets
            timestamps.extend(daily_dates.tolist())

        return timestamps
