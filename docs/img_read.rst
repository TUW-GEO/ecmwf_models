Reading data
============

After downloading the data for ERA Interim or ERA5 via ``eraint_download`` resp.
``era5_download``, images can be read with the ``ERA5GrbDs`` and
``ERA5NcDs`` (for grib and netcdf image stacks), respectively the
``ERA5GrbImg`` and ``ERA5NcImg`` (for single grib and netcdf images) classes.
The respective functions for reading images are defined in
``ecmwf_models.erainterim.interface`` ``ecmwf_models.era5.interface``.

The following examples are shown for ERA5 data, but work the same way with the
respective ERA Interim functions.

For example, you can read the image for a single variable at a specific date.
In this case for a stack of downloaded image files:

.. code-block:: python

    # Script to load a stack of downloaded netcdf images
    # and read a variable for a single date.
    from ecmwf_models.era5.interface import ERA5NcDs
    root_path = "/path/to/netcdf_storage"
    ds = ERA5NcDs(root_path, parameter='swvl1')
    data = ds.read(datetime(2010, 1, 1, 0))

    # Script to load a stack of downloaded grib images
    # and read a variable for a single date.
    from ecmwf_models.era5.interface import ERA5GrbDs
    root_path = "/path/to/grib_storage"
    ds = ERA5GrbDs(root_path, parameter='swvl1')
    data = ds.read(datetime(2010, 1, 1, 0))


You can also read multiple variables at a specific date by passing a list of parameters.
In this case for a set of netcdf files:

.. code-block:: python

    # Script to load a stack of downloaded netcdf images
    # and read two variables for a single date.
    from ecmwf_models.era5.interface import ERA5NcDs
    root_path = "/path/to/storage"
    ds = ERA5NcDs(root_path, parameter=['swvl1', 'swvl2'])
    data = ds.read(datetime(2000, 1, 1, 0))


All images between two given dates can be read using the
``iter_images`` methods of all the image stack reader classes.