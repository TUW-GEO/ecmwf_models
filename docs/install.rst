Installation
============

Setup of a complete environment with `conda
<http://conda.pydata.org/miniconda.html>`_ can be performed using the following
commands:

.. code-block:: shell

  conda create -n ecmwf-models python=2.7 # or any other supported python version
  source activate ecmwf-models

.. code-block:: shell

  # Either install required conda packages manually
  conda install -c conda-forge numpy netCDF4 pyproj pygrib xarray
  # Or use the provided environment file to install all dependencies
  conda env update -f environment.yml

.. code-block:: shell

  # Install the ecmwf-models package and pip-dependencies
  pip install ecmwf_models

This will also try to install pygrib for reading the ERA grib files. If this
does not work then please consult the `pygrib manual
<http://jswhit.github.io/pygrib/docs/>`_.

.. note::

   Reading grib files does not work on Windows as far as we know, use the netcdf
   option instead.


Supported Products
==================

At the moment this package supports **ERA Interim** and **ERA5** reanalysis data in
**grib** and **netcdf** format (reading, time series creation) with a default spatial
sampling of 0.75 degrees (ERA Interim) resp. 0.25 degrees (ERA5).
It should be easy to extend the package to support other ERA products.
This will be done as need arises.