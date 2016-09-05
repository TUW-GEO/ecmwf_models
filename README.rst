============
ecmwf_models
============

.. image:: https://travis-ci.org/TUW-GEO/ecmwf_models.svg?branch=master
    :target: https://travis-ci.org/TUW-GEO/ecmwf_models

.. image:: https://coveralls.io/repos/github/TUW-GEO/ecmwf_models/badge.svg?branch=master
   :target: https://coveralls.io/github/TUW-GEO/ecmwf_models?branch=master

.. image:: https://badge.fury.io/py/ecmwf_models.svg
    :target: http://badge.fury.io/py/ecmwf_models

.. image:: https://zenodo.org/badge/12761/TUW-GEO/ecmwf_models.svg
   :target: https://zenodo.org/badge/latestdoi/12761/TUW-GEO/ecmwf_models

Readers and converters for data from the `ECMWF reanalysis models
<http://apps.ecmwf.int/datasets/>`_. Written in Python.

Works great in combination with `pytesmo <https://github.com/TUW-GEO/pytesmo>`_.

Description
===========

A small package for downloading ECMWF reanalysis data and converting it into a
time series format supported by `pytesmo <https://github.com/TUW-GEO/pytesmo>`_.

Documentation
=============

|Documentation Status|

.. |Documentation Status| image:: https://readthedocs.org/projects/ecmwf_models/badge/?version=latest
   :target: http://ecmwf_models.readthedocs.org/

Supported Products
==================

This version supports the following products:

- ERA-Interim

Installation
============

For installation we recommend `Miniconda
<http://conda.pydata.org/miniconda.html>`_. So please install it according to
the official installation instructions. As soon as you have the ``conda``
command in your shell you can continue.

The following script will download and install all the needed packages.

.. code::

    conda create -q -n ecmwf_models -c conda-forge python=2 pygrib
    source activate ecmwf_models
    pip install ecmwf_models

This script should work on Linux or OSX. On Windows the reading of grib files is
not available at the moment. On Windows a solution would be to download the
ECMWF data in netCDF format instead. We do not yet support that format but would
love pull requests for adding support.

Downloading data
================

ERA-Interim data can be downloaded manually from the ECMWF servers. It can also
be done automatically using the ECMWF API. To use the ECMWF API you have to be
registered, install the ecmwf-api Python package and setup the ECMWF API Key. A
guide for this is provided by `ECMWF
<https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets>`_.

After that you can use the command line program ``ecmwf_download`` to download
data. For example ``ecmwf_download /path/to/storage 39 40 -s 2000-01-01 -e
2000-02-01`` would download the parameters 39 and 40 into the folder
``/path/to/storage`` between the first of January 2000 and the first of February
2000 The data will be stored in yearly subfolders of the format ``ei_YYYY``.
After the download the data can be read with the ``ecmwf_models.ERAInterimDs``
class.

Reading data
============

The dataset can be read by datetime using the ``ecmwf_models.ERAInterimDs``.

.. code-block:: python

    from ecmwf_models import ERAInterimDs
    root_path = "/path/to/storage"
    ds = ERAInterimDs('39', root_path)
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['39'].shape == (256, 512)
    assert data.lon.shape == (256, 512)
    assert data.lat.shape == (256, 512)

Multiple parameters can be read by providing a list to ``ERAInterimDs``:

.. code-block:: python

    from ecmwf_models import ERAInterimDs
    root_path = "/path/to/storage"
    ds = ERAInterimDs(['39', '40'], root_path)
    data = ds.read(datetime(2000, 1, 1, 0))
    assert data.data['39'].shape == (256, 512)
    assert data.data['40'].shape == (256, 512)

All images between two given dates can be read using the
``ERAInterimDs.iter_images`` method.

Conversion to time series format
================================

For a lot of applications it is favorable to convert the image based format into
a format which is optimized for fast time series retrieval. This is what we
often need for e.g. validation studies. This can be done by stacking the images
into a netCDF file and choosing the correct chunk sizes or a lot of other
methods. We have chosen to do it in the following way:

- Store only the reduced gaußian grid points since that saves space.
- Store the time series in netCDF4 in the Climate and Forecast convention
  `Orthogonal multidimensional array representation
  <http://cfconventions.org/cf-conventions/v1.6.0/cf-conventions.html#_orthogonal_multidimensional_array_representation>`_
- Store the time series in 5x5 degree cells. This means there will be 2566 cell
  files and a file called ``grid.nc`` which contains the information about which
  grid point is stored in which file. This allows us to read a whole 5x5 degree
  area into memory and iterate over the time series quickly.

  .. image:: docs/5x5_cell_partitioning.png

This conversion can be performed using the ``ecmwf_repurpose`` command line
program. An example would be:

.. code-block:: shell

   ecmwf_repurpose /era_interim_data /timeseries/data 2000-01-01 2001-01-01 39 40

Which would take ERA Interim data stored in ``/era_interim_data`` from January
1st 2000 to January 1st 2001 and store the parameters 39 and 40 as time series
in the folder ``/timeseries/data``.

Conversion to time series is performed by the `repurpose package
<https://github.com/TUW-GEO/repurpose>`_ in the background. For custom settings
or other options see the `repurpose documentation
<http://repurpose.readthedocs.io/en/latest/>`_ and the code in
``ecmwf_models.reshuffle``.

Reading converted time series data
----------------------------------

For reading the data the ``ecmwf_repurpose`` command produces the class
``ERAInterimTs`` can be used:

.. code-block:: python

    from ecmwf_models.interface import ERAinterimTs
    ds = ERAinterimTs(ts_path)
    # read_ts takes either lon, lat coordinates or a grid point indices.
    # and returns a pandas.DataFrame
    ts = ds.read_ts(45, 15)

