Reading data
============

After downloading the data for ERA Interim or ERA5 via ``eraint_download`` resp.
``era5_download``, images can be read with the ``ERAGrbDs`` and
``ERANcDs`` (for grib and netcdf image stacks), respectively the
``ERAGrbImg`` and ``ERANcImg`` (for single grib and netcdf images) classes,
as defined in ``ecmwf_models.interface``.

For example, you can read the image for a single variable at a specific date.
In this case for a stack of grib files:

.. code-block:: python

    # Script to load a stack of downloaded grib images
    # and read a variable for a single date.
    from ecmwf_models.interface import ERAGrbDs
    root_path = "/path/to/storage"
    ds = ERAGrbDs(root_path, 'swvl1')
    data = ds.read(datetime(2000, 1, 1, 0))


You can also read multiple variables at a specific date by passing a list of parameters.
In this case for a set of netcdf files:

.. code-block:: python

    # Script to load a stack of downloaded netcdf images
    # and read two variables for a single date.
    from ecmwf_models.interface import ERANcDs
    root_path = "/path/to/storage"
    ds = ERANcDs(root_path, ['swvl1', 'swvl2'])
    data = ds.read(datetime(2000, 1, 1, 0))


All images between two given dates can be read using the
``ERAGrbDs.iter_images`` and ``ERANcDs.iter_images`` method.