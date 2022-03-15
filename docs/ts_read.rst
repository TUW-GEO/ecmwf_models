
Reading converted time series data
----------------------------------

For reading time series data, that the ``era5_reshuffle`` and ``eraint_reshuffle``
command produces, the class ``ERATs`` can be used.
Optional arguments that are passed to the parent class
(``OrthoMultiTs``, as defined in `pynetcf.time_series <https://github.com/TUW-GEO/pynetCF/blob/master/pynetcf/time_series.py>`_)
can be passed as well:

.. code-block:: python

    from ecmwf_models import ERATs
    # read_bulk reads full files into memory
    # read_ts takes either lon, lat coordinates to perform a nearest neighbour search
    # or a grid point index (from the grid.nc file) and returns a pandas.DataFrame.
    ds = ERATs(ts_path, ioclass_kws={'read_bulk': True})
    ts = ds.read_ts(45, 15)

Bulk reading speeds up reading multiple points from a cell file by storing the
file in memory for subsequent calls. Either Longitude and Latitude can be passed
to perform a nearest neighbour search on the data grid (``grid.nc`` in the time series
path) or the grid point index (GPI) can be passed directly.
