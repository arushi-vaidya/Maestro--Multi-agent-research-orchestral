"""Patent Data Sources"""

from .uspto_client import USPTOClient
from .lens_org_client import LensOrgClient
from .google_patents_client import GooglePatentsClient

__all__ = ['USPTOClient', 'LensOrgClient', 'GooglePatentsClient']
