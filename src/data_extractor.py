"""
Data Extractor Module
Handles data extraction from classified documents using templates
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class DataExtractor:
    """Extracts structured data from documents using predefined templates"""
    
    def __init__(self, config: Dict):
        """Initialize extractor with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.templates_folder = Path("templates")
        self.output_format = config['extraction']['output_format']
        
        # Ensure templates folder exists
        self.templates_folder.mkdir(exist_ok=True)
        
        # Load extraction templates
        self.templates = self._load_templates()
    
    def extract_data(self, file_path: Path, document_type: str) -> Dict[str, Any]:
        """
        Extract structured data from a document
        
        Args:
            file_path: Path to the classified document
            document_type: Type of document to extract from
            
        Returns:
            Extraction results with success status and extracted data
        """
        result = {
            'success': False,
            'file_path': str(file_path),
            'document_type': document_type,
            'extracted_data': {},
            'extraction_timestamp': datetime.now().isoformat(),
            'errors': []
        }
        
        try:
            # Get the template for this document type
            template = self.templates.get(document_type)
            if not template:
                result['errors'].append(f"No template found for document type: {document_type}")
                return result
            
            # Extract text content (reuse classifier's text extraction)
            from .document_classifier import DocumentClassifier
            classifier = DocumentClassifier(self.config)
            text_content = classifier._extract_text(file_path)
            
            if not text_content.strip():
                result['errors'].append("No text content could be extracted from document")
                return result
            
            # Extract data using template
            extracted_data = self._extract_using_template(text_content, template)
            
            result['extracted_data'] = extracted_data
            result['success'] = True
            
            # Save extraction results
            self._save_extraction_results(file_path, result)
            
            self.logger.info(f"Successfully extracted data from {file_path.name}")
            
        except Exception as e:
            error_msg = f"Error extracting data from {file_path}: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _load_templates(self) -> Dict[str, Dict]:
        """Load extraction templates for each document type"""
        templates = {}
        
        # Create default templates if they don't exist
        self._create_default_templates()
        
        # Load existing templates
        for doc_type, type_config in self.config['document_types'].items():
            template_file = type_config.get('template')
            if template_file:
                template_path = self.templates_folder / template_file
                if template_path.exists():
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            templates[doc_type] = json.load(f)
                        self.logger.debug(f"Loaded template for {doc_type}")
                    except Exception as e:
                        self.logger.error(f"Error loading template {template_file}: {str(e)}")
                else:
                    self.logger.warning(f"Template file not found: {template_path}")
        
        return templates
    
    def _create_default_templates(self):
        """Create default extraction templates"""
        default_templates = {
            "factura_template.json": {
                "name": "Factura Template",
                "description": "Template for invoice data extraction",
                "fields": {
                    "numero_factura": {
                        "patterns": [
                            r"(?:factura|invoice|bill)[\s#]*:?\s*([A-Z0-9\-\/]+)",
                            r"n[úu]mero[\s:]*([A-Z0-9\-\/]+)",
                            r"#\s*([A-Z0-9\-\/]+)"
                        ],
                        "type": "string",
                        "required": True
                    },
                    "fecha": {
                        "patterns": [
                            r"fecha[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                            r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                            r"date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
                        ],
                        "type": "date",
                        "required": True
                    },
                    "importe_total": {
                        "patterns": [
                            r"total[\s:]*([0-9,\.]+)[\s]*€?",
                            r"amount[\s:]*([0-9,\.]+)",
                            r"importe[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": True
                    },
                    "iva": {
                        "patterns": [
                            r"iva[\s:]*([0-9,\.]+)[\s]*%?",
                            r"vat[\s:]*([0-9,\.]+)",
                            r"tax[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": False
                    },
                    "proveedor": {
                        "patterns": [
                            r"de[\s:]*([A-Z][A-Za-z\s]+)",
                            r"supplier[\s:]*([A-Z][A-Za-z\s]+)",
                            r"from[\s:]*([A-Z][A-Za-z\s]+)"
                        ],
                        "type": "string",
                        "required": False
                    }
                }
            },
            "contrato_template.json": {
                "name": "Contrato Template",
                "description": "Template for contract data extraction",
                "fields": {
                    "tipo_contrato": {
                        "patterns": [
                            r"contrato\s+de\s+([A-Za-z\s]+)",
                            r"contract\s+of\s+([A-Za-z\s]+)",
                            r"agreement\s+for\s+([A-Za-z\s]+)"
                        ],
                        "type": "string",
                        "required": True
                    },
                    "fecha_inicio": {
                        "patterns": [
                            r"fecha\s+inicio[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                            r"start\s+date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
                        ],
                        "type": "date",
                        "required": True
                    },
                    "fecha_fin": {
                        "patterns": [
                            r"fecha\s+fin[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                            r"end\s+date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
                        ],
                        "type": "date",
                        "required": False
                    },
                    "partes": {
                        "patterns": [
                            r"entre\s+([A-Za-z\s,]+)\s+y\s+([A-Za-z\s,]+)",
                            r"between\s+([A-Za-z\s,]+)\s+and\s+([A-Za-z\s,]+)"
                        ],
                        "type": "array",
                        "required": True
                    }
                }
            },
            "nomina_template.json": {
                "name": "Nómina Template",
                "description": "Template for payroll data extraction",
                "fields": {
                    "empleado": {
                        "patterns": [
                            r"empleado[\s:]*([A-Za-z\s]+)",
                            r"employee[\s:]*([A-Za-z\s]+)",
                            r"worker[\s:]*([A-Za-z\s]+)"
                        ],
                        "type": "string",
                        "required": True
                    },
                    "periodo": {
                        "patterns": [
                            r"periodo[\s:]*([A-Za-z0-9\s\/\-]+)",
                            r"period[\s:]*([A-Za-z0-9\s\/\-]+)"
                        ],
                        "type": "string",
                        "required": True
                    },
                    "salario_bruto": {
                        "patterns": [
                            r"salario\s+bruto[\s:]*([0-9,\.]+)",
                            r"gross\s+salary[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": True
                    },
                    "deducciones": {
                        "patterns": [
                            r"deducciones[\s:]*([0-9,\.]+)",
                            r"deductions[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": False
                    },
                    "salario_neto": {
                        "patterns": [
                            r"salario\s+neto[\s:]*([0-9,\.]+)",
                            r"net\s+salary[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": True
                    }
                }
            },
            "balance_template.json": {
                "name": "Balance Template",
                "description": "Template for balance sheet data extraction",
                "fields": {
                    "fecha_balance": {
                        "patterns": [
                            r"balance\s+al[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                            r"as\s+of[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
                        ],
                        "type": "date",
                        "required": True
                    },
                    "activo_total": {
                        "patterns": [
                            r"activo\s+total[\s:]*([0-9,\.]+)",
                            r"total\s+assets[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": True
                    },
                    "pasivo_total": {
                        "patterns": [
                            r"pasivo\s+total[\s:]*([0-9,\.]+)",
                            r"total\s+liabilities[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": True
                    },
                    "patrimonio": {
                        "patterns": [
                            r"patrimonio[\s:]*([0-9,\.]+)",
                            r"equity[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": True
                    }
                }
            },
            "recibo_template.json": {
                "name": "Recibo Template",
                "description": "Template for receipt data extraction",
                "fields": {
                    "establecimiento": {
                        "patterns": [
                            r"^([A-Z][A-Za-z\s&\.]+)",
                            r"store[\s:]*([A-Za-z\s]+)"
                        ],
                        "type": "string",
                        "required": True
                    },
                    "fecha": {
                        "patterns": [
                            r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                            r"date[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
                        ],
                        "type": "date",
                        "required": True
                    },
                    "total": {
                        "patterns": [
                            r"total[\s:]*([0-9,\.]+)[\s]*€?",
                            r"amount[\s:]*([0-9,\.]+)"
                        ],
                        "type": "decimal",
                        "required": True
                    },
                    "metodo_pago": {
                        "patterns": [
                            r"(tarjeta|card|efectivo|cash|transferencia)",
                            r"payment[\s:]*([A-Za-z]+)"
                        ],
                        "type": "string",
                        "required": False
                    }
                }
            }
        }
        
        # Create template files
        for filename, template_data in default_templates.items():
            template_path = self.templates_folder / filename
            if not template_path.exists():
                try:
                    with open(template_path, 'w', encoding='utf-8') as f:
                        json.dump(template_data, f, indent=2, ensure_ascii=False)
                    self.logger.info(f"Created default template: {filename}")
                except Exception as e:
                    self.logger.error(f"Error creating template {filename}: {str(e)}")
    
    def _extract_using_template(self, text_content: str, template: Dict) -> Dict[str, Any]:
        """Extract data from text using a template"""
        extracted_data = {}
        text_lines = text_content.lower()
        
        fields = template.get('fields', {})
        
        for field_name, field_config in fields.items():
            patterns = field_config.get('patterns', [])
            field_type = field_config.get('type', 'string')
            is_required = field_config.get('required', False)
            
            extracted_value = None
            
            # Try each pattern until one matches
            for pattern in patterns:
                try:
                    match = re.search(pattern, text_lines, re.IGNORECASE | re.MULTILINE)
                    if match:
                        if field_type == 'array' and len(match.groups()) > 1:
                            extracted_value = list(match.groups())
                        else:
                            extracted_value = match.group(1).strip()
                        
                        # Convert to appropriate type
                        extracted_value = self._convert_value(extracted_value, field_type)
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error applying pattern {pattern}: {str(e)}")
            
            # Store the extracted value
            if extracted_value is not None:
                extracted_data[field_name] = extracted_value
            elif is_required:
                extracted_data[field_name] = None
                self.logger.warning(f"Required field '{field_name}' not found")
        
        return extracted_data
    
    def _convert_value(self, value: str, field_type: str) -> Any:
        """Convert extracted string value to appropriate type"""
        if value is None:
            return None
        
        try:
            if field_type == 'decimal':
                # Handle different decimal separators
                value = value.replace(',', '.')
                return float(re.sub(r'[^\d\.]', '', value))
            elif field_type == 'integer':
                return int(re.sub(r'[^\d]', '', value))
            elif field_type == 'date':
                # Basic date parsing (could be enhanced)
                return value.strip()
            elif field_type == 'array':
                if isinstance(value, list):
                    return [v.strip() for v in value]
                else:
                    return [value.strip()]
            else:  # string
                return value.strip()
        except Exception as e:
            self.logger.warning(f"Error converting value '{value}' to {field_type}: {str(e)}")
            return value
    
    def _save_extraction_results(self, file_path: Path, result: Dict[str, Any]):
        """Save extraction results to a file"""
        try:
            # Create extraction results folder
            results_folder = Path(self.config['output_folder']) / "extraction_results"
            results_folder.mkdir(exist_ok=True)
            
            # Generate results filename
            file_stem = file_path.stem
            results_filename = f"{file_stem}_extraction.json"
            results_path = results_folder / results_filename
            
            # Save results
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved extraction results to {results_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving extraction results: {str(e)}")
    
    def create_custom_template(self, document_type: str, template_data: Dict) -> bool:
        """Create a custom extraction template"""
        try:
            template_filename = f"{document_type}_template.json"
            template_path = self.templates_folder / template_filename
            
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            # Reload templates
            self.templates[document_type] = template_data
            
            self.logger.info(f"Created custom template for {document_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating custom template: {str(e)}")
            return False
    
    def get_available_templates(self) -> List[str]:
        """Get list of available templates"""
        return list(self.templates.keys())