#!/usr/bin/env bash

in_path='/data-read/USERS/wpreimes/ERA5_images'
out_path='/data-write/USERS/wpreimes/ERA5_ts'

era5_reshuffle $in_path $out_path 2000-01-01 2000-01-02 evaporation land_sea_mask potential_evaporation snow_density snow_depth soil_temperature_level_1 soil_temperature_level_2 soil_temperature_level_3 soil_temperature_level_4 soil_type total_precipitation volumetric_soil_water_layer_1 volumetric_soil_water_layer_2 volumetric_soil_water_layer_3 volumetric_soil_water_layer_4 --mask_seapoints True --imgbuffer 800
