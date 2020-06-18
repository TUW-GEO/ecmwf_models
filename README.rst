============
ecmwf_models
============

.. image:: https://travis-ci.org/TUW-GEO/ecmwf_models.svg?branch=master
    :target: https://travis-ci.org/TUW-GEO/ecmwf_models

.. image:: https://coveralls.io/repos/github/TUW-GEO/ecmwf_models/badge.svg?branch=master
   :target: https://coveralls.io/github/TUW-GEO/ecmwf_models?branch=master

.. image:: https://badge.fury.io/py/ecmwf-models.svg
    :target: https://badge.fury.io/py/ecmwf-models

.. image:: https://readthedocs.org/projects/ecmwf-models/badge/?version=latest
   :target: https://ecmwf-models.readthedocs.io/en/latest/

Readers and converters for data from the `ECMWF reanalysis models
<http://apps.ecmwf.int/datasets/>`_. Written in Python.

Works great in combination with `pytesmo <https://github.com/TUW-GEO/pytesmo>`_.

Citation
========

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.593533.svg
   :target: https://doi.org/10.5281/zenodo.593533

If you use the software in a publication then please cite it using the Zenodo DOI.
Be aware that this badge links to the latest package version.

Please select your specific version at https://doi.org/10.5281/zenodo.593533 to get the DOI of that version.
You should normally always use the DOI for the specific version of your record in citations.
This is to ensure that other researchers can access the exact research artefact you used for reproducibility.

You can find additional information regarding DOI versioning at http://help.zenodo.org/#versioning

Installation
============

Install required C-libraries via conda. For installation we recommend
`Miniconda <http://conda.pydata.org/miniconda.html>`_. So please install it according
to the official installation instructions. As soon as you have the ``conda``
command in your shell you can continue:

.. code::

    conda install -c conda-forge pandas pygrib netcdf4 scipy pyresample xarray

The following command will download and install all the needed pip packages as well
as the ecmwf-model package itself.

.. code::

    pip install ecmwf_models

To create a full development environment with conda, the environment.yml file
in this repository can be used.

.. code::

    git clone git@github.com:TUW-GEO/ecmwf_models.git ecmwf_models
    cd ecmwf_models
    conda create -n ecmwf-models python=3.6 # or any other supported version
    source activate ecmwf-models
    conda env update -f environment.yml
    python setup.py develop

This script should work on Linux or OSX and uses the ``environment.yml`` file
included in this repository.

Supported Products
==================

At the moment this package supports

- **ERA Interim** (deprecated)
- **ERA5**
- **ERA5-Land** 

reanalysis data in **grib** and **netcdf** format (download, reading, time series creation) with a default spatial
sampling of 0.75 degrees (ERA Interim), 0.25 degrees (ERA5), resp. 0.1 degrees (ERA5-Land).
It should be easy to extend the package to support other ECMWF reanalysis products.
This will be done as need arises.

Contribute
==========

We are happy if you want to contribute. Please raise an issue explaining what
is missing or if you find a bug. We will also gladly accept pull requests
against our master branch for new features or bug fixes.

Development setup
-----------------

For Development we also recommend the ``conda`` environment from the
installation part.

Guidelines
----------

If you want to contribute please follow these steps:

- Fork the ecmwf_models repository to your account
- make a new feature branch from the ecmwf_models master branch
- Add your feature
- please include tests for your contributions in one of the test directories
  We use py.test so a simple function called test_my_feature is enough
- submit a pull request to our master branch
