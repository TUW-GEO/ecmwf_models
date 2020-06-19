=========
Changelog
=========

Unreleased
==========
-

Version 0.7
===========

- Update pyscaffold structure
- Drop support for python2
- Travis deoploy to pypi

Version 0.6.1
=============

- Fix bug when creating 0.1 deg grid cells (floating point precision)
- Missing variables in grib files are now replaced by empty images.
- Read variable names from grib files from cfVarNameECMF instead of short_name field

Version 0.6
===========

- Add support for downloading, reading, reshuffling era5-land
- Add support for reading, reshuffling points over land only (era5 and era5-land)
- Add function to create land definition files
- Test with pinned environments

Version 0.5
===========

- Change default time steps to 6 hours.
- Add more tests, also for download functions
- Update documentation, add installation script
- Fix bugs, update command line interfaces, update dependencies
- Separate download programs for ERA5 and ERA Interim
- Change the ERA5 download api to use cdsapi instead of ecmwf api
- Update package structure to better separate between the ERA products
- Add look-up-table file for more flexibility in variable names passed by user
- Update readme

Version 0.4
===========

- Add ERA5 support (download, reading, TS conversion)
- Add netcdf support for ERA5 and ERA-Interim download (regular grid)
- Add new grid defintions: netcdf download in regular grid, grib in gaussian grid
- Add Download with spatial resampling (grib and nc) 
- Update GRIB message storing (per day instead of per message)
- Add tests for splitting downloaded files, ERA5 reading, ERA5 reshuffling, generated grids
- Add new test data

Version 0.3
===========

- Fix help text in ecmwf_repurpose command line program.
- Fix reading of metadata for variables that do not have 'levels'
- Fix wrong import when trying to read the reformatted time series data.

Version 0.2
===========

- Add reading of basic metadata fields name, depth and units.
- Fix reading of latitudes and longitudes - where flipped before.
- Fix longitude range to -180, 180.
- Add conversion to time series format.

Version 0.1
===========

- First version
- Add ERA Interim support for downloading and reading.
