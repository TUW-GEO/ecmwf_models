=========
Changelog
=========

Version 0.X
===========

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
