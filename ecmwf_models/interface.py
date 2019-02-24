# -*- coding: utf-8 -*-

import warnings
import os
from pygeobase.io_base import ImageBase, MultiTemporalImageBase
from pygeobase.object_base import Image
import numpy as np
from datetime import timedelta
from ecmwf_models.grid import ERA_RegularImgGrid, get_grid_resolution, ERA_IrregularImgGrid
from datetime import datetime
from ecmwf_models.utils import lookup
import xarray as xr
try:
    import pygrib
except ImportError:
    warnings.warn("pygrib has not been imported")

'''
Base classes for reading downloaded ERA netcdf and grib images and 6H image stacks
'''

class ERANcImg(ImageBase):
    """
    Reader for a single ERA netcdf file.

    Parameters
    ----------
    filename: str
        Path to the image file to read.
    product : str
        ERA5 or ERAINT
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Name of parameters to read from the image file.
    mode: str, optional (default: 'r')
        Mode in which to open the file, changing this can cause data loss.
    subgrid: pygeogrids.CellGrid, optional (default:None)
        Read only data for points of this grid and not global values.
    mask_seapoints : bool, optional (default: False)
        Read the land-sea mask to mask points over water and set them to nan.
        This option needs the 'lsm' parameter to be in the file!
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(self, filename, product, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=False):

        super(ERANcImg, self).__init__(filename, mode=mode)

        if type(parameter) == str:
            parameter = [parameter]

        self.parameter = lookup(product, parameter)['short_name'].values # look up short names

        self.mask_seapoints = mask_seapoints
        self.array_1D = array_1D
        self.subgrid = subgrid

    def read(self, timestamp=None):
        '''
        Read data from the loaded image file.

        Parameters
        ---------
        timestamp : datetime, optional (default: None)
            Specific date (time) to read the data for.
        '''
        return_img = {}
        return_metadata = {}

        try:
            dataset = xr.open_dataset(self.filename, engine='netcdf4',
                                      mask_and_scale=True)
        except IOError as e:
            print(e)
            print(" ".join([self.filename, "can not be opened"]))
            raise e

        res_lat, res_lon = get_grid_resolution(dataset.variables['latitude'][:],
                                               dataset.variables['longitude'][:])

        grid = ERA_RegularImgGrid(res_lat, res_lon) if not self.subgrid else self.subgrid

        if self.mask_seapoints and 'lsm' not in dataset.variables.keys():
            raise IOError('No land sea mask parameter (lsm) in passed image for masking.')
        else:
            sea_mask = dataset.variables['lsm'].values

        for name in dataset.variables:
            if name in self.parameter:
                variable = dataset[name]

                param_data = variable.data

                if self.mask_seapoints:
                    param_data = np.ma.array(param_data, mask=np.logical_not(sea_mask),
                                             fill_value=np.nan)
                    param_data = param_data.filled()

                param_data = param_data.flatten()

                return_metadata[name] = variable.attrs
                return_img.update(dict([(str(name), param_data[grid.activegpis])]))

                try:
                    return_img[name]
                except KeyError:
                    path, thefile = os.path.split(self.filename)
                    warnings.warn('Cannot load variable {var} from file {thefile}. '
                                  'Filling image with NaNs.'.format(var=name, thefile=thefile))
                    return_img[name] = np.empty(grid.activegpis.size).fill(np.nan)

        dataset.close()

        if self.array_1D:
            return Image(grid.activearrlon, grid.activearrlat,
                         return_img, return_metadata, timestamp)
        else:
            nlat = np.unique(grid.activearrlat).size
            nlon = np.unique(grid.activearrlon).size

            for key in return_img:
                return_img[key] = return_img[key].reshape((nlat, nlon))

            return Image(grid.activearrlon.reshape(nlat, nlon),
                         grid.activearrlat.reshape(nlat, nlon),
                         return_img,
                         return_metadata,
                         timestamp)

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
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(self, root_path, product, parameter=['swvl1', 'swvl2'],
                 subgrid=None, mask_seapoints=False, array_1D=False):

        subpath_templ = ["%Y", "%j"]

        if type(parameter) == str:
            parameter = [parameter]

        ioclass_kws = {'product': product,
                       'parameter': parameter,
                       'subgrid': subgrid,
                       'mask_seapoints': mask_seapoints,
                       'array_1D': array_1D}

        super(ERANcDs, self).__init__(root_path, ERANcImg,
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
    mode: str, optional (default: 'r')
        Mode in which to open the file, changing this can cause data loss.
    subgrid: pygeogrids.CellGrid, optional (default:None)
        Read only data for points of this grid and not global values.
    mask_seapoints : bool, optional (default: False)
        Read the land-sea mask to mask points over water and set them to nan.
        This option needs the 'lsm' parameter to be in the file!
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(self, filename, product, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=True):

        super(ERAGrbImg, self).__init__(filename, mode=mode)

        if type(parameter) == str:
            parameter = [parameter]

        self.parameter = lookup(product, parameter)['short_name'].values # look up short names

        self.mask_seapoints = mask_seapoints
        self.array_1D = array_1D
        self.subgrid = subgrid


    def read(self, timestamp=None):
        '''
        Read data from the loaded image file.

        Parameters
        ---------
        timestamp : datetime, optional (default: None)
            Specific date (time) to read the data for.
        '''
        grbs = pygrib.open(self.filename)

        grid = self.subgrid

        return_img = {}
        return_metadata = {}

        sea_mask = None

        for message in grbs:
            param_name = message.short_name

            if param_name == 'lsm':
                if self.mask_seapoints and sea_mask is None:
                    sea_mask = message.values.flatten()

            param_name = message.short_name
            if param_name not in self.parameter: continue

            return_metadata[param_name] = {}
            param_data = message.values.flatten()


            return_img[param_name] = param_data

            if grid is None:
                lats, lons = message.latlons()
                try:
                    res_lat, res_lon = get_grid_resolution(lats, lons)
                    grid = ERA_RegularImgGrid(res_lat, res_lon)
                except ValueError: # when grid not regular
                    lons_gt_180 = np.where(lons > 180.0)
                    lons[lons_gt_180] = lons[lons_gt_180] - 360
                    grid = ERA_IrregularImgGrid(lons, lats)

            return_metadata[param_name]['units'] = message['units']
            return_metadata[param_name]['long_name'] = message['parameterName']

            if 'levels' in message.keys():
                return_metadata[param_name]['depth'] = '{:} cm'.format(message['levels'])

        if self.mask_seapoints:
            if sea_mask is None:
                raise IOError('No land sea mask parameter (lsm) in passed image for masking.')
            else:
                #mask the loaded data
                for name in return_img.keys():
                    param_data = return_img[name]
                    param_data = np.ma.array(param_data, mask=np.logical_not(sea_mask),
                                             fill_value=np.nan)
                    param_data = param_data.filled()
                    return_img[name] = param_data

        grbs.close()


        if self.array_1D:
            return Image(grid.activearrlon, grid.activearrlat,
                         return_img, return_metadata, timestamp)

        else:
            nlat = np.unique(grid.activearrlat).size
            nlon = np.unique(grid.activearrlon).size

            for key in return_img:
                return_img[key] = return_img[key].reshape((nlat, nlon))

            return Image(grid.activearrlon.reshape(nlat, nlon),
                         grid.activearrlat.reshape(nlat, nlon),
                         return_img,
                         return_metadata,
                         timestamp)


    def write(self, data):
        raise NotImplementedError()

    def flush(self):
        pass

    def close(self):
        pass


class ERAGrbDs(MultiTemporalImageBase):
    """
    Parameters
    ----------
    root_path: string
        Root path where the data is stored
    product : str
        ERA5 or ERAINT
    parameter: list or str, optional (default: ['swvl1', 'swvl2'])
        Parameter or list of parameters to read
    expand_grid: bool, optional (default: True)
        If the reduced gaußian grid should be expanded to a full gaußian grid.
    """

    def __init__(self, root_path, product, parameter=['swvl1', 'swvl2'],
                 subgrid=None, mask_seapoints=False, array_1D=True):

        subpath_templ = ["%Y", "%j"]

        if type(parameter) == str:
            parameter = [parameter]

        ioclass_kws = {'product': product,
                       'parameter': parameter,
                       'subgrid': subgrid,
                       'mask_seapoints': mask_seapoints,
                       'array_1D': array_1D}

        super(ERAGrbDs, self).__init__(root_path, ERAGrbImg,
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
