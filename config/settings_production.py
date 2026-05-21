"""
Django settings for NeuraxoCore - Production
"""

from .settings import *  # noqa

DEBUG = os.getenv('DEBUG', 'False') == 'True'
