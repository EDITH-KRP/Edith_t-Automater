"""
FTK Metadata Capture Module
Extracts metadata from FTK Imager forensic images without needing FTK source code
"""

from .ftk_image_analyzer import FTKImageAnalyzer
from .ftk_integration import FTKIntegration, integrate_ftk_with_case

__version__ = "1.0.0"
__all__ = ['FTKImageAnalyzer', 'FTKIntegration', 'integrate_ftk_with_case']
