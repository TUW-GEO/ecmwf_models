============
ecmwf_models
============

|ci| |cov| |pip| |doc|

.. |ci| image:: https://github.com/TUW-GEO/ecmwf_models/actions/workflows/ci.yml/badge.svg?branch=master
   :target: https://github.com/TUW-GEO/ecmwf_models/actions

.. |cov| image:: https://coveralls.io/repos/TUW-GEO/ecmwf_models/badge.png?branch=master
  :target: https://coveralls.io/r/TUW-GEO/ecmwf_models?branch=master

.. |pip| image:: https://badge.fury.io/py/ecmwf-models.svg
    :target: https://badge.fury.io/py/ecmwf-models

.. |doc| image:: https://readthedocs.org/projects/ecmwf-models/badge/?version=latest
   :target: https://ecmwf-models.readthedocs.io/en/latest/


Readers and converters for ECMWF reanalysis (`ERA5 <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels>`_
and `ERA5-Land <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land>`_) data.
Written in Python.

Works great in combination with `pytesmo <https://github.com/TUW-GEO/pytesmo>`_.


Installation
============

Install required C-libraries via conda. For installation we recommend
`Miniconda <http://conda.pydata.org/miniconda.html>`_:

.. code::

    conda install -c conda-forge pygrib netcdf4 pyresample pykdtree

Afterwards the following command will install all remaining python dependencies
as well as the ``ecmwf_models`` package itself.

.. code::

    pip install ecmwf_models

Quickstart
==========

Download image data from CDS (`set up API <https://cds.climate.copernicus.eu/how-to-api>`_ first) using the ``era5 download`` and ``era5land download``
console command (see ``era5 download --help`` for all options) ...

.. code-block:: shell

    era5land download /tmp/era5/img -s 2024-04-01 -e 2024-04-05 -v swvl1,swvl2 --h_steps 0,12

... and convert them to time series (ideally for a longer period). Check ``era5 reshuffle --help``

.. code-block:: shell

    era5land reshuffle /tmp/era5/img /tmp/era5/ts -s 2024-04-01 -e 2024-04-05 --land_points True

Finally, in python, read the time series data for a location as a pandas
DataFrame.

.. code-block:: python

    >> from ecmwf_models.interface import ERATs
    >> ds = ERATs('/tmp/era5/ts')
    >> ds.read(18, 48)  # (lon, lat)

                            swvl1     swvl2
    2024-04-01 00:00:00  0.318054  0.329590
    2024-04-01 12:00:00  0.310715  0.325958
    2024-04-02 00:00:00  0.360229  0.323502
            ...             ...       ...
    2024-04-04 12:00:00  0.343353  0.348755
    2024-04-05 00:00:00  0.350266  0.346558
    2024-04-05 12:00:00  0.343994  0.344498

More programs are available to keep an exisiting image and time series record
up-to-date. Type ``era5 --help`` and ``era5land --help`` to see all available
programs.

CDS API Setup
=============

In order to download data from CDS, this package uses the CDS API
(https://pypi.org/project/cdsapi/). You can either pass your credentials
directly on the command line (which might be unsafe) or set up a
.cdsapirc file in your home directory (recommended).
Please see the description at https://cds.climate.copernicus.eu/how-to-api.

Supported Products
==================

At the moment this package supports

- **ERA5**
- **ERA5-Land**

reanalysis data in **grib** and **netcdf** format (download, reading, time
series creation) with a default spatial sampling of 0.25 degrees (ERA5),
and 0.1 degrees (ERA5-Land).
It should be easy to extend the package to support other ECMWF reanalysis
products. This will be done as need arises.

Docker image
============

We provide a docker image for this package. This contains all
pre-installed dependencies and can simply be pulled via

.. code-block:: shell

    $ docker pull ghcr.io/tuw-geo/ecmwf_models:latest

Alternatively, to build the image locally using the provided Dockerfile, call
from the package root

.. code-block:: shell

    $ docker buildx build -t ecmwf_models:latest . 2>&1 | tee docker_build.log

Afterwards, you can execute the ``era5`` and ``era5land`` commands directly in
the container (after mounting some volumes to write data to).
The easiest way to set the API credentials in this case is via the
``CDSAPI_KEY`` container variable or the ``--cds_token`` option as below.

.. code-block:: shell

    $ docker run -v /data/era5/img:/container/path ecmwf_models:latest bash -c \
       'era5land update_img /container/path --cds_token xxxx-xxx-xxx-xx-xxxx'

You can use this together with a task scheduler to regularly pull new data.

Citation
========

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.593533.svg
   :target: https://doi.org/10.5281/zenodo.593533

If you use the software in a publication then please cite it using the Zenodo DOI.
Be aware that this badge links to the latest package version.

Contribute
==========

We are happy if you want to contribute. Please raise an issue explaining what
is missing or if you find a bug.
Please take a look at the `developers guide <https://github.com/TUW-GEO/ecmwf_models/blob/master/CONTRIBUTING.rst>`_.
