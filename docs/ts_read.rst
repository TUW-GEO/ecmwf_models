Reading converted time series data
----------------------------------

For reading time series data, that the ``era5 reshuffle`` and ``era5land reshuffle``
command produces, the class ``ERATs`` can be used. This will return a time series
of values for the chosen location.

Optional arguments that are forwarded to the parent class
(``OrthoMultiTs``, as defined in `pynetcf.time_series <https://github.com/TUW-GEO/pynetCF/blob/master/pynetcf/time_series.py>`_)
can be passed as well:

.. code-block:: python

    >> from ecmwf_models import ERATs
    # read_bulk reads full files into memory
    # read_ts takes either lon, lat coordinates to perform a nearest neighbour search
    # or a grid point index (from the grid.nc file) and returns a pandas.DataFrame.
    >> ds = ERATs(ts_path, ioclass_kws={'read_bulk': True})

    >> ds.read(18, 48)  # (lon, lat)

                            swvl1     swvl2
    2024-04-01 00:00:00  0.318054  0.329590
    2024-04-01 12:00:00  0.310715  0.325958
    2024-04-02 00:00:00  0.360229  0.323502
            ...             ...       ...
    2024-04-04 12:00:00  0.343353  0.348755
    2024-04-05 00:00:00  0.350266  0.346558
    2024-04-05 12:00:00  0.343994  0.344498

Bulk reading speeds up reading multiple points from a cell file by storing the
file in memory for subsequent calls. Either Longitude and Latitude can be passed
to perform a nearest neighbour search on the data grid (``grid.nc`` in the time series
path) or the grid point index (GPI) can be passed directly.
