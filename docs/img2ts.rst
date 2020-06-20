Conversion to time series format
================================

For a lot of applications it is favorable to convert the image based format into
a format which is optimized for fast time series retrieval. This is what we
often need for e.g. validation studies. This can be done by stacking the images
into a netCDF file and choosing the correct chunk sizes or a lot of other
methods. We have chosen to do it in the following way:

- Store only the reduced gaußian grid points (for grib data) since that saves space.
- Store the time series in netCDF4 in the Climate and Forecast convention
  `Orthogonal multidimensional array representation
  <http://cfconventions.org/cf-conventions/v1.6.0/cf-conventions.html#_orthogonal_multidimensional_array_representation>`_
- Store the time series in 5x5 degree cells. This means there will be 2566 cell
  files and a file called ``grid.nc`` which contains the information about which
  grid point is stored in which file. This allows us to read a whole 5x5 degree
  area into memory and iterate over the time series quickly.

  .. image:: 5x5_cell_partitioning.png
     :target: _images/5x5_cell_partitioning.png

This conversion can be performed using the ``era5_reshuffle`` (respectively
``eraint_reshuffle``) command line program. An example would be:

.. code-block:: shell

   era5_reshuffle /era_data /timeseries/data 2000-01-01 2001-01-01 swvl1 swvl2

Which would take 6-hourly ERA5 images stored in ``/era_data`` from January
1st 2000 to January 1st 2001 and store the parameters "swvl1" and "swvl2" as time
series in the folder ``/timeseries/data``. If you time series should have a different
resolution than 6H, use the ``h_steps`` flag here accordingly (images to use for time
series generation have to be in the downloaded raw data).
The passed names have to correspond with the names in the downloaded file,
i.e. use the variable short names here.
Other flags, that can be used in ``era5_reshuffle`` are:

- **-h (--help)** : Shows the help text for the reshuffle function
- **--land_points** : Reshuffle and store only data over land points.
- **-h_steps (--as_grib)** : full hours for which images are reshuffled (e.g. --h_steps 0
  would reshuffle only data at 00:00 UTC). By default we use 0, 6, 12 and 18.
- **--imgbuffer** : The number of images that are read into memory before converting
  them into time series. Bigger numbers make the conversion faster but consume more memory.


Conversion to time series is performed by the `repurpose package
<https://github.com/TUW-GEO/repurpose>`_ in the background. For custom settings
or other options see the `repurpose documentation
<http://repurpose.readthedocs.io/en/latest/>`_ and the code in
``ecmwf_models.reshuffle``.
