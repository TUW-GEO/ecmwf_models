# -*- coding: utf-8 -*-


'''
Module description
'''
# TODO # (+)

# NOTES # -

import matplotlib.pyplot as plt
from ecmwf_models.interface import ERATs
import os
from datetime import datetime
from ecmwf_models.era5.interface import ERA5NcDs
import pandas as pd
from ecmwf_models.grid import ERA_RegularImgGrid
import cartopy
import cartopy.crs as ccrs

from local_scripts.cp_map import cp_map


NEG_VALUES = False
BREAKS = True
VARS = 'sm'
if VARS == 'sm':
    IMAGE_OUT = r"C:\Temp\era5_breaks"
elif VARS == 'tmp':
    IMAGE_OUT = r"C:\Temp\era5_breaks"


IMAGE_IN = r"R:\Datapool_raw\ECMWF_reanalysis\ERA5\datasets\images_core_vars"

#######negative values in ERA5 ############################
if NEG_VALUES:
    image_stamp = datetime(2017, 8, 16, 6, 0)
    grid = ERA_RegularImgGrid()

    parameters = ['swvl1', 'swvl2', 'swvl3', 'swvl4']
    ds = ERA5NcDs(IMAGE_IN, parameter=parameters, array_1D=True)
    img = ds.read(timestamp=image_stamp)

    df = pd.DataFrame(index=list(range(img.lat.size)), data={'lon': img.lon,
                                                             'lat': img.lat})
    for var in parameters:
        df[var] = img.data[var]


    df = df.set_index(['lat', 'lon']).sort_index()

    f, imax, im = cp_map(df=df, col='swvl1', grid=None, projection=ccrs.PlateCarree(), llc=(-20., 20.),
           urc=(10., 40.), extend=(-0.02,0), cmap=plt.get_cmap('hot'), coastline_size='110m',
           flip_ud=False, veg_mask=None, title='Negative Values in ERA5 SWVL1 (2017-08-16 06:00 UTC)',
           gridspace=(10,5), grid_loc='0011', ocean=True, land=True, cbar_location='bottom',
           cbar_label='SWVL1', cbar_kwargs={'shrink': 0.5})


    f.save_fig(os.path.join(IMAGE_OUT, 'negative_sm.png'))

#######Time Series Breaks ############################
if BREAKS:
    if VARS == 'sm':
        parameters = ['swvl1', 'swvl2', 'swvl3','swvl4']
    elif VARS == 'tmp':
        parameters = ['stl1', 'stl2', 'stl3','stl4']



    path = r"D:\data-read\ERA5\timeseries\netcdf"
    ds = ERATs(path, ioclass_kws={'read_bulk':True})

    lonlats = [(58,40),(144.625, -25.625),
               (-4.35, 25.),
               (18.375, 13.375),
               (-10., 25.), (4., 33.), (6.,14.), (15,22), (59,31) , (89,40)]



    for (lon, lat) in lonlats:
        print(lon, lat)
        ts = ds.read(lon, lat)

        sm = ts.loc[:, parameters]

        fig, ax = plt.subplots(1,1)
        fig.set_size_inches(13., 5.)
        sm.plot(marker='.', linestyle='None', title='Lon: {}, Lat: {}'.format(lon, lat), ax=ax)

        plt.tight_layout()
        plt.savefig(os.path.join(IMAGE_OUT, '{}_{}LON_{}LAT.png'.format(VARS,lon, lat)), transparent=True)
        plt.close('all')