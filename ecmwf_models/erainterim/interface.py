# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2019, TU Wien
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

from ecmwf_models.interface import ERANcImg, ERANcDs, ERAGrbImg, ERAGrbDs
import warnings

'''
This module contains ERA Interim specific child classes of the netcdf and grib
base classes, that are used for reading all ecmwf products.
'''

class ERAIntNcImg(ERANcImg):
    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=False):
        warnings.warn("ERA Interim data is deprecated. Use ERA5 instead.", DeprecationWarning)
        product = 'ERAINT'
        super(ERAIntNcImg, self).__init__(filename=filename,
                                          product=product,
                                          parameter=parameter,
                                          mode=mode,
                                          subgrid=subgrid,
                                          mask_seapoints=mask_seapoints,
                                          array_1D=array_1D)


class ERAIntNcDs(ERANcDs):
    def __init__(self, root_path, parameter=['swvl1', 'swvl2'], subgrid=None,
                 mask_seapoints=False, h_steps=[0, 6, 12, 18], array_1D=False):

        warnings.warn("ERA Interim data is deprecated. Use ERA5 instead.", DeprecationWarning)
        product = 'ERAINT'
        super(ERAIntNcDs, self).__init__(root_path=root_path,
                                         product=product,
                                         parameter=parameter,
                                         subgrid=subgrid,
                                         mask_seapoints=mask_seapoints,
                                         h_steps=h_steps,
                                         array_1D=array_1D)


class ERAIntGrbImg(ERAGrbImg):
    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=False):

        warnings.warn("ERA Interim data is deprecated. Use ERA5 instead.", DeprecationWarning)
        product = 'ERAINT'
        super(ERAIntGrbImg, self).__init__(filename=filename,
                                           product=product,
                                           parameter=parameter,
                                           mode=mode,
                                           subgrid=subgrid,
                                           mask_seapoints=mask_seapoints,
                                           array_1D=array_1D)


class ERAIntGrbDs(ERAGrbDs):
    def __init__(self, root_path, parameter=['swvl1', 'swvl2'], subgrid=None,
                 mask_seapoints=False,  h_steps=[0, 6, 12, 18], array_1D=False):

        warnings.warn("ERA Interim data is deprecated. Use ERA5 instead.", DeprecationWarning)
        product = 'ERAINT'
        super(ERAIntGrbDs, self).__init__(root_path=root_path,
                                          product=product,
                                          parameter=parameter,
                                          subgrid=subgrid,
                                          mask_seapoints=mask_seapoints,
                                          h_steps=h_steps,
                                          array_1D=array_1D)
