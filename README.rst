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

    conda env create -f environment.yml
    source activate ecmwf_models
    pip install ecmwf_models

This script should work on Linux or OSX and uses the ``environment.yml`` file
included in this repository. On Windows the reading of grib files is not
available at the moment. On Windows a solution would be to download the ECMWF
data in netCDF format instead. We do not yet support that format but would love
pull requests for adding support.


