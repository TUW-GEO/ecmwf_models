# -*- coding: utf-8 -*-

"""
This module contains ERA Interim specific child classes of the netcdf and grib
base classes, that are used for reading all ecmwf products.
"""

from ecmwf_models.interface import ERANcImg, ERANcDs, ERAGrbImg, ERAGrbDs
import warnings
from typing import Collection, Optional
from pygeogrids.grids import CellGrid


class ERAIntNcImg(ERANcImg):
    def __init__(
        self,
        filename: str,
        parameter: Optional[Collection[str]] = ("swvl1", "swvl2"),
        mode: Optional[str] = "r",
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        array_1D: Optional[bool] = False,
    ):
        """
        Reader for a single ERA INT netcdf image file.

        Parameters
        ----------
        filename: str
            Path to the image file to read.
        parameter: list or str, optional (default: ('swvl1', 'swvl2'))
            Name of parameters to read from the image file.
        subgrid: CellGrid, optional (default: None)
            Read only data for points of this grid and not global values.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and
            set them to nan. This option needs the 'lsm' parameter to be
            in the file!
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        """
        warnings.warn(
            "ERA Interim data is deprecated. Use ERA5 instead.",
            DeprecationWarning,
        )
        product = "ERAINT"
        super(ERAIntNcImg, self).__init__(
            filename=filename,
            product=product,
            parameter=parameter,
            mode=mode,
            subgrid=subgrid,
            mask_seapoints=mask_seapoints,
            array_1D=array_1D,
        )


class ERAIntNcDs(ERANcDs):
    def __init__(
        self,
        root_path: str,
        parameter: Optional[Collection[str]] = ("swvl1", "swvl2"),
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        h_steps: Collection[int] = (0, 6, 12, 18),
        array_1D: Optional[bool] = False,
    ):

        """
        Reader for a stack of ERA INT netcdf image files.

        Parameters
        ----------
        root_path: str
            Path to the image files to read.
        parameter: list or str, optional (default: ('swvl1', 'swvl2'))
            Name of parameters to read from the image file.
        subgrid: pygeogrids.CellGrid, optional (default: None)
            Read only data for points of this grid and not global values.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and set them
            to nan. This option needs the 'lsm' parameter to be in the file!
        h_steps : list, optional (default: (0,6,12,18))
            List of full hours to read images for.
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        """

        warnings.warn(
            "ERA Interim data is deprecated. Use ERA5 instead.",
            DeprecationWarning,
        )
        product = "ERAINT"
        super(ERAIntNcDs, self).__init__(
            root_path=root_path,
            product=product,
            parameter=parameter,
            subgrid=subgrid,
            mask_seapoints=mask_seapoints,
            h_steps=h_steps,
            array_1D=array_1D,
        )


class ERAIntGrbImg(ERAGrbImg):
    def __init__(
        self,
        filename: str,
        parameter: Optional[Collection[str]] = ("swvl1", "swvl2"),
        mode: Optional[str] = "r",
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        array_1D: Optional[bool] = False,
    ):
        """
        Reader for a single ERA5 grib image file.

        Parameters
        ----------
        filename: str
            Path to the image file to read.
        parameter: list or str, optional (default: ['swvl1', 'swvl2'])
            Name of parameters to read from the image file.
        mode: str, optional (default: "r")
            File mode, better don't change...
        subgrid: pygeogrids.CellGrid, optional (default: None)
            Read only data for points of this grid and not global values.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and set
            them to nan. This option needs the 'lsm' parameter to be in
            the file!
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        """
        warnings.warn(
            "ERA Interim data is deprecated. Use ERA5 instead.",
            DeprecationWarning,
        )
        product = "ERAINT"
        super(ERAIntGrbImg, self).__init__(
            filename=filename,
            product=product,
            parameter=parameter,
            mode=mode,
            subgrid=subgrid,
            mask_seapoints=mask_seapoints,
            array_1D=array_1D,
        )


class ERAIntGrbDs(ERAGrbDs):
    def __init__(
        self,
        root_path: str,
        parameter: Collection[str] = ("swvl1", "swvl2"),
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        h_steps: Collection[int] = (0, 6, 12, 18),
        array_1D: Optional[bool] = False,
    ):
        """
        Reader for a stack of ERA INT grib image file.

        Parameters
        ----------
        root_path: str
            Path to the image files to read.
        parameter: list or str, optional (default: ['swvl1', 'swvl2'])
            Name of parameters to read from the image file.
        subgrid: CellGrid, optional (default: None)
            Read only data for points of this grid and not global values.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and set them
            to nan. This option needs the 'lsm' parameter to be in the file!
        h_steps : list, optional (default: [0,6,12,18])
            List of full hours to read images for.
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        """
        warnings.warn(
            "ERA Interim data is deprecated. Use ERA5 instead.",
            DeprecationWarning,
        )
        product = "ERAINT"
        super(ERAIntGrbDs, self).__init__(
            root_path=root_path,
            product=product,
            parameter=parameter,
            subgrid=subgrid,
            mask_seapoints=mask_seapoints,
            h_steps=h_steps,
            array_1D=array_1D,
        )
