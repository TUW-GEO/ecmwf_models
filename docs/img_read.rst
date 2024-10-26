Reading data
============

To read the downloaded image data in python we recommend standard libraries such
as `xarray <https://docs.xarray.dev/en/stable/>`_ or
`netCDF4 <https://unidata.github.io/netcdf4-python/>`_.

However, you can also use the internal classes from this package. The main
purpose of these, however, is to use them in the time series conversion
module.

For example, you can read the image for some variables at a specific date.
In this case for a stack of downloaded image files (the chosen date
must be available of course):

.. code-block:: python

    >> from ecmwf_models.era5.reader import ERA5NcDs
    >> root_path = "/path/to/netcdf_storage"
    >> ds = ERA5NcDs(root_path, parameter=['swvl1'])
    >> img = ds.read(datetime(2010, 1, 1, 0))

    # To read the coordinates
    >> img.lat   # also: img.lon
    array([[ 90. ,  90. ,  90. , ...,  90. ,  90. ,  90. ],
           [ 89.9,  89.9,  89.9, ...,  89.9,  89.9,  89.9],
           [ 89.8,  89.8,  89.8, ...,  89.8,  89.8,  89.8],
           ...,
           [-89.8, -89.8, -89.8, ..., -89.8, -89.8, -89.8],
           [-89.9, -89.9, -89.9, ..., -89.9, -89.9, -89.9],
           [-90. , -90. , -90. , ..., -90. , -90. , -90. ]])

    # To read the data variables
    >> img.data['swvl1']
    array([[   nan,    nan,    nan, ...,    nan,    nan,    nan],
           [   nan,    nan,    nan, ...,    nan,    nan,    nan],
           [   nan,    nan,    nan, ...,    nan,    nan,    nan],
           ...,
           [0.159 , 0.1589, 0.1588, ..., 0.1595, 0.1594, 0.1592],
           [0.1582, 0.1582, 0.1581, ..., 0.1588, 0.1587, 0.1584],
           [0.206 , 0.206 , 0.206 , ..., 0.206 , 0.206 , 0.206 ]])


The equivalent class to read grib files is called in ``ERA5GrbDs``.
