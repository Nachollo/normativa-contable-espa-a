"""
Document Classification Agent Package
"""

__version__ = "1.0.0"
__author__ = "Document Classification Agent"
__description__ = "Sistema de clasificación automática de documentos"

from .document_classifier import DocumentClassifier
from .folder_organizer import FolderOrganizer
from .data_extractor import DataExtractor
from .utils import load_config, setup_logging

__all__ = [
    'DocumentClassifier',
    'FolderOrganizer', 
    'DataExtractor',
    'load_config',
    'setup_logging'
]