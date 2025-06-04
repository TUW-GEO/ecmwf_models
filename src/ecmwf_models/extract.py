import tempfile
from datetime import datetime
import logging
import os
import pandas as pd
import xarray as xr
import zipfile
import shutil
import numpy as np

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


def create_dt_fpath(dt, root, fname, subdirs=[]):
    """
    Create filepaths from root + fname and a list of subdirectories.
    fname and subdirs will be put through dt.strftime.

    Parameters
    ----------
    dt: datetime.datetime
        date as basis for the URL
    root: string
        root of the filenpath
    fname: string
        filename to use
    subdirs: list, optional
        list of strings.
        Each element represents a subdirectory.
        For example the list ['%Y', '%m'] would lead to a URL of
        ``root/YYYY/MM/fname`` or for a dt of datetime(2000,12,31)
        ``root/2000/12/fname``

    Returns
    -------
    fpath: string
        Full filename including path
    """
    dt_subdirs = []
    for subdir in subdirs:
        dt_subdirs.append(dt.strftime(subdir))
    dt_fname = dt.strftime(fname)
    flist = [root] + dt_subdirs + [dt_fname]
    fpath = os.path.join(*flist)
    return fpath


def unzip_nc(
        input_zip,
        output_nc,
):
    """
    Unzip and merge all netcdf files downloaded from CDS. If the zip file
    contains only 1 netcdf file, it only be extracted.

    Parameters
    ----------
    input_zip: str
        Path to the downloaded zip file containing one or more (datastream)
        netcdf files.
    output_nc: str
        Path to the netcdf file to write
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(input_zip, "r") as zip_ref:
            zip_ref.extractall(tmpdir)
        ncfiles = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir)
                   if f.endswith(".nc")]
        if len(ncfiles) == 1:
            shutil.move(ncfiles[0], output_nc)
        else:
            # Sometimes CDS returns multiple netcdf files, merge them
            ds = [xr.open_dataset(os.path.join(tmpdir, f)) for f in ncfiles]
            expvers = []
            for d in ds:
                if 'expver' in d.coords:
                    expvers.append(d.coords['expver'].values.astype(int))
            if len(expvers) > 0:
                expvers = np.array(expvers).max(axis=0)
                for d in ds:
                    d.coords['expver'] = np.array([f"{e:04}" for e in expvers])

            ds = xr.combine_by_coords(ds, combine_attrs="override",
                                      compat='override')
            ds.to_netcdf(output_nc, encoding={
                v: {'zlib': True, 'complevel': 6} for v in ds.data_vars})

    os.remove(input_zip)


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
    if 'valid_time' in nc_in.dims:
        nc_in = nc_in.rename_dims({"valid_time": 'time'})
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

    for i, time in enumerate(nc_in["time"].values):
        subset = nc_in.sel({"time": time})

        # Expver identifies preliminary data
        if 'expver' in subset:
            ex = np.atleast_1d(subset['expver'].values)
            if len(ex) == 1:
                expver = str(ex[0])
            else:
                expver = str(ex[i])
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
