
Reading converted time series data
----------------------------------

For reading time series data, that the ``ecmwf_repurpose`` command produces, the class
``ERATs`` can be used. Optional arguments that are passed to the parent class
(``OrthoMultiTs``, as defined in `pynetcf.time_series <https://github.com/TUW-GEO/pynetCF/blob/master/pynetcf/time_series.py>`_)
can be passed as well:

.. code-block:: python

    from ecmwf_models.interface import ERATs
    ds = ERATs(ts_path, ioclass_kws={'read_bulk':True}) # read_bulk reads full files into memory
    # read_ts takes either lon, lat coordinates to perform a nearest neighbour search
    # or a grid point index (from the grid.nc file) and returns a pandas.DataFrame.
    ts = ds.read_ts(45, 15)