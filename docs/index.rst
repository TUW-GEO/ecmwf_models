.. include:: ../README.rst

Downloading data
================

ERA-Interim and ERA5 data can be downloaded manually from the ECMWF servers. It can also
be done automatically using the ECMWF API. To use the ECMWF API you have to be
registered, install the ecmwf-api Python package and setup the ECMWF API Key. A
guide for this is provided by `ECMWF
<https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets>`_.

After that you can use the command line program ``ecmwf_download`` to download
data. For example ``ecmwf_download /path/to/storage 39 40 -s 2000-01-01 -e
2000-02-01 -p ERA-Interim`` would download the parameters 39 and 40 of ERA-Interim in grib1 format on the
default gaussian grid for ERA-Interim into the folder ``/path/to/storage`` between the first of January 2000
and the first of February 2000. The data will be stored in subfolders of the format ``YYYY/jjj``, where YYYY describes the
year and jjj the day of the year for the downloaded files. After the download the data can be
read with the ``ERAGrbDs`` and ``ERANcDs`` class.

Reading data
============

The dataset can be read by datetime using the ``ecmwf_models.ERAGrbDs`` and
``ecmwf_models.ERANcDs`` classes for downloaded data in the according format.

.. code-block:: python

    from ecmwf_models.interface import ERAGrbDs
    root_path = "/path/to/storage"
    ds = ERAGrbDs(root_path, 'swvl1')
    data = ds.read(datetime(2000, 1, 1, 0))
.. code-block:: python

    from ecmwf_models.interface import ERANcDs
    root_path = "/path/to/storage"
    ds = ERANcDs(root_path, ['swvl1', 'swvl2'])
    data = ds.read(datetime(2000, 1, 1, 0))
Multiple parameters can be read by providing a list to ``ERAGrbDs`` and ``ERANcDs``:

All images between two given dates can be read using the
``ERAGrbDs.iter_images`` and ``ERANcDs.iter_images`` method.

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

Reading converted time series data
----------------------------------

For reading the data the ``ecmwf_repurpose`` command produces the class
``ERATs`` can be used:

.. code-block:: python

    from ecmwf_models.interface import ERATs
    ds = ERATs(ts_path)
    # read_ts takes either lon, lat coordinates or a grid point indices.
    # and returns a pandas.DataFrame
    ts = ds.read_ts(45, 15)

Contents
========

.. toctree::
   :maxdepth: 2

   License <license>
   Authors <authors>
   Changelog <changes>
   Module Reference <api/modules>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
