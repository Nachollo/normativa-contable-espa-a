"""
Document Classifier Module
Handles document type classification based on content and metadata
"""

import os
import re
import magic
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None


class DocumentClassifier:
    """Classifies documents based on content, filename, and metadata"""
    
    def __init__(self, config: Dict):
        """Initialize classifier with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.document_types = config['document_types']
        self.confidence_threshold = config['classification']['confidence_threshold']
        
        # Initialize file type detector
        self.magic = magic.Magic(mime=True)
    
    def classify_document(self, file_path: Path) -> Dict[str, any]:
        """
        Classify a document and return classification results
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with classification results
        """
        result = {
            'file_path': str(file_path),
            'filename': file_path.name,
            'document_type': 'unknown',
            'confidence': 0.0,
            'detected_keywords': [],
            'file_type': 'unknown',
            'file_size': 0
        }
        
        try:
            # Basic file information
            result['file_size'] = file_path.stat().st_size
            result['file_type'] = self._detect_file_type(file_path)
            
            # Extract text content
            text_content = self._extract_text(file_path)
            
            # Classify based on content and filename
            classification = self._classify_content(file_path.name, text_content)
            
            result.update(classification)
            
            self.logger.info(f"Classified {file_path.name} as {result['document_type']} "
                           f"(confidence: {result['confidence']:.2f})")
            
        except Exception as e:
            self.logger.error(f"Error classifying {file_path}: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Detect the MIME type of a file"""
        try:
            mime_type = self.magic.from_file(str(file_path))
            return mime_type
        except Exception as e:
            self.logger.warning(f"Could not detect MIME type for {file_path}: {str(e)}")
            # Fallback to extension-based detection
            extension = file_path.suffix.lower()
            extension_map = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.xls': 'application/vnd.ms-excel',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain'
            }
            return extension_map.get(extension, 'application/octet-stream')
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text content from various file types"""
        text = ""
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.pdf':
                text = self._extract_text_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                text = self._extract_text_from_docx(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                text = self._extract_text_from_excel(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                text = self._extract_text_from_image(file_path)
            elif file_extension == '.txt':
                text = self._extract_text_from_txt(file_path)
            else:
                self.logger.warning(f"Unsupported file type: {file_extension}")
        
        except Exception as e:
            self.logger.error(f"Error extracting text from {file_path}: {str(e)}")
        
        return text
    
    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF files"""
        text = ""
        
        # Try pdfplumber first (better for complex layouts)
        if pdfplumber:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    return text
            except Exception as e:
                self.logger.warning(f"pdfplumber failed for {file_path}: {str(e)}")
        
        # Fallback to PyPDF2
        if PyPDF2:
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                self.logger.warning(f"PyPDF2 failed for {file_path}: {str(e)}")
        
        return text
    
    def _extract_text_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX files"""
        if not DocxDocument:
            self.logger.warning("python-docx not available")
            return ""
        
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            self.logger.error(f"Error reading DOCX {file_path}: {str(e)}")
            return ""
    
    def _extract_text_from_excel(self, file_path: Path) -> str:
        """Extract text from Excel files"""
        if not load_workbook:
            self.logger.warning("openpyxl not available")
            return ""
        
        try:
            workbook = load_workbook(file_path, data_only=True)
            text = ""
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                for row in sheet.iter_rows(values_only=True):
                    row_text = " ".join([str(cell) for cell in row if cell is not None])
                    if row_text.strip():
                        text += row_text + "\n"
            
            return text
        except Exception as e:
            self.logger.error(f"Error reading Excel {file_path}: {str(e)}")
            return ""
    
    def _extract_text_from_image(self, file_path: Path) -> str:
        """Extract text from images using OCR"""
        if not (Image and pytesseract):
            self.logger.warning("PIL and pytesseract not available for OCR")
            return ""
        
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='spa+eng')
            return text
        except Exception as e:
            self.logger.error(f"Error performing OCR on {file_path}: {str(e)}")
            return ""
    
    def _extract_text_from_txt(self, file_path: Path) -> str:
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                self.logger.error(f"Error reading text file {file_path}: {str(e)}")
                return ""
    
    def _classify_content(self, filename: str, content: str) -> Dict[str, any]:
        """
        Classify document based on filename and content
        
        Args:
            filename: Name of the file
            content: Extracted text content
            
        Returns:
            Classification results
        """
        scores = {}
        detected_keywords = []
        
        # Combine filename and content for analysis
        full_text = (filename + " " + content).lower()
        
        # Score each document type
        for doc_type, type_config in self.document_types.items():
            score = 0
            type_keywords = []
            
            # Check keywords
            keywords = type_config.get('keywords', [])
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in full_text:
                    # Count occurrences and weight by keyword importance
                    occurrences = full_text.count(keyword_lower)
                    score += occurrences
                    type_keywords.extend([keyword] * occurrences)
            
            # Normalize score by content length and keyword count
            if content:
                word_count = len(content.split())
                if word_count > 0:
                    score = score / max(word_count / 100, 1)  # Normalize by content length
            
            scores[doc_type] = score
            if type_keywords:
                detected_keywords.extend(type_keywords)
        
        # Find best match
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            
            # Convert to confidence (0-1 scale)
            confidence = min(best_score / 5.0, 1.0)  # Adjust scaling as needed
            
            if confidence >= self.confidence_threshold:
                return {
                    'document_type': best_type,
                    'confidence': confidence,
                    'detected_keywords': list(set(detected_keywords)),
                    'all_scores': scores
                }
        
        return {
            'document_type': 'unknown',
            'confidence': 0.0,
            'detected_keywords': detected_keywords,
            'all_scores': scores
        }
    
    def add_document_type(self, type_name: str, keywords: List[str], 
                         extensions: List[str], template: str):
        """Add a new document type for classification"""
        self.document_types[type_name] = {
            'keywords': keywords,
            'extensions': extensions,
            'template': template
        }
        self.logger.info(f"Added new document type: {type_name}")
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported document types"""
        return list(self.document_types.keys())