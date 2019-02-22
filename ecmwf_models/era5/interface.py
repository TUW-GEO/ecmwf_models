# -*- coding: utf-8 -*-


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

class ERA5NcImg(ImageBase):
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
                 subgrid=None, mask_seapoints=False, array_1D=False):

        super(ERA5NcImg, self).__init__(filename, mode=mode)

        if type(parameter) == str:
            parameter = [parameter]
        if mask_seapoints:
            parameter.append('lsm')

        self.parameter = parameter
        self.mask_seapoints = mask_seapoints
        self.array_1D = array_1D
        self.subgrid = subgrid

    def read(self, timestamp=None):
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

        if self.mask_seapoints and 'lsm' not in dataset.variables.keys():
            raise IOError('No land sea mask parameter (lsm) in passed image for masking.')
        else:
            sea_mask = dataset.variables['lsm'][:]

        for parameter, variable in dataset.variables.items():
            if parameter in self.parameter:
                param_metadata = {}
                param_data = {}
                for attrname in variable.ncattrs():
                    param_metadata.update(
                        {str(attrname): getattr(variable, attrname)})

                param_data = variable[:]
                param_data.set_fill_value(np.nan)
                param_data = param_data.filled()

                if self.mask_seapoints:
                    param_data = np.ma.array(param_data, mask=np.logical_not(sea_mask),
                                             fill_value=np.nan)
                    param_data = param_data.filled()

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



class ERA5NcDs(MultiTemporalImageBase):
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
                 mask_seapoints=False, array_1D=False):

        subpath_templ = ["%Y", "%j"]

        if type(parameter) == str:
            parameter = [parameter]

        ioclass_kws = {'parameter': parameter,
                       'subgrid': subgrid,
                       'array_1D': array_1D,
                       'mask_seapoints': mask_seapoints}

        super(ERA5NcDs, self).__init__(root_path, ERA5NcImg,
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


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    afile = "/data-read/USERS/wpreimes/era5_netcdf_image/1979/002/ERA5_19790102_1200.nc"
    imgf = ERA5NcDs('/data-read/USERS/wpreimes/era5_netcdf_image', mask_seapoints=True)
    img = imgf.read(datetime(1979,1,2))
    plt.imshow(img['swvl1'])
    plt.savefig('test.png')