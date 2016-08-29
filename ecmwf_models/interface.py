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

try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")
from pygeobase.io_base import ImageBase
from pygeobase.io_base import MultiTemporalImageBase
from pygeobase.object_base import Image
import numpy as np
from datetime import timedelta


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

        for message in grbs:
            message.expand_grid(self.expand_grid)
            image = message.values
            lons, lats = message.latlons()

        grbs.close()
        return Image(lons, lats, image, {}, timestamp)

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

        return Image(lon, lat, return_img, None, timestamp)

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
