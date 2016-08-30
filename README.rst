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
