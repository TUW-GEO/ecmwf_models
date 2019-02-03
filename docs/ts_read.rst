
Reading converted time series data
----------------------------------

For reading time series data, that the ``ecmwf_repurpose`` command produces, the class
``ERATs`` can be used:

.. code-block:: python

    from ecmwf_models.interface import ERATs
    ds = ERATs(ts_path)
    # read_ts takes either lon, lat coordinates to perform a nearest neighbour search
    # or a grid point index (from the grid.nc file) and returns a pandas.DataFrame.
    ts = ds.read_ts(45, 15)