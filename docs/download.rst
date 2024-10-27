Downloading ERA5 and ERA5-Land data
-----------------------------------

ERA5 (and ERA5-Land) data can be downloaded manually from the `Copernicus Data Store (CDS)
<https://cds.climate.copernicus.eu/#!/home>`_ or automatically via the CDS api,
as done in the download modules (``era5 download`` and ``era5land download``).
Before you can use this, you have to set up an `account at the CDS
<https://cds.climate.copernicus.eu>`_ and get your
`API key <https://cds.climate.copernicus.eu/how-to-api>`_.

Then you can use the programs ``era5 download`` and ``era5land download`` to
download ERA5 images between a passed start and end date.
Passing ``--help`` will show additional information on using the commands.

For example, the following command in your terminal would download ERA5 images
for all available layers of soil moisture in netcdf format, between
January 1st and February 1st 2000 in netcdf format into ``/path/to/storage``.
The data will be stored in subfolders of the format ``YYYY/jjj``. The temporal
resolution of the images is 6 hours by default, but can be changed using the
``--h_steps`` option.

.. code-block:: shell

    era5 download /path/to/storage -s 2000-01-01 -e 2000-02-01 \
        --variables swvl1,swvl2,swvl3,swvl4 --h_steps 0,6,18,24

The names of the variables to download can be its long names, the short names
(as in the example). See the :ref:`ERA5 variable table <variables_era5>`
and :ref:`ERA5-Land variable table <variables_era5land>` to look up the right
name for the CDS API.

By default, the command expects that you have set up your ``.cdsapirc`` file
to identify with the data store as described above. Alternatively you can pass
your token directly with the download command using the ``--cds_token`` option.
Or you can set an environment variable ``CDSAPI_KEY`` that contains your token.

We recommend downloading data in netcdf format, however, using the ``--as_grib``
option, you can also download data in grib format.

For all other available options, type ``era5 download --help``,
or ``era5land download --help`` respectively

Updating an existing record
---------------------------
After some time, new ERA data will become available. You can then use the
program ``era5 update_img`` with a path to the existing record, to download
new images with the same settings that became available since the last time
the record was downloaded. You might even set up a cron job to check for new
data in regular intervals to keep your copy up-to-date.