"""
AI-powered Document Processing Module
Handles intelligent document classification, OCR, and data extraction using AI models
"""

import os
import logging
import torch
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    pipeline = None
    SentenceTransformer = None

try:
    import openai
except ImportError:
    openai = None

try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    import cv2
except ImportError:
    convert_from_path = None
    pytesseract = None
    Image = None
    cv2 = None


class AIDocumentProcessor:
    """AI-powered document processor for classification and extraction"""
    
    def __init__(self, config: Dict):
        """Initialize AI processor with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # AI configuration
        self.use_openai = config.get('ai', {}).get('use_openai', False)
        self.openai_api_key = config.get('ai', {}).get('openai_api_key', os.getenv('OPENAI_API_KEY'))
        self.use_local_models = config.get('ai', {}).get('use_local_models', True)
        
        # Initialize models
        self._initialize_models()
        
        # OCR configuration
        self.ocr_enabled = config.get('extraction', {}).get('ocr_enabled', True)
        self.ocr_languages = config.get('extraction', {}).get('ocr_languages', ['spa', 'eng'])
        
        # Parallel processing
        self.max_workers = config.get('processing', {}).get('max_workers', 4)
        
    def _initialize_models(self):
        """Initialize AI models for document processing"""
        self.logger.info("Initializing AI models...")
        
        # Initialize embedding model for semantic similarity
        if self.use_local_models and SentenceTransformer:
            try:
                self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                self.logger.info("Loaded multilingual embedding model")
            except Exception as e:
                self.logger.warning(f"Failed to load embedding model: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
        
        # Initialize OpenAI if configured
        if self.use_openai and openai and self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.logger.info("OpenAI API configured")
        
        # Initialize zero-shot classification model
        if self.use_local_models and pipeline:
            try:
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if torch.cuda.is_available() else -1
                )
                self.logger.info("Loaded zero-shot classification model")
            except Exception as e:
                self.logger.warning(f"Failed to load classifier: {e}")
                self.classifier = None
        else:
            self.classifier = None
    
    def classify_with_ai(self, text: str, document_types: List[str]) -> Dict[str, Any]:
        """
        Classify document using AI models
        
        Args:
            text: Document text content
            document_types: List of possible document types
            
        Returns:
            Classification results with confidence scores
        """
        results = {
            'document_type': 'unknown',
            'confidence': 0.0,
            'scores': {},
            'method': 'ai'
        }
        
        # Try OpenAI GPT-4 first if available
        if self.use_openai and openai:
            try:
                results = self._classify_with_openai(text, document_types)
                return results
            except Exception as e:
                self.logger.warning(f"OpenAI classification failed: {e}")
        
        # Fall back to local models
        if self.classifier:
            try:
                results = self._classify_with_local_model(text, document_types)
                return results
            except Exception as e:
                self.logger.warning(f"Local model classification failed: {e}")
        
        # Fall back to embedding similarity
        if self.embedding_model:
            try:
                results = self._classify_with_embeddings(text, document_types)
                return results
            except Exception as e:
                self.logger.warning(f"Embedding classification failed: {e}")
        
        return results
    
    def _classify_with_openai(self, text: str, document_types: List[str]) -> Dict[str, Any]:
        """Classify document using OpenAI GPT models"""
        prompt = f"""Analiza el siguiente texto de un documento y clasifícalo en uno de estos tipos:
{', '.join(document_types)}

Texto del documento:
{text[:2000]}

Responde en formato JSON con:
- document_type: el tipo de documento más probable
- confidence: tu nivel de confianza (0.0 a 1.0)
- reasoning: breve explicación de tu decisión
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en clasificación de documentos contables y legales españoles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        return {
            'document_type': result_json.get('document_type', 'unknown'),
            'confidence': result_json.get('confidence', 0.0),
            'reasoning': result_json.get('reasoning', ''),
            'method': 'openai-gpt4'
        }
    
    def _classify_with_local_model(self, text: str, document_types: List[str]) -> Dict[str, Any]:
        """Classify using local zero-shot classification model"""
        # Prepare text (limit to avoid memory issues)
        text_sample = text[:1000]
        
        # Classify
        result = self.classifier(
            text_sample,
            candidate_labels=document_types,
            hypothesis_template="Este documento es un {}."
        )
        
        return {
            'document_type': result['labels'][0],
            'confidence': result['scores'][0],
            'scores': dict(zip(result['labels'], result['scores'])),
            'method': 'zero-shot-local'
        }
    
    def _classify_with_embeddings(self, text: str, document_types: List[str]) -> Dict[str, Any]:
        """Classify using semantic embeddings"""
        # Create embeddings for document
        doc_embedding = self.embedding_model.encode(text[:1000])
        
        # Create embeddings for document type descriptions
        type_descriptions = {
            'factura': 'factura invoice pago importe total IVA',
            'contrato': 'contrato acuerdo partes cláusulas firma',
            'nomina': 'nómina salario sueldo empleado seguridad social',
            'balance': 'balance activo pasivo patrimonio cuenta',
            'recibo': 'recibo ticket comprobante compra',
            'escritura': 'escritura notarial notario protocolo',
            'justificante_pago': 'justificante pago transferencia banco',
            'extracto_bancario': 'extracto bancario movimientos saldo cuenta',
            'cirbe': 'CIRBE riesgo crédito Banco España endeudamiento',
            'declaracion_fiscal': 'declaración fiscal impuesto modelo hacienda',
            'circularizacion': 'circularización confirmación auditoría verificación',
            'albaran': 'albarán entrega mercancía pedido',
            'rlc': 'registro mercantil inscripción sociedad',
            'rnt': 'registro propiedad finca inmueble'
        }
        
        # Calculate similarities
        scores = {}
        for doc_type in document_types:
            if doc_type in type_descriptions:
                type_embedding = self.embedding_model.encode(type_descriptions[doc_type])
                similarity = np.dot(doc_embedding, type_embedding) / (
                    np.linalg.norm(doc_embedding) * np.linalg.norm(type_embedding)
                )
                scores[doc_type] = float(similarity)
        
        # Get best match
        if scores:
            best_type = max(scores, key=scores.get)
            return {
                'document_type': best_type,
                'confidence': scores[best_type],
                'scores': scores,
                'method': 'embedding-similarity'
            }
        
        return {
            'document_type': 'unknown',
            'confidence': 0.0,
            'method': 'embedding-similarity'
        }
    
    def extract_with_ai(self, text: str, document_type: str, template: Dict) -> Dict[str, Any]:
        """
        Extract structured data using AI
        
        Args:
            text: Document text
            document_type: Type of document
            template: Extraction template
            
        Returns:
            Extracted data
        """
        if self.use_openai and openai:
            try:
                return self._extract_with_openai(text, document_type, template)
            except Exception as e:
                self.logger.warning(f"OpenAI extraction failed: {e}")
        
        # Fall back to template-based extraction
        return {}
    
    def _extract_with_openai(self, text: str, document_type: str, template: Dict) -> Dict[str, Any]:
        """Extract data using OpenAI GPT models"""
        fields = template.get('fields', {})
        field_descriptions = {
            name: field.get('description', name)
            for name, field in fields.items()
        }
        
        prompt = f"""Extrae los siguientes datos de este documento tipo {document_type}:

Campos a extraer:
{json.dumps(field_descriptions, indent=2, ensure_ascii=False)}

Texto del documento:
{text[:3000]}

Responde SOLO con un JSON válido con los campos extraídos. Si no encuentras un campo, usa null.
"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto extrayendo datos estructurados de documentos españoles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content
        # Remove markdown code blocks if present
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        extracted_data = json.loads(result_text)
        
        return {
            'data': extracted_data,
            'method': 'openai-gpt4',
            'confidence': 0.9
        }
    
    def enhanced_ocr(self, image_path: Path) -> str:
        """
        Perform enhanced OCR with preprocessing
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        if not self.ocr_enabled or not pytesseract or not cv2:
            self.logger.warning("OCR not available")
            return ""
        
        try:
            # Load image
            img = cv2.imread(str(image_path))
            
            # Preprocess image for better OCR
            img = self._preprocess_image_for_ocr(img)
            
            # Perform OCR with multiple languages
            lang_string = '+'.join(self.ocr_languages)
            text = pytesseract.image_to_string(img, lang=lang_string)
            
            return text
            
        except Exception as e:
            self.logger.error(f"OCR failed for {image_path}: {e}")
            return ""
    
    def _preprocess_image_for_ocr(self, img):
        """Preprocess image to improve OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        # Deskew if needed
        # (Could add deskewing algorithm here)
        
        return thresh
    
    def process_pdf_with_ocr(self, pdf_path: Path) -> str:
        """
        Extract text from PDF with OCR for scanned pages
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Combined extracted text
        """
        if not convert_from_path:
            return ""
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            # OCR each page
            all_text = []
            for i, image in enumerate(images):
                self.logger.info(f"OCR processing page {i+1}/{len(images)}")
                
                # Convert PIL image to numpy array for OpenCV
                img_array = np.array(image)
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # Preprocess and OCR
                preprocessed = self._preprocess_image_for_ocr(img_array)
                lang_string = '+'.join(self.ocr_languages)
                text = pytesseract.image_to_string(preprocessed, lang=lang_string)
                all_text.append(text)
            
            return '\n\n'.join(all_text)
            
        except Exception as e:
            self.logger.error(f"PDF OCR failed for {pdf_path}: {e}")
            return ""
    
    def process_documents_batch(self, file_paths: List[Path], callback=None) -> List[Dict[str, Any]]:
        """
        Process multiple documents in parallel
        
        Args:
            file_paths: List of document paths
            callback: Optional callback function for progress
            
        Returns:
            List of processing results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for file_path in file_paths:
                future = executor.submit(self._process_single_document, file_path)
                futures.append((file_path, future))
            
            for i, (file_path, future) in enumerate(futures):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if callback:
                        callback(i + 1, len(file_paths), file_path, result)
                        
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {e}")
                    results.append({
                        'file_path': str(file_path),
                        'error': str(e),
                        'status': 'failed'
                    })
        
        return results
    
    def _process_single_document(self, file_path: Path) -> Dict[str, Any]:
        """Process a single document (used by batch processing)"""
        # This would be called by the main document agent
        return {
            'file_path': str(file_path),
            'status': 'processed'
        }
