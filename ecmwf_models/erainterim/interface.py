# -*- coding: utf-8 -*-
from ecmwf_models.interface import ERANcImg, ERANcDs, ERAGrbImg, ERAGrbDs


class ERAIntNcImg(ERANcImg):
    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=False):

        product = 'ERAINT'
        super(ERAIntNcImg, self).__init__(filename, product, parameter, mode,
                                        subgrid, mask_seapoints, array_1D)

class ERAIntNcDs(ERANcDs):
    def __init__(self, root_path, parameter=['swvl1', 'swvl2'], subgrid=None,
                 mask_seapoints=False, h_steps=[0,6,12,18], array_1D=False):

        product = 'ERAINT'
        super(ERAIntNcDs, self).__init__(root_path, product, parameter,
                                       subgrid, mask_seapoints, h_steps, array_1D)


class ERAIntGrbImg(ERAGrbImg):
    def __init__(self, filename, parameter=['swvl1', 'swvl2'], mode='r',
                 subgrid=None, mask_seapoints=False, array_1D=False):

        product = 'ERAINT'
        super(ERAIntGrbImg, self).__init__(filename, product, parameter, mode,
                                        subgrid, mask_seapoints, array_1D)

class ERAIntGrbDs(ERAGrbDs):
    def __init__(self, root_path, parameter=['swvl1', 'swvl2'],
                 subgrid=None, mask_seapoints=False,  h_steps=[0,6,12,18],
                 array_1D=False):

        product = 'ERAINT'
        super(ERAIntGrbDs, self).__init__(root_path, product, parameter,
                                       subgrid, mask_seapoints, array_1D)



if __name__ == '__main__':
    from datetime import datetime
    path = '/data-write/USERS/wpreimes/eraint/images'
    ds = ERAIntNcDs(path, parameter=['ssrd', 'lsm'], array_1D=False, h_steps=[3, 15])

    img = ds.read(timestamp=datetime(2013,1,1,3))
    for img in ds.iter_images(datetime(2013,1,1), datetime(2013,1,31)):
        img.data
