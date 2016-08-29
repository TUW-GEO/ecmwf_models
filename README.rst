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
data.
