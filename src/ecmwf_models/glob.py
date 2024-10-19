import os
from pathlib import Path

# ERA5 products supported by the reader.
SUPPORTED_PRODUCTS = ['era5', 'era5-land']

CDS_API_URL = "https://cds.climate.copernicus.eu/api/v2"

# CDSAPI_RC variable must be set or we use home dir
DOTRC = os.environ.get('CDSAPI_RC', os.path.join(Path.home(), '.cdsapirc'))

class CdoNotFoundError(ModuleNotFoundError):
    def __init__(self, msg=None):
        _default_msg = "cdo and/or python-cdo not installed. " \
                       "Use conda to install it them under Linux."
        self.msg = _default_msg if msg is None else msg
