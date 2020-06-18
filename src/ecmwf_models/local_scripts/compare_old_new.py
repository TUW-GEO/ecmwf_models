# -*- coding: utf-8 -*-

'''
Module description
'''
# TODO # (+) 

# NOTES # -

from datetime import datetime
from ecmwf_models.interface import ERATs

old_data_path = '/home/wpreimes/shares/radar/Datapool_processed/ECMWF_reanalysis/ERA5/datasets/netcdf'
new_data_path = "/data-write/USERS/wpreimes/ERA5_TS"
compare_variables = ['swvl1', 'stl1']

#this is the date that the new data must go until
last_date_new = datetime(2019,12,31,18)

# this time frame must be in the old AND in the new data
compare_timeframe = (datetime(1978,1,1), datetime(2018,12,31))
compare_lonlat = [(147.125, -25.625),
                  (44.625, -24.125),
                  (-42.875, -3.125),
                  (	-121.875, 43.125)]

ds_old = ERATs(old_data_path, parameters=compare_variables)
ds_new = ERATs(new_data_path, parameters=compare_variables)

for (lon, lat) in compare_lonlat:
    print(lon,lat)
    ts_old = ds_old.read(lon,lat)
    ts_new = ds_new.read(lon,lat)

    # check the last date in the new data to see if the whole period is covered
    assert ts_new.index[-1] == last_date_new
    for var in compare_variables:
        print(var)
        #compare the selected variables in the selected points over the selected
        # period to the rpevious data.
        assert all(ts_old.loc[compare_timeframe[0]:compare_timeframe[1], var] == \
                   ts_new.loc[compare_timeframe[0]:compare_timeframe[1], var])

        print('--------------------------------------------------------------')