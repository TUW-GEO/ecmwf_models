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
from pygeobase.object_base import Image


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
