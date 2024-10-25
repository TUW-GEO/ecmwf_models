# -*- coding: utf-8 -*-
"""
This module contains ERA5/ERA5-Land specific child classes of the netcdf
and grib base classes, that are used for reading all ecmwf products.
"""

from typing import Optional, Collection
from typing_extensions import Literal
from pygeogrids.grids import CellGrid

from ecmwf_models.utils import assert_product
from ecmwf_models.interface import ERANcImg, ERANcDs, ERAGrbImg, ERAGrbDs


class ERA5NcImg(ERANcImg):

    def __init__(
        self,
        filename: str,
        parameter: Collection[str] = None,
        product: Literal['era5', 'era5-land'] = 'era5',
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        array_1D: Optional[bool] = False,
    ):
        """
        Reader for a single ERA5 netcdf image file.

        Parameters
        ----------
        filename: str
            Path to the image file to read.
        parameter: list[str] or str, optional (default: None)
            Name of parameters to read from the image file.
            None means all parameter
        product: str, optional (default: 'era5')
            What era5 product, either era5 or era5-land.
        subgrid: pygeogrids.CellGrid, optional (default: None)
            Read only data for points of this grid and not global values.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and
            set them to nan. This option needs the 'lsm' parameter to be
            in the file!
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        """

        super(ERA5NcImg, self).__init__(
            filename=filename,
            product=assert_product(product.lower()),
            parameter=parameter,
            subgrid=subgrid,
            mask_seapoints=mask_seapoints,
            array_1D=array_1D,
        )


class ERA5NcDs(ERANcDs):
    """
    Reader for a stack of ERA5 netcdf image files.

    Parameters
    ----------
    root_path: str
        Path to the image files to read.
    parameter: list[str] or str, optional (default: None)
        Name of parameters to read from the image file.
        None means all parameter
    product: str, optional (default: 'era5')
        What era5 product, either `era5` or `era5-land`.
    h_steps : list, optional (default: (0,6,12,18))
        List of full hours to read images for.
    subgrid: pygeogrids.CellGrid, optional (default: None)
        Read only data for points of this grid and not global values.
    mask_seapoints : bool, optional (default: False)
        Read the land-sea mask to mask points over water and set them to nan.
        This option needs the 'lsm' parameter to be in the file!
    array_1D: bool, optional (default: False)
        Read data as list, instead of 2D array, used for reshuffling.
    """

    def __init__(
        self,
        root_path: str,
        parameter: Collection[str] = None,
        product: str = 'era5',
        h_steps: Collection[int] = (0, 6, 12, 18),
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        array_1D: Optional[bool] = False,
    ):
        super(ERA5NcDs, self).__init__(
            root_path=root_path,
            product=assert_product(product.lower()),
            parameter=parameter,
            subgrid=subgrid,
            h_steps=h_steps,
            array_1D=array_1D,
            mask_seapoints=mask_seapoints,
        )


class ERA5GrbImg(ERAGrbImg):

    def __init__(
        self,
        filename: str,
        parameter: Collection[str] = None,
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        array_1D=False,
    ):
        """
        Reader for a single ERA5 grib image file.

        Parameters
        ----------
        filename: str
            Path to the image file to read.
        parameter: list[str] or str, optional (default: None)
            Name of parameters to read from the image file.
            None means all parameter
        subgrid: pygeogrids.CellGrid, optional (default: None)
            Read only data for points of this grid and not global values.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and set
            them to nan. This option needs the 'lsm' parameter to be in
            the file!
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        """
        super(ERA5GrbImg, self).__init__(
            filename=filename,
            product="era5",
            parameter=parameter,
            subgrid=subgrid,
            mask_seapoints=mask_seapoints,
            array_1D=array_1D,
        )


class ERA5GrbDs(ERAGrbDs):

    def __init__(
        self,
        root_path: str,
        parameter: Collection[str] = None,
        h_steps: Collection[int] = (0, 6, 12, 18),
        product: str = "era5",
        subgrid: Optional[CellGrid] = None,
        mask_seapoints: Optional[bool] = False,
        array_1D: Optional[bool] = False,
    ):
        """
        Reader for a stack of ERA5 grib image file.

        Parameters
        ----------
        root_path: str
            Path to the image files to read.
        parameter: list[str] or str, optional (default: None)
            Name of parameters to read from the image file.
            None means all parameter
        h_steps : list, optional (default: [0,6,12,18])
            List of full hours to read images for.
        product: str, optional (default: 'era5')
            What era5 product, either `era5` or `era5-land`.
        subgrid: pygeogrids.CellGrid, optional (default: None)
            Read only data for points of this grid and not global values.
        mask_seapoints : bool, optional (default: False)
            Read the land-sea mask to mask points over water and set them
            to nan. This option needs the 'lsm' parameter to be in the file!
        array_1D: bool, optional (default: False)
            Read data as list, instead of 2D array, used for reshuffling.
        """

        super(ERA5GrbDs, self).__init__(
            root_path=root_path,
            product=assert_product(product.lower()),
            parameter=parameter,
            subgrid=subgrid,
            h_steps=h_steps,
            mask_seapoints=mask_seapoints,
            array_1D=array_1D,
        )
