from datetime import datetime
import logging
import os
import pandas as pd
import xarray as xr
from datedown.fname_creator import create_dt_fpath

from ecmwf_models.globals import (IMG_FNAME_TEMPLATE,
                                  IMG_FNAME_DATETIME_FORMAT, EXPVER, SUBDIRS)
from ecmwf_models.globals import (
    Cdo,
    cdo_available,
    CdoNotFoundError,
    pygrib,
    pygrib_available,
    PygribNotFoundError,
)


def save_ncs_from_nc(
    input_nc,
    output_path,
    product_name,
    grid=None,
    keep_original=True,
    remap_method="bil",
    keep_prelim=True,
):
    """
    Split the downloaded netcdf file into daily files and add to folder
    structure necessary for reshuffling.

    Parameters
    ----------
    input_nc : str
        Filepath of the downloaded .nc file
    output_path : str
        Where to save the resulting netcdf files
    product_name : str
        Name of the ECMWF model (only for filename generation)
    keep_original: bool
        keep the original downloaded data too, before it is sliced into
        individual images.
    keep_prelim: bool, optional (default: True)
        True to keep preliminary data from ERA5T with a different file name, or
        False drop these files and only keep the final records.
    """
    _filename_templ = IMG_FNAME_TEMPLATE.format(
        product="{product}",
        type='AN',
        datetime=IMG_FNAME_DATETIME_FORMAT,
        ext='nc')

    nc_in = xr.open_dataset(input_nc, mask_and_scale=True)
    if 'valid_time' in nc_in.variables:
        nc_in = nc_in.rename_vars({"valid_time": 'time'})

    if grid is not None:
        if not cdo_available:
            raise CdoNotFoundError()
        cdo = Cdo()

        gridpath = os.path.join(output_path, "grid.txt")
        weightspath = os.path.join(output_path, "remap_weights.nc")
        if not os.path.exists(gridpath):
            with open(gridpath, "w") as f:
                for k, v in grid.items():
                    f.write(f"{k} = {v}\n")

    for time in nc_in["time"].values:
        subset = nc_in.sel({"time": time})

        # Expver identifies preliminary data
        if 'expver' in subset:
            expver = str(subset['expver'].values)
            subset = subset.drop_vars('expver')
            try:
                ext = EXPVER[expver]
            except KeyError:
                ext = ''
        else:
            ext = ''

        if len(ext) > 0 and not keep_prelim:
            logging.info(f"Dropping preliminary data {time}")
            continue

        if len(ext) > 0:
            filename_templ = _filename_templ.format(product=product_name +
                                                    '-' + ext)
        else:
            filename_templ = _filename_templ.format(product=product_name)

        if 'number' in subset.variables:
            subset = subset.drop_vars('number')

        timestamp = pd.Timestamp(time).to_pydatetime()
        filepath = create_dt_fpath(
            timestamp,
            root=output_path,
            fname=filename_templ,
            subdirs=SUBDIRS,
        )

        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        if grid is not None:
            if not os.path.exists(weightspath):
                # create weights file
                getattr(cdo, "gen" + remap_method)(
                    gridpath, input=subset, output=weightspath)
            subset = cdo.remap(
                ",".join([gridpath, weightspath]),
                input=subset,
                returnXDataset=True,
            )

        # same compression for all variables
        var_encode = {"zlib": True, "complevel": 6}
        subset.to_netcdf(
            filepath, encoding={var: var_encode for var in subset.variables})

    nc_in.close()

    if not keep_original:
        os.remove(input_nc)
    if grid is not None:
        cdo.cleanTempDir()


def save_gribs_from_grib(
    input_grib,
    output_path,
    product_name,
    keep_original=True,
    keep_prelim=True,
):
    """
    Split the downloaded grib file into daily files and add to folder structure
    necessary for reshuffling.

    Parameters
    ----------
    input_grib : str
        Filepath of the downloaded .grb file
    output_path : str
        Where to save the resulting grib files
    product_name : str
        Name of the ECMWF model (only for filename generation)
    keep_original: bool
        keep the original downloaded data too, before it is sliced into
        individual images.
    keep_prelim: bool, optional (default: True)
        True to keep preliminary data from ERA5T with a different file name, or
        False drop these files and only keep the final records.
    """
    if not pygrib_available:
        raise PygribNotFoundError()
    grib_in = pygrib.open(input_grib)

    _filename_templ = IMG_FNAME_TEMPLATE.format(
        product="{product}",
        type='AN',
        datetime=IMG_FNAME_DATETIME_FORMAT,
        ext='grb')

    grib_in.seek(0)
    prev_date = None

    for grb in grib_in:
        filedate = datetime(grb["year"], grb["month"], grb["day"], grb["hour"])

        expver = grb['expver']

        try:
            ext = EXPVER[expver]
        except KeyError:
            ext = ''

        if len(ext) > 0 and not keep_prelim:
            logging.info(f"Dropping preliminary data {filedate}")
            continue

        if len(ext) > 0:
            filename_templ = _filename_templ.format(product=product_name +
                                                    '-' + ext)
        else:
            filename_templ = _filename_templ.format(product=product_name)

        filepath = create_dt_fpath(
            filedate, root=output_path, fname=filename_templ, subdirs=SUBDIRS)

        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))

        if prev_date != filedate:  # to overwrite old files
            mode = 'wb'
            prev_date = filedate
        else:
            mode = "ab"

        with open(filepath, mode) as grb_out:
            grb_out.write(grb.tostring())

    grib_in.close()

    if not keep_original:
        os.remove(input_grib)
