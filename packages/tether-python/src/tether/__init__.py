"""
Tether - Python backend utilities for AI/ML desktop applications.
"""

from tether.app import create_app
from tether.config import Settings, get_settings

__version__ = "0.1.0"
__all__ = ["create_app", "Settings", "get_settings", "__version__"]
