import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'

from ecmwf_models.interface import ERAInterimImg
from ecmwf_models.interface import ERAInterimDs
