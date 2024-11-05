=========
Changelog
=========

Unreleased changes in master branch
===================================
-

Version 0.10.1
==============
- Option to download spatial subsets added
- Reshuffling when some of the images in a period are missing (larger than imgbuffer) no longer leads to error (`#40 <https://github.com/TUW-GEO/ecmwf_models/issues/40>`_)
- Repurpose to log warnings and errors only (`#40 <https://github.com/TUW-GEO/ecmwf_models/issues/40>`_)

Version 0.10.0
==============
- ERA-Interim support removed
- Package refactored (globals and utils modules added)
- Refactored command line interface (separate ``era5`` and ``era5land`` commands)
- Added functions that allow automatic updates of existing images and time series records
- Added Dockerfile and build image as part of CD pipeline

Version 0.9.2
=============
- Fix issue with too large data requests to download, added command line arg to specify max request size.
- Pin pynetcf>=0.5.0
- Add test for downloading ERA5 data directly from CDS (requires CDS API key)

Version 0.9.1
=============
- Fix returned status code in case of partial data availability.

Version 0.9
===========
- ERA5T images are downloaded and sliced correctly
- Code formatting with yapf

Version 0.8
===========
- Program `era5_download` returns exit code now (PR `#27 <https://github.com/TUW-GEO/ecmwf_models/pull/27>`_);
- Program `era5_reshuffle` can now take a bounding box to reshuffle spatial subsets;
- TravisCI was replaced by Github Actions;
- Pyscaffold 4 is used; contributing guide added; pre-commit added;
- Code formatting with black (line length 79);

Version 0.7
===========
- Update pyscaffold structure
- Drop support for python2
- Travis deploy to pypi

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
