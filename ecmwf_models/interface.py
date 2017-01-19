# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2016,TU Wien
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
from pygeobase.io_base import ImageBase
from pygeobase.io_base import MultiTemporalImageBase
from pygeobase.object_base import Image
import numpy as np
from datetime import timedelta
from pygeogrids.netcdf import load_grid

from pynetcf.time_series import GriddedNcOrthoMultiTs


class ERAInterimImg(ImageBase):
    """
    Reader for a single ERA Interim grib file.

    Parameters
    ----------
    filename: string
        filename
    mode: string, optional
        mode in which to open the file
    expand_grid: boolean, optional
        If the reduced gaußian grid should be expanded to a full gaußian grid.
    """

    def __init__(self, filename, mode='r', expand_grid=True):
        super(ERAInterimImg, self).__init__(filename, mode=mode)
        self.expand_grid = expand_grid

    def read(self, timestamp=None):

        grbs = pygrib.open(self.filename)
        if grbs.messages != 1:
            grbs.close()
            raise IOError("Wrong number of messages in file")

        metadata = {}
        for message in grbs:
            message.expand_grid(self.expand_grid)
            image = message.values
            lats, lons = message.latlons()
            metadata['units'] = message['units']
            metadata['long_name'] = message['parameterName']

            if 'levels' in message.keys():
                metadata['depth'] = '{:} cm'.format(message['levels'])

            if 'level' in message.keys():
                metadata['depth'] = '{:} cm'.format(message['level'])

        grbs.close()
        lons_gt_180 = np.where(lons > 180.0)
        lons[lons_gt_180] = lons[lons_gt_180] - 360
        return Image(lons, lats, image, metadata, timestamp)

    def write(self, data):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass


class ERAInterimDs(MultiTemporalImageBase):
    """

    Parameters
    ----------
    parameter: string or list
        parameter or list of parameters to read
    root_path: string
        root path where the data is stored
    subpath_templ: list, optional
        list of strings that specifies a subpath depending on date. If the
        data is e.g. in year folders
    expand_grid: boolean, optional
        If the reduced gaußian grid should be expanded to a full gaußian grid.
    """

    def __init__(self, parameter, root_path,
                 subpath_templ=["ei_%Y"], expand_grid=True):
        super(ERAInterimDs, self).__init__(root_path, ERAInterimImg,
                                           subpath_templ=subpath_templ,
                                           ioclass_kws={'expand_grid': expand_grid})
        if type(parameter) == str:
            parameter = [parameter]
        self.parameters = parameter
        self.filename_template = "%s.128_EI_OPER_0001_AN_N128_%s_0.grb"

    def _assemble_img(self, timestamp, **kwargs):

        return_img = {}
        metadata_img = {}
        for parameter in self.parameters:

            custom_templ = self.filename_template % (
                parameter,
                timestamp.strftime('%Y%m%d_%H%M'))
            grb_file = self._build_filename(
                timestamp, custom_templ=custom_templ)

            self._open(grb_file)
            (data, metadata,
             timestamp, lon,
             lat, time) = self.fid.read(timestamp=timestamp,
                                        **kwargs)

            return_img[parameter] = data
            metadata_img[parameter] = metadata

        return Image(lon, lat, return_img, metadata_img, timestamp)

    def tstamps_for_daterange(self, start_date, end_date):
        """
        return timestamps for daterange

        Parameters
        ----------
        start_date: datetime
            start datetime
        end_date: datetime
            end datetime

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


class ERAinterimTs(GriddedNcOrthoMultiTs):

    def __init__(self, ts_path, grid_path=None):

        if grid_path is None:
            grid_path = os.path.join(ts_path, "grid.nc")

        grid = load_grid(grid_path)
        super(ERAinterimTs, self).__init__(ts_path, grid)
