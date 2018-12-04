import pkgutil
import sys
from .config import Config

__all__ = ['__version__', 'version_info', 'Config']

__version__ = pkgutil.get_data(__package__, 'VERSION').decode('ascii').strip()
version_info = tuple(int(v) if v.isdigit() else v
                     for v in __version__.split('.'))

del pkgutil
del sys
