============
ecmwf_models
============


.. image:: https://github.com/TUW-GEO/ecmwf_models/workflows/Automated%20Tests/badge.svg?branch=master
   :target: https://github.com/TUW-GEO/ecmwf_models/actions

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

    conda install -c conda-forge pandas pygrib netcdf4 pyresample xarray

The following command will download and install all the needed pip packages as well
as the ecmwf-model package itself.

.. code::

    pip install ecmwf_models

To create a full development environment with conda, the `yml` files inside
the folder `environment/` in this repository can be used. Both environements
should work. The file `latest` should install the newest version of most
dependencies. The file `pinned` is a fallback option and should always work.

.. code::

    git clone --recursive git@github.com:TUW-GEO/ecmwf_models.git ecmwf_models
    cd ecmwf_models
    conda env create -f environment/latest.yml
    source activate ecmwf_models
    python setup.py develop
    pytest


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
is missing or if you find a bug.
Please take a look at the `developers guide <https://github.com/TUW-GEO/ecmwf_models/blob/master/CONTRIBUTING.rst>`_.
