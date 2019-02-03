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

This conversion can be performed using the ``ecmwf_repurpose`` command line
program. An example would be:

.. code-block:: shell

   ecmwf_repurpose /era_data /timeseries/data 2000-01-01 2001-01-01 swvl1 swvl2

Which would take ERA images stored in ``/era_data`` from January
1st 2000 to January 1st 2001 and store the parameters "swvl1" and "swvl2"
(don't enter parameter IDs here, since they are only stored in grib files,
it is necessary to access variables via their short names, to also allow
time series conversion from netcdf images) as time series in the folder
``/timeseries/data``.

Conversion to time series is performed by the `repurpose package
<https://github.com/TUW-GEO/repurpose>`_ in the background. For custom settings
or other options see the `repurpose documentation
<http://repurpose.readthedocs.io/en/latest/>`_ and the code in
``ecmwf_models.reshuffle``.


**Note**: If a ``RuntimeError: NetCDF: Bad chunk sizes.`` appears during reshuffling,
consider downgrading the netcdf4 C-library via:

.. code-block:: shell

  conda install -c conda-forge libnetcdf==4.3.3.1 --yes