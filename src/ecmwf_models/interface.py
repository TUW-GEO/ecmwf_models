# The MIT License (MIT)
#
# Copyright (c) 2019, TU Wien, Department of Geodesy and Geoinformation
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

import warnings
import os
from pygeobase.io_base import ImageBase, MultiTemporalImageBase
from pygeobase.object_base import Image
import numpy as np
from datetime import timedelta

from pygeogrids.netcdf import load_grid
from pynetcf.time_series import GriddedNcOrthoMultiTs
from ecmwf_models.grid import (
    ERA_RegularImgGrid,
    get_grid_resolution,
    ERA_IrregularImgGrid,
)
from ecmwf_models.utils import lookup
import glob

import xarray as xr

try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")
"""
Base classes for reading downloaded ERA netcdf and grib images and stacks
"""


class ERANcImg(ImageBase):
    """
    Reader for a single ERA netcdf file.

    Parameters
    ----------
    filename: str
        Path to the image file to read.
    product : str
        'era5' or 'era5-land' or 'eraint'
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Name of parameters to read from the image file.
    subgrid: pygeogrids.CellGrid, optional (default: None)
        Read only data for points of this grid and not global values.
    mask_seapoints : bool, optional (default: False)
        Read the land-sea mask to mask points over water and set them to nan.
        This option needs the 'lsm' parameter to be in the file!
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    mode : str, optional (default: 'r')
        Mode in which to open the file, changing this can cause data loss.
        This argument should not be changed!

    """

    def __init__(
        self,
        filename,
        product,
        parameter=["swvl1", "swvl2"],
        subgrid=None,
        mask_seapoints=False,
        array_1D=False,
        mode="r",
    ):

        super(ERANcImg, self).__init__(filename, mode=mode)

        if type(parameter) == str:
            parameter = [parameter]

        # look up short names
        self.parameter = lookup(product, parameter)["short_name"].values

        self.mask_seapoints = mask_seapoints
        self.array_1D = array_1D
        self.subgrid = subgrid

        if self.subgrid and not self.array_1D:
            warnings.warn(
                "Reading spatial subsets as 2D arrays ony works if there "
                "is an equal number of points in each line")

    def read(self, timestamp=None):
        """
        Read data from the loaded image file.

        Parameters
        ---------
        timestamp : datetime, optional (default: None)
            Specific date (time) to read the data for.
        """
        return_img = {}
        return_metadata = {}

        try:
            dataset = xr.open_dataset(
                self.filename, engine="netcdf4", mask_and_scale=True)
        except IOError as e:
            print(e)
            print(" ".join([self.filename, "can not be opened"]))
            raise e

        res_lat, res_lon = get_grid_resolution(
            dataset.variables["latitude"][:],
            dataset.variables["longitude"][:])

        grid = (
            ERA_RegularImgGrid(res_lat, res_lon)
            if not self.subgrid else self.subgrid)

        if self.mask_seapoints:
            if "lsm" not in dataset.variables.keys():
                raise IOError("No land sea mask parameter (lsm) in"
                              " passed image for masking.")
            else:
                sea_mask = dataset.variables["lsm"].values

        for name in dataset.variables:
            if name in self.parameter:
                variable = dataset[name]

                if 'expver' in variable.dims and (variable.data.ndim == 3):
                    warnings.warn(
                        f"Found experimental data in {self.filename}")
                    param_data = variable.data[-1]
                    for vers_data in variable.data:
                        if not np.all(np.isnan(vers_data)):
                            param_data = vers_data
                else:
                    param_data = variable.data

                if self.mask_seapoints:
                    param_data = np.ma.array(
                        param_data,
                        mask=np.logical_not(sea_mask),
                        fill_value=np.nan,
                    )
                    param_data = param_data.filled()

                param_data = param_data.flatten()

                return_metadata[name] = variable.attrs
                return_img.update(
                    dict([(str(name), param_data[grid.activegpis])]))

                try:
                    return_img[name]
                except KeyError:
                    path, thefile = os.path.split(self.filename)
                    warnings.warn(
                        "Cannot load variable {var} from file {thefile}. "
                        "Filling image with NaNs.".format(
                            var=name, thefile=thefile))
                    return_img[name] = np.empty(grid.activegpis.size).fill(
                        np.nan)

        dataset.close()

        if self.array_1D:
            return Image(
                grid.activearrlon,
                grid.activearrlat,
                return_img,
                return_metadata,
                timestamp,
            )
        else:
            nlat = np.unique(grid.activearrlat).size
            nlon = np.unique(grid.activearrlon).size

            for key in return_img:
                return_img[key] = return_img[key].reshape((nlat, nlon))

            return Image(
                grid.activearrlon.reshape(nlat, nlon),
                grid.activearrlat.reshape(nlat, nlon),
                return_img,
                return_metadata,
                timestamp,
            )

    def write(self, data):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass


class ERANcDs(MultiTemporalImageBase):
    """
    Class for reading ERA 5 images in nc format.

    Parameters
    ----------
    root_path: str
        Root path where image data is stored.
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Parameter or list of parameters to read from image files.
    subgrid: pygeogrids.CellGrid, optional (default: None)
        Read only data for points of this grid and not global values.
    mask_seapoints : bool, optional (default: False)
        Use the land-sea-mask parameter in the file to mask points over water.
    h_steps : list, optional (default: [0,6,12,18])
        List of full hours for which images exist.
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(
            self,
            root_path,
            product,
            parameter=("swvl1", "swvl2"),
            subgrid=None,
            mask_seapoints=False,
            h_steps=(0, 6, 12, 18),
            array_1D=False,
    ):

        self.h_steps = h_steps
        subpath_templ = ["%Y", "%j"]

        if type(parameter) == str:
            parameter = [parameter]

        ioclass_kws = {
            'product': product,
            'parameter': parameter,
            'subgrid': subgrid,
            'mask_seapoints': mask_seapoints,
            'array_1D': array_1D
        }

        # the goal is to use expERA5*.nc if necessary, but perfer ERA5*.nc
        self.fn_templ_priority = [
            'ERA5_*_{datetime}.nc', 'expERA5_*_{datetime}.nc'
        ]

        super(ERANcDs, self).__init__(
            root_path,
            ERANcImg,
            fname_templ='*_{datetime}.nc',
            datetime_format="%Y%m%d_%H%M",
            subpath_templ=subpath_templ,
            exact_templ=False,
            ioclass_kws=ioclass_kws)

    def _search_files(self,
                      timestamp,
                      custom_templ=None,
                      str_param=None,
                      custom_datetime_format=None):
        """
        override the original filename generation to allow multiple files for
        time stamp
        """
        if custom_templ is not None:
            raise NotImplementedError
        else:
            fname_templ = self.fname_templ

        if custom_datetime_format is not None:
            dFormat = {self.dtime_placeholder: custom_datetime_format}

        else:
            dFormat = {self.dtime_placeholder: self.datetime_format}

        sub_path = ''
        if self.subpath_templ is not None:
            for s in self.subpath_templ:
                sub_path = os.path.join(sub_path, timestamp.strftime(s))

        fname_templ = fname_templ.format(**dFormat)

        if str_param is not None:
            fname_templ = fname_templ.format(**str_param)

        search_file = os.path.join(self.path, sub_path,
                                   timestamp.strftime(fname_templ))

        if self.exact_templ:
            raise NotImplementedError
        else:
            filename = glob.glob(search_file)
            if len(filename) > 1:
                for templ in self.fn_templ_priority:
                    fname_templ = templ.format(**dFormat)
                    if str_param is not None:
                        fname_templ = fname_templ.format(**str_param)
                    search_file = os.path.join(self.path, sub_path,
                                               timestamp.strftime(fname_templ))
                    filename = glob.glob(search_file)
                    if len(filename) == 1:
                        break

        if not filename:
            filename = []

        return filename

    def tstamps_for_daterange(self, start_date, end_date):
        """
        Get datetimes in the correct sub-daily resolution between 2 dates

        Parameters
        ----------
        start_date: datetime
            Start datetime
        end_date: datetime
            End datetime

        Returns
        ----------
        timestamps : list
            List of datetimes
        """

        img_offsets = np.array([timedelta(hours=h) for h in self.h_steps])

        timestamps = []
        diff = end_date - start_date
        for i in range(diff.days + 1):
            daily_dates = start_date + timedelta(days=i) + img_offsets
            timestamps.extend(daily_dates.tolist())

        return timestamps


class ERAGrbImg(ImageBase):
    """
    Base class for reader for a single ERA Grib file.

    Parameters
    ----------
    filename: str
        Path to the image file to read.
    product : str
        ERA5 or ERAINT
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Name of parameters to read from the image file.
    subgrid: pygeogrids.CellGrid, optional (default:None)
        Read only data for points of this grid and not global values.
    mask_seapoints : bool, optional (default: False)
        Read the land-sea mask to mask points over water and set them to nan.
        This option needs the 'lsm' parameter to be in the file!
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    mode : str, optional (default: 'r')
        Mode in which to open the file, changing this can cause data loss.
        This argument should not be changed!
    """

    def __init__(
        self,
        filename,
        product,
        parameter=("swvl1", "swvl2"),
        subgrid=None,
        mask_seapoints=False,
        array_1D=True,
        mode="r",
    ):

        super(ERAGrbImg, self).__init__(filename, mode=mode)

        if type(parameter) == str:
            parameter = [parameter]

        self.parameter = lookup(
            product, parameter)["short_name"].values  # look up short names
        self.product = product

        self.mask_seapoints = mask_seapoints
        self.array_1D = array_1D
        self.subgrid = subgrid

    def read(self, timestamp=None):
        """
        Read data from the loaded image file.

        Parameters
        ---------
        timestamp : datetime, optional (default: None)
            Specific date (time) to read the data for.
        """
        grbs = pygrib.open(self.filename)

        grid = self.subgrid

        return_img = {}
        return_metadata = {}

        var_msg_lut = {p: None for p in self.parameter}
        sea_mask = None
        for N in range(grbs.messages):
            n = N + 1
            message = grbs.message(n)
            param_name = str(message.cfVarNameECMF)

            if param_name == "lsm":
                if self.mask_seapoints and sea_mask is None:
                    sea_mask = message.values.flatten()

            if param_name not in self.parameter:
                continue
            else:
                var_msg_lut[param_name] = n

        # available variables
        shape = None
        for param_name, n in var_msg_lut.items():
            if n is None:
                continue

            return_metadata[param_name] = {}

            message = grbs.message(n)

            param_data = message.values.flatten()
            if not shape:
                shape = param_data.shape
            return_img[param_name] = param_data

            if grid is None:
                lats, lons = message.latlons()
                try:
                    res_lat, res_lon = get_grid_resolution(lats, lons)
                    grid = ERA_RegularImgGrid(res_lat, res_lon)
                except ValueError:  # when grid not regular
                    lons_gt_180 = np.where(lons > 180.0)
                    lons[lons_gt_180] = lons[lons_gt_180] - 360
                    grid = ERA_IrregularImgGrid(lons, lats)

            return_metadata[param_name]["units"] = message["units"]
            return_metadata[param_name]["long_name"] = \
                message["parameterName"]

            if "levels" in message.keys():
                return_metadata[param_name]["depth"] = "{:} cm".format(
                    message["levels"])

        if self.mask_seapoints:
            if sea_mask is None:
                raise IOError(
                    "No land sea mask parameter (lsm) in passed image"
                    " for masking.")
            else:
                # mask the loaded data
                for name in return_img.keys():
                    param_data = return_img[name]
                    param_data = np.ma.array(
                        param_data,
                        mask=np.logical_not(sea_mask),
                        fill_value=np.nan,
                    )
                    param_data = param_data.filled()
                    return_img[name] = param_data

        grbs.close()

        # missing variables
        for param_name, n in var_msg_lut.items():
            if n is not None:
                continue
            param_data = np.full(shape, np.nan)
            warnings.warn("Cannot load variable {var} from file {thefile}. "
                          "Filling image with NaNs.".format(
                              var=param_name, thefile=self.filename))
            return_img[param_name] = param_data
            return_metadata[param_name] = {}
            return_metadata[param_name]["long_name"] = lookup(
                self.product, [param_name]).iloc[0]["long_name"]

        if self.array_1D:
            return Image(
                grid.activearrlon,
                grid.activearrlat,
                return_img,
                return_metadata,
                timestamp,
            )
        else:
            nlat = np.unique(grid.activearrlat).size
            nlon = np.unique(grid.activearrlon).size

            for key in return_img:
                return_img[key] = return_img[key].reshape((nlat, nlon))

            return Image(
                grid.activearrlon.reshape(nlat, nlon),
                grid.activearrlat.reshape(nlat, nlon),
                return_img,
                return_metadata,
                timestamp,
            )

    def write(self, data):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass


class ERAGrbDs(MultiTemporalImageBase):
    """
    Reader for a stack of ERA grib files.

    Parameters
    ----------
    root_path: string
        Root path where the data is stored
    product : str
        ERA5 or ERAINT
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Parameter or list of parameters to read
    expand_grid: bool, optional (default: True)
        If the reduced gaussian grid should be expanded to a full
        gaussian grid.
    """

    def __init__(
            self,
            root_path,
            product,
            parameter=("swvl1", "swvl2"),
            subgrid=None,
            mask_seapoints=False,
            h_steps=(0, 6, 12, 18),
            array_1D=True,
    ):

        self.h_steps = h_steps

        subpath_templ = ["%Y", "%j"]

        if type(parameter) == str:
            parameter = [parameter]

        ioclass_kws = {
            "product": product,
            "parameter": parameter,
            "subgrid": subgrid,
            "mask_seapoints": mask_seapoints,
            "array_1D": array_1D,
        }

        super(ERAGrbDs, self).__init__(
            root_path,
            ERAGrbImg,
            fname_templ="*_{datetime}.grb",
            datetime_format="%Y%m%d_%H%M",
            subpath_templ=subpath_templ,
            exact_templ=False,
            ioclass_kws=ioclass_kws,
        )

    def tstamps_for_daterange(self, start_date, end_date):
        """
        Get datetimes in the correct sub-daily resolution between 2 dates

        Parameters
        ----------
        start_date: datetime
            Start datetime
        end_date: datetime
            End datetime

        Returns
        ----------
        timestamps : list
            List of datetimes
        """
        img_offsets = np.array([timedelta(hours=h) for h in self.h_steps])

        timestamps = []
        diff = end_date - start_date
        for i in range(diff.days + 1):
            daily_dates = start_date + timedelta(days=i) + img_offsets
            timestamps.extend(daily_dates.tolist())

        return timestamps


class ERATs(GriddedNcOrthoMultiTs):
    """
    Time series reader for all reshuffled ERA reanalysis products in time
    series format.
    Use the read_ts(lon, lat) resp. read_ts(gpi) function of this class
    to read data for locations!

    Parameters
    ----------
    ts_path : str
        Directory where the netcdf time series files are stored
    grid_path : str, optional (default: None)
        Path to grid file, that is used to organize the location of time
        series to read. If None is passed, grid.nc is searched for in the
        ts_path.

    Optional keyword arguments that are passed to the Gridded Base when used
    ------------------------------------------------------------------------
        parameters : list, optional (default: None)
            Specific variable names to read, if None are selected,
            all are read.
        offsets : dict, optional (default: None)
            Offsets (values) that are added to the parameters (keys)
        scale_factors : dict, optional (default: None)
            Offset (value) that the parameters (key) is multiplied with
        ioclass_kws: dict, (optional)

        Optional keyword arguments, passed to the OrthoMultiTs class when used
        ----------------------------------------------------------------------
            read_bulk : boolean, optional (default: False)
                If set to True, the data of all locations is read into memory,
                and subsequent calls to read_ts then read from cache and
                not from disk. This makes reading complete files faster.
            read_dates : boolean, optional (default: False)
                If false, dates will not be read automatically but only on
                specific request useable for bulk reading because currently
                the netCDF num2date routine is very slow for big datasets.
    """

    def __init__(self, ts_path, grid_path=None, **kwargs):

        if grid_path is None:
            grid_path = os.path.join(ts_path, "grid.nc")

        grid = load_grid(grid_path)
        super(ERATs, self).__init__(ts_path, grid, **kwargs)
