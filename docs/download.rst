Downloading data ERA Interim Data
=================================

ERA-Interim data can be downloaded manually from the ECMWF servers. It can also
be done automatically using the ECMWF API. To use the ECMWF API you have to be
registered, install the ecmwf-api Python package and setup the ECMWF API Key. A
guide for this is provided by `ECMWF
<https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets>`_.

After that you can use the command line program ``eraint_download`` to download
images with a temporal resoltuion of 6 hours between a passed start and end date.
``eraint_download --help`` will show additional information on using the command.

For example, the following command in you terminal would download ERA Interim images
for variables 39 and 40 (Volumetric soil water layer 1 and 2, see the
`Variable DB <https://apps.ecmwf.int/codes/grib/param-db>`_) as well as a
land-sea mask in grib format on the default gaussian grid for ERA-Interim into
the folder ``/path/to/storage`` between January 1st and February 1st 2000.
The data will be stored in subfolders of the format ``YYYY/jjj``, where YYYY describes the
year and jjj the day of the year for the downloaded files.

.. code-block:: shell

    eraint_download /path/to/storage  -s 2000-01-01 -e 2000-02-01 --variables 39 40

Additional optional parameters allow downloading images in netcdf format, and
in a different spatial resolution (default 0.75°x0.75°).

Downloading data ERA5 Data
==========================

ERA5 data can be downloaded from the `Copernicus Data Store (CDS)
<https://cds.climate.copernicus.eu/#!/home>`_ or automatically via the CDS api,
as done in the download module (era5_download). Before you can use this, you
have to set up an `account at the CDS
<https://cds.climate.copernicus.eu/drupal_auth_check>`_ and setup
the `CDS key <https://cds.climate.copernicus.eu/api-how-to>`_.

Then you can use the program ``era5_download`` to download ERA5 images with
a temporal resolution of 6 hours between a passed start and end date.
``era5_download --help`` will show additional information on using the command.


For example, the following command in your terminal would download ERA5 images
for precipitation, top level soil moisture and a land-sea mask between
January 1st and February 1st 2000 in grib format into ``/path/to/storage``.
The data will be stored in subfolders of the format ``YYYY/jjj``, where YYYY describes the
year and jjj the day of the year for the downloaded files.

.. code-block:: shell

    era5_download /path/to/storage -s 2000-01-01 -e 2000-02-01 --variables total_precipitation volumetric_soil_water_layer_1
