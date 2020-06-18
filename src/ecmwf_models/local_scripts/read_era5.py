# -*- coding: utf-8 -*-

'''
Module description
'''
# TODO # (+) 

# NOTES # -

from ecmwf_models.era5.interface import ERA5GrbImg, ERA5GrbDs, ERA5NcImg
from ecmwf_models.interface import ERATs
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


path_img_grb = "/data-write/USERS/wpreimes/shahn_test/img/grb/"
path_img_nc = "/data-write/USERS/wpreimes/shahn_test/img/nc/"
path_ts_grb = "/data-write/USERS/wpreimes/shahn_test/ts/from_grb"
path_ts_nc = "/data-write/USERS/wpreimes/shahn_test/ts/from_nc"


ds_grb = ERATs(path_ts_grb)
ds_nc = ERATs(path_ts_nc)
lon, lat =  2.125, 46.875
year, doy = '2007', '001'

ts_grb = ds_grb.read(lon,lat)
ts_nc = ds_nc.read(lon,lat)

for var, vlim in {'skt':(220,330), 'swvl1':(0,1), 'stl1':(220,330), 'lai_hv':(0,7), 'lai_lv':(0,5), 'sd':(0,10),
                  'slt':(0,7), 't2m':(220,330), 'tcsw':(0,20), 'tp':(0,0.01)}.items():

    v = pd.concat([ts_nc[[var]].rename(columns={var: '{}_nc'.format(var)}),
                    ts_grb[[var]].rename(columns={var: '{}_grb'.format(var)})], axis=1)

    figsm = v.plot(title='Location: ({},{})'.format(lon, lat))
    plt.savefig('/data-write/USERS/wpreimes/shahn_test/ts/plots/{}_compare.png'.format(var))
    plt.close('all')

    img = ERA5GrbImg(filename=os.path.join(path_img_grb, year, doy, 'ERA5_AN_20070101_0600.grb'),
                     parameter=[var], array_1D=False)
    data = img.read()
    fig, (ax0, ax1, ax2) = plt.subplots(nrows=3)
    im = ax0.imshow(data.data[var], vmin=vlim[0], vmax=vlim[1])
    fig.colorbar(im, ax=ax0)
    plotpath = '/data-write/USERS/wpreimes/shahn_test/img/plots/{}_{}'.format(year, doy)
    if not os.path.exists(plotpath):
        os.mkdir(plotpath)

    img2 = ERA5NcImg(filename=os.path.join(path_img_nc, year, doy, 'ERA5_AN_20070101_0600.nc'),
                     parameter=[var], array_1D=False)
    data2 = img2.read()

    im2 = ax1.imshow(data2.data[var], vmin=vlim[0], vmax=vlim[1])


    fig.colorbar(im2, ax=ax1)

    d = data.data[var]-data2.data[var]
    dmin = np.nanmin(d)
    dmax = np.nanmax(d)
    print(var)
    print(dmin)
    print(dmax)
    im3 = ax2.imshow(d, vmin=dmin, vmax=dmax)
    fig.colorbar(im3, ax=ax2)


    fig.suptitle('Top: .grb, Middle: .nc, Bottom: Diff, Year: {}, DOY: {}'.format(year, doy))
    plt.savefig(os.path.join(plotpath, '{}_img.png'.format(var)), dpi=200)
    plt.close('all')


