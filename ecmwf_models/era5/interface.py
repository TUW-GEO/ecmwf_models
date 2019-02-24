# -*- coding: utf-8 -*-
from ecmwf_models.interface import ERANcImg, ERANcDs, ERAGrbImg, ERAGrbDs


class ERA5NcImg(ERANcImg):
    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=False):

        product = 'ERA5'
        super(ERA5NcImg, self).__init__(filename, product, parameter, mode,
                                        subgrid, mask_seapoints, array_1D)

class ERA5NcDs(ERANcDs):
    def __init__(self, root_path, parameter=['swvl1', 'swvl2'],
                 subgrid=None, mask_seapoints=False, array_1D=False):

        product = 'ERA5'
        super(ERA5NcDs, self).__init__(root_path, product, parameter,
                                       subgrid, mask_seapoints, array_1D)


class ERA5GrbImg(ERAGrbImg):
    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=False):

        product = 'ERA5'
        super(ERA5GrbImg, self).__init__(filename, product, parameter, mode,
                                        subgrid, mask_seapoints, array_1D)

class ERA5GrbDs(ERAGrbDs):
    def __init__(self, root_path, parameter=['swvl1', 'swvl2'],
                 subgrid=None, mask_seapoints=False, array_1D=False):

        product = 'ERA5'
        super(ERA5GrbDs, self).__init__(root_path, product, parameter,
                                       subgrid, mask_seapoints, array_1D)


if __name__ == '__main__':
    from datetime import datetime
    import matplotlib.pyplot as plt

    afile = "/data-read/USERS/wpreimes/era5_netcdf_image/1979/002/ERA5_19790102_1200.nc"
    imgf = ERA5NcDs('/data-read/USERS/wpreimes/era5_netcdf_image', mask_seapoints=True)
    img = imgf.read(datetime(1979,1,2))
    plt.imshow(img['swvl1'])
    plt.savefig('test.png')