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
"""
Base classes for reading downloaded ERA netcdf and grib images and stacks
"""
import warnings
import os
import glob
from datetime import timedelta, datetime  # noqa: F401
import numpy as np
import xarray as xr

from pygeobase.io_base import ImageBase, MultiTemporalImageBase
from pygeobase.object_base import Image
from pynetcf.time_series import GriddedNcOrthoMultiTs
from pygeogrids.grids import BasicGrid, gridfromdims
from pygeogrids.netcdf import load_grid

from ecmwf_models.grid import trafo_lon
from ecmwf_models.utils import lookup
from ecmwf_models.globals import (
    IMG_FNAME_TEMPLATE,
    IMG_FNAME_DATETIME_FORMAT,
    SUPPORTED_PRODUCTS,
    SUBDIRS,
)
from ecmwf_models.globals import (pygrib, pygrib_available,
                                  PygribNotFoundError)


class ERANcImg(ImageBase):
    """
    Reader for a single ERA netcdf file. The main purpose of this class is
    to use it in the time series conversion routine. To read downloaded image
    files, we recommend using xarray (https://docs.xarray.dev/en/stable/).

    Parameters
    ----------
    filename: str
        Path to the image file to read.
    product : str
        'era5' or 'era5-land'
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Name of parameters to read from the image file.
    subgrid: ERA_RegularImgGrid or ERA_RegularImgLandGrid or None, optional
        Read only data for points of this grid.
        If None is passed, we read all points from the file.
        The main purpose of this parameter is when reshuffling to time series,
        to include only e.g. points over land.
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
        parameter=None,
        subgrid=None,
        mask_seapoints=False,
        array_1D=False,
        mode='r',
    ):

        super(ERANcImg, self).__init__(filename, mode=mode)

        if parameter is not None:
            # look up short names
            self.parameter = lookup(
                product, np.atleast_1d(parameter))["short_name"].values
        else:
            self.parameter = None

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

        try:
            dataset = xr.open_dataset(
                self.filename, engine="netcdf4", mask_and_scale=True)
        except IOError as e:
            print(" ".join([self.filename, "can not be opened"]))
            raise e

        if self.parameter is None:
            self.parameter = list(dataset.data_vars)

        if self.mask_seapoints:
            if "lsm" not in dataset.variables.keys():
                raise IOError("No land sea mask parameter (lsm) in"
                              " passed image for masking.")
            else:
                sea_mask = dataset.variables["lsm"].values
        else:
            sea_mask = None

        return_img = {}
        return_metadata = {}

        grid = gridfromdims(
            trafo_lon(dataset['longitude'].values),
            dataset['latitude'].values,
            origin='top')

        if self.subgrid is not None:
            gpis = grid.find_nearest_gpi(self.subgrid.activearrlon,
                                         self.subgrid.activearrlat)[0]
        else:
            gpis = None

        for name in self.parameter:
            try:
                variable = dataset[name]
            except KeyError:
                path, f = os.path.split(self.filename)
                warnings.warn(f"Cannot load variable {name} from file {f}. "
                              f"Filling image with NaNs.")
                dat = np.full(
                    grid.shape if gpis is None else len(gpis), np.nan)
                return_img[name] = dat
                continue

            if 'expver' in variable.dims and (variable.data.ndim == 3):
                warnings.warn(f"Found experimental data in {self.filename}")
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

            if gpis is not None:
                param_data = param_data[gpis]

            return_metadata[name] = variable.attrs
            return_img[name] = param_data

        dataset.close()

        if self.subgrid is None:
            self.subgrid = grid

        if self.array_1D:
            return Image(
                self.subgrid.activearrlon,
                self.subgrid.activearrlat,
                return_img,
                return_metadata,
                timestamp,
            )
        else:
            if len(self.subgrid.shape) != 2:
                raise ValueError("Passed subgrid does not have a 2d shape."
                                 "Did you mean to read data as 1d arrays?")

            for key in return_img:
                return_img[key] = return_img[key].reshape(self.subgrid.shape)

            return Image(
                self.subgrid.activearrlon.reshape(self.subgrid.shape),
                self.subgrid.activearrlat.reshape(self.subgrid.shape),
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
    Reader to extract individual images from a multi-image netcdf dataset.
    The main purpose of this class is to use it in the time series conversion
    routine. To read downloaded image files, we recommend using
    xarray (https://docs.xarray.dev/en/stable/).

    Parameters
    ----------
    root_path: str
        Root path where image data is stored.
    product: str
        ERA5 or ERA5-LAND
    parameter: list[str] or str, optional (default: None)
        Parameter or list of parameters to read. None reads all available
        Parameters.
    subgrid: ERA_RegularImgGrid or ERA_RegularImgLandGrid, optional
        Read only data for points of this grid.
        If None is passed, we read all points from the file.
        The main purpose of this parameter is when reshuffling to time series,
        to include only e.g. points over land.
    mask_seapoints: bool, optional (default: False)
        All points that are not over land are replaced with NaN values.
        This requires that the land sea mask (lsm) parameter is included
        in the image files!
    h_steps: tuple, optional (default: (0, 6, 12, 18))
        Time stamps available for each day. Numbers refer to full hours.
    array_1D: bool, optional (default: True)
        Read data as 1d arrays. This is required when the passed subgrid
        is 1-dimensional (e.g. when only landpoints are read). Otherwise
        when a 2d (subgrid) is used, this switch means that the extracted
        image data is also 2-dimensional (lon, lat).
    """

    def __init__(
            self,
            root_path,
            product,
            parameter=None,
            subgrid=None,
            mask_seapoints=False,
            h_steps=(0, 6, 12, 18),
            array_1D=False,
    ):

        self.h_steps = h_steps

        if parameter is not None:
            # look up short names
            self.parameter = lookup(
                product, np.atleast_1d(parameter))["short_name"].values
        else:
            self.parameter = None

        ioclass_kws = {
            'product': product,
            'parameter': parameter,
            'subgrid': subgrid,
            'mask_seapoints': mask_seapoints,
            'array_1D': array_1D
        }

        # the goal is to use ERA5-T*.nc if necessary, but prefer ERA5*.nc
        self.fn_templ_priority = [
            IMG_FNAME_TEMPLATE.format(
                product=(p + ext).upper(),
                type='*',
                datetime="{datetime}",
                ext='nc') for ext in ['', '-T'] for p in SUPPORTED_PRODUCTS
        ]

        super(ERANcDs, self).__init__(
            root_path,
            ERANcImg,
            fname_templ=IMG_FNAME_TEMPLATE.format(
                product='*', type='*', datetime='{datetime}', ext='nc'),
            datetime_format=IMG_FNAME_DATETIME_FORMAT,
            subpath_templ=SUBDIRS,
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

    def __init__(self,
                 filename,
                 product,
                 parameter=None,
                 subgrid=None,
                 mask_seapoints=False,
                 array_1D=True,
                 mode='r'):
        """
        Reader for a single ERA grib file. The main purpose of this class is
        to use it in the time series conversion routine. To read downloaded image
        files, we recommend using xarray (https://docs.xarray.dev/en/stable/).

        Parameters
        ----------
        filename: str
            Path to the image file to read.
        product : str
            ERA5 or ERA5-LAND
        parameter: list or str, optional
            Name of parameters to read from the image file. None means all
            available data variables.
        subgrid: ERA_RegularImgGrid or ERA_RegularImgLandGrid, optional (default: None)
            Read only data for points of this grid.
            If None is passed, we read all points from the file.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and set them to nan.
            This option needs the 'lsm' parameter to be in the file!
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        mode : str, optional (default: 'r')
            Mode in which to open the file, changing this can cause data loss.
            This argument should not be changed!
        """
        super(ERAGrbImg, self).__init__(filename, mode=mode)

        if parameter is None:
            self.parameter = None
        else:
            # look up short names
            self.parameter = lookup(
                product, np.atleast_1d(parameter))["short_name"].values

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
        if not pygrib_available:
            raise PygribNotFoundError()
        grbs = pygrib.open(self.filename)

        return_img = {}
        return_metadata = {}

        grid = None

        for n in range(1, grbs.messages + 1):
            message = grbs.message(n)
            try:
                param_name = str(message.cfVarNameECMF)  # old field?
            except RuntimeError:
                param_name = str(message.shortName)

            if self.mask_seapoints and (param_name == "lsm"):
                pass
            elif self.parameter is None:
                pass
            elif param_name in self.parameter:
                pass
            else:
                continue

            return_metadata[param_name] = {}

            message = grbs.message(n)
            lats, lons = message.latlons()
            param_data = message.values

            if grid is None:
                grid = BasicGrid(
                    trafo_lon(lons).flatten(),
                    lats.flatten(),
                    shape=param_data.shape)

            param_data = param_data.flatten()

            if self.subgrid is not None:
                gpis = grid.find_nearest_gpi(self.subgrid.activearrlon,
                                             self.subgrid.activearrlat)[0]

                param_data = param_data[gpis]

            return_img[param_name] = param_data

            return_metadata[param_name]["units"] = message["units"]
            return_metadata[param_name]["long_name"] = \
                message["parameterName"]

            if "levels" in message.keys():
                return_metadata[param_name]["depth"] = "{:} cm".format(
                    message["levels"])

        grbs.close()

        # Set data for non-land points to NaN
        if self.mask_seapoints:
            if 'lsm' not in return_img:
                raise IOError(
                    "No land sea mask parameter (lsm) in passed image"
                    " for masking.")
            else:
                # mask the loaded data
                mask = np.logical_not(return_img['lsm'].flatten())
                for name in return_img.keys():
                    param_data = return_img[name]
                    param_data = np.ma.array(
                        param_data,
                        mask=mask,
                        fill_value=np.nan,
                    )
                    param_data = param_data.filled()
                    return_img[name] = param_data

            if (self.parameter is not None) and ('lsm' not in self.parameter):
                return_img.pop('lsm')
                return_metadata.pop('lsm')

        if self.subgrid is None:
            self.subgrid = grid

        # Add empty arrays for missing variables
        if self.parameter is not None:
            for p in self.parameter:
                if p not in return_img:
                    param_data = np.full(np.prod(self.subgrid.shape), np.nan)
                    warnings.warn(
                        f"Cannot load variable {param_name} from file "
                        f"{self.filename}. Filling image with NaNs.")
                    return_img[param_name] = param_data
                    return_metadata[param_name] = {}
                    return_metadata[param_name]["long_name"] = lookup(
                        self.product, [param_name]).iloc[0]["long_name"]

        if self.array_1D:
            return Image(
                self.subgrid.activearrlon,
                self.subgrid.activearrlat,
                return_img,
                return_metadata,
                timestamp,
            )
        else:
            if len(self.subgrid.shape) != 2:
                raise ValueError("Passed subgrid does not have a 2d shape."
                                 "Did you mean to read data as 1d arrays?")

            for key in return_img:
                return_img[key] = return_img[key].reshape(self.subgrid.shape)

            return Image(
                self.subgrid.activearrlon.reshape(self.subgrid.shape),
                self.subgrid.activearrlat.reshape(self.subgrid.shape),
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

    def __init__(
            self,
            root_path,
            product,
            parameter=None,
            subgrid=None,
            mask_seapoints=False,
            h_steps=(0, 6, 12, 18),
            array_1D=True,
    ):
        """
        Reader to extract individual images from a multi-image grib dataset.
        The main purpose of this class is to use it in the time series conversion
        routine. To read downloaded image files, we recommend using
        xarray (https://docs.xarray.dev/en/stable/).

        Parameters
        ----------
        root_path: str
            Root path where the downloaded image data is stored in grib format.
            We assume that image files are organized in subfolders by year,
            with each year containing subfolders for individual days of the
            year.
        product : str
            ERA5 or ERA5-Land
        parameter: list[str] or str, optional (default: None)
            Parameter or list of parameters to read. None reads all available
            Parameters.
        subgrid: ERA_RegularImgGrid or ERA_RegularImgLandGrid, optional
            Read only data for points of this grid.
            If None is passed, we read all points from the file.
        mask_seapoints: bool, optional (default: False)
            All points that are not over land are replaced with NaN values.
            This requires that the land sea mask (lsm) parameter is included
            in the image files!
        h_steps: tuple, optional (default: (0, 6, 12, 18))
            Time stamps available for each day. Numbers refer to full hours.
        array_1D: bool, optional (default: True)
            Read data as 1d arrays. This is required when the passed subgrid
            is 1-dimensional (e.g. when only landpoints are read). Otherwise
            when a 2d (subgrid) is used, this switch means that the extracted
            image data is also 2-dimensional (lon, lat).
        """
        self.h_steps = h_steps

        ioclass_kws = {
            "product": product,
            "parameter": parameter,
            "subgrid": subgrid,
            "mask_seapoints": mask_seapoints,
            "array_1D": array_1D,
        }

        fname_templ = IMG_FNAME_TEMPLATE.format(
            product="*", type="*", datetime="{datetime}", ext="grb")

        super(ERAGrbDs, self).__init__(
            root_path,
            ERAGrbImg,
            fname_templ=fname_templ,
            datetime_format=IMG_FNAME_DATETIME_FORMAT,
            subpath_templ=SUBDIRS,
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
            List of datetime values (between start and end date) for all
            required time stamps.
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
    series format (pynetcf OrthoMultiTs format)
    Use the read_ts(lon, lat) resp. read_ts(gpi) function of this class
    to read data for a location!
    """

    def __init__(self, ts_path, grid_path=None, **kwargs):
        """
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
        if grid_path is None:
            grid_path = os.path.join(ts_path, "grid.nc")
        grid = load_grid(grid_path)

        super(ERATs, self).__init__(ts_path, grid, **kwargs)
