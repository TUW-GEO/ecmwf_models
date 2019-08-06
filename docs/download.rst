Downloading ERA5 Data
==========================

ERA5 (and ERA5-Land) data can be downloaded manually from the `Copernicus Data Store (CDS)
<https://cds.climate.copernicus.eu/#!/home>`_ or automatically via the CDS api,
as done in the download module (era5_download). Before you can use this, you
have to set up an `account at the CDS
<https://cds.climate.copernicus.eu/drupal_auth_check>`_ and setup
the `CDS key <https://cds.climate.copernicus.eu/api-how-to>`_.

Then you can use the program ``era5_download`` to download ERA5 images between
a passed start and end date.
``era5_download --help`` will show additional information on using the command.


For example, the following command in your terminal would download ERA5 images
for all available layers of soil moisture in netcdf format, between
January 1st and February 1st 2000 in grib format into ``/path/to/storage``.
The data will be stored in subfolders of the format ``YYYY/jjj``. The temporal
resolution of the images is 6 hours by default.

.. code-block:: shell

    era5_download /path/to/storage -s 2000-01-01 -e 2000-02-01 --variables swvl1 swvl2 swvl3 swvl4

The names of the variables to download can be its long names, the short names
(as in the example) or the parameter IDs. We use the ``era5_lut.csv`` file to
look up the right name for the CDS API.
Other flags, that can be activated in ``era5_download`` are:

- **-h (--help)** : shows the help text for the download function
- **-p (--product)**: specify the ERA5 product to download. Choose either ERA5 or ERA5-Land. Default is ERA5.
- **-keep (--keep_original)** : keeps the originally downloaded files as well.
  We split the downloaded, monthly stacks into single images and discard the original
  files by default.
- **-grb (--as_grib)** : download the data in grib format instead of the default nc4
   format (grib reading is not supported on Windows OS).
- **--h_steps** : full hours for which images are downloaded (e.g. --h_steps 0
  would download only data at 00:00 UTC). By default we use 0, 6, 12 and 18.


Downloading ERA Interim Data
=================================
**ERA-Interim has been decommissioned. Use ERA5 instead.**

ERA-Interim data can be downloaded manually from the ECMWF servers. It can also
be done automatically using the ECMWF API. To use the ECMWF API you have to be
registered, install the ecmwf-api Python package and setup the ECMWF API Key. A
guide for this is provided by `ECMWF
<https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets>`_.

After that you can use the command line program ``eraint_download`` to download
images with a temporal resoltuion of 6 hours between a passed start and end date.
``eraint_download --help`` will show additional information on using the command.

For example, the following command in your terminal would download ERA Interim
soil moisture images of all available layers (see the
`Variable DB <https://apps.ecmwf.int/codes/grib/param-db>`_) in netcdf format on
the default gaussian grid for ERA-Interim (0.75°x0.75°) into
the folder ``/path/to/storage`` between January 1st and February 1st 2000.
The data will be stored in subfolders of the format ``YYYY/jjj``, where ``YYYY``
describes the year and ``jjj`` the day of the year for the downloaded files.

.. code-block:: shell

    eraint_download /path/to/storage  -s 2000-01-01 -e 2000-02-01 --variables swvl1 swvl2 swvl3 swvl4

Additional optional parameters allow downloading images in netcdf format, and
in a different spatial resolution (see the --help function and descriptions for
downloading ERA5 data)