# -*- coding: utf-8 -*-

"""
Module description
"""
# TODO:
#   (+) 
#---------
# NOTES:
#   -

from ecmwf_models.interface import ERATs

path_all_nc = "/data-write/USERS/wpreimes/shahn_test/ts/from_nc"
path_land_nc = "/data-write/USERS/wpreimes/shahn_test/ts/from_nc_land"
path_all_grb = "/data-write/USERS/wpreimes/shahn_test/ts/from_grb"

lon, lat =  2.125, 46.875

ds_nc_all =  ERATs(path_all_nc)
ds_nc_land = ERATs(path_land_nc)
ds_grb_all = ERATs(path_all_grb)

ts_nc_all = ds_nc_all.read(lon, lat)['skt']
ts_grb_all = ds_grb_all.read(lon, lat)['skt']
ts_nc_land = ds_nc_land.read(lon, lat)['skt']

