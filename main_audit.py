#!/usr/bin/env python3
"""
Audit Document Processing System
Main application with priority loading for accounting core documents
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from colorama import init, Fore, Style

from src.document_classifier import DocumentClassifier
from src.folder_organizer import FolderOrganizer
from src.data_extractor import DataExtractor
from src.utils import setup_logging, load_config
from src.accounting_core import AccountingCoreProcessor
from src.bulk_loader import BulkDocumentLoader
from src.ai_processor import AIDocumentProcessor
from src.working_papers import WorkingPapersGenerator

# Initialize colorama
init(autoreset=True)


class AuditDocumentSystem:
    """Main audit document processing system"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the audit system"""
        self.config = load_config(config_path)
        self.logger = setup_logging()
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  SISTEMA DE PROCESAMIENTO DE DOCUMENTOS DE AUDITORÍA")
        print(f"{Fore.CYAN}{'='*60}\n")
        
        # Initialize core components
        self.logger.info("Initializing system components...")
        
        # Accounting core (PRIORITY)
        self.accounting = AccountingCoreProcessor(self.config)
        print(f"{Fore.GREEN}✓ Núcleo contable inicializado")
        
        # Document processors
        self.classifier = DocumentClassifier(self.config)
        self.organizer = FolderOrganizer(self.config)
        self.extractor = DataExtractor(self.config)
        print(f"{Fore.GREEN}✓ Procesadores de documentos inicializados")
        
        # AI processor
        self.ai_processor = AIDocumentProcessor(self.config)
        print(f"{Fore.GREEN}✓ Procesador de IA inicializado")
        
        # Bulk loader
        self.bulk_loader = BulkDocumentLoader(self.config)
        print(f"{Fore.GREEN}✓ Cargador masivo inicializado")
        
        # Working papers generator
        self.working_papers = WorkingPapersGenerator(self.config, self.accounting)
        print(f"{Fore.GREEN}✓ Generador de papeles de trabajo inicializado")
        
        # Setup directories
        self._setup_directories()
        
        print(f"\n{Fore.CYAN}Sistema listo para procesar documentos\n")
    
    def _setup_directories(self):
        """Create necessary directories"""
        directories = [
            Path(self.config['input_folder']),
            Path(self.config['output_folder']),
            Path(self.config['working_papers']['output_dir']),
            Path('logs'),
            Path('backup')
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
        
        # Create subfolders for each document type
        output_dir = Path(self.config['output_folder'])
        for doc_type in self.config['document_types'].keys():
            (output_dir / doc_type).mkdir(exist_ok=True)
    
    def load_accounting_core(self, accounting_files: Dict[int, Dict[str, Path]], company_info: Optional[Dict] = None):
        """
        PRIORITY: Load balance sheets and general ledgers first
        
        Args:
            accounting_files: Dictionary mapping year to {'balance': path, 'ledger': path}
            company_info: Company information
        """
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"{Fore.YELLOW}  FASE 1: CARGA DE DOCUMENTOS CONTABLES (PRIORITARIA)")
        print(f"{Fore.YELLOW}{'='*60}\n")
        
        self.logger.info("Starting priority loading of accounting core documents")
        
        # Load accounting data
        results = self.accounting.load_multiple_periods(accounting_files, company_info)
        
        # Display results
        print(f"\n{Fore.CYAN}Resumen de carga:")
        print(f"  Ejercicios procesados: {results['summary']['total_years']}")
        print(f"  {Fore.GREEN}Exitosos: {results['summary']['successful']}")
        print(f"  {Fore.RED}Fallidos: {results['summary']['failed']}")
        
        if results['errors']:
            print(f"\n{Fore.RED}Errores detectados:")
            for error in results['errors']:
                print(f"  - {error}")
        
        # Generate working papers for loaded periods
        print(f"\n{Fore.CYAN}Generando papeles de trabajo...")
        
        for period_result in results['periods']:
            year = period_result['year']
            if period_result['balance'] and period_result['balance']['status'] == 'success':
                wp_path = self.working_papers.generate_balance_analysis(year)
                if wp_path:
                    print(f"  {Fore.GREEN}✓ Papel de trabajo generado: {wp_path}")
        
        # Generate audit areas summary for current year
        if results['periods']:
            current_year = max(p['year'] for p in results['periods'])
            areas_path = self.working_papers.generate_audit_areas_summary(current_year)
            if areas_path:
                print(f"  {Fore.GREEN}✓ Resumen de áreas de auditoría: {areas_path}")
        
        print(f"\n{Fore.GREEN}✓ Documentos contables cargados correctamente")
        print(f"{Fore.CYAN}  Base de datos contable lista para consultas\n")
        
        return results
    
    def process_bulk_documents(self, directory: Path, recursive: bool = True):
        """
        PHASE 2: Process all other documents in bulk
        
        Args:
            directory: Directory containing documents
            recursive: Whether to scan subdirectories
        """
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"{Fore.YELLOW}  FASE 2: PROCESAMIENTO MASIVO DE DOCUMENTOS")
        print(f"{Fore.YELLOW}{'='*60}\n")
        
        self.logger.info(f"Starting bulk document processing from {directory}")
        
        def process_document(task):
            """Process a single document"""
            try:
                file_path = task.file_path
                
                # Classify document
                classification = self.classifier.classify_document(file_path)
                doc_type = classification['document_type']
                
                # Use AI classification if confidence is low
                if classification['confidence'] < 0.6:
                    # Extract text and use AI
                    text = self.classifier._extract_text(file_path)
                    if text:
                        ai_result = self.ai_processor.classify_with_ai(
                            text,
                            list(self.config['document_types'].keys())
                        )
                        if ai_result['confidence'] > classification['confidence']:
                            doc_type = ai_result['document_type']
                            classification.update(ai_result)
                
                # Organize document
                new_path = self.organizer.organize_document(file_path, doc_type)
                
                # Extract data
                extraction_result = None
                if doc_type != 'unknown':
                    extraction_result = self.extractor.extract_data(new_path, doc_type)
                
                return {
                    'status': 'success',
                    'file_path': str(file_path),
                    'document_type': doc_type,
                    'confidence': classification['confidence'],
                    'new_path': str(new_path),
                    'extraction': extraction_result
                }
                
            except Exception as e:
                self.logger.error(f"Failed to process {task.file_path}: {e}")
                return {
                    'status': 'error',
                    'file_path': str(task.file_path),
                    'error': str(e)
                }
        
        def progress_callback(processed, total, result):
            """Progress callback"""
            percentage = (processed / total) * 100
            print(f"\r{Fore.CYAN}Progreso: {processed}/{total} ({percentage:.1f}%) - "
                  f"Último: {Path(result['file_path']).name}", end='')
        
        # Process documents
        results = self.bulk_loader.load_documents_bulk(
            directory,
            process_document,
            progress_callback,
            recursive
        )
        
        print("\n")  # New line after progress
        
        # Display results
        summary = results['summary']
        print(f"\n{Fore.CYAN}Resumen de procesamiento:")
        print(f"  Total archivos: {summary['total_files']}")
        print(f"  {Fore.GREEN}Procesados: {summary['processed']}")
        print(f"  {Fore.RED}Fallidos: {summary['failed']}")
        print(f"  {Fore.YELLOW}Omitidos (duplicados): {summary['skipped']}")
        print(f"  Tamaño total: {summary['total_size_mb']:.2f} MB")
        print(f"  Duración: {summary['duration_seconds']:.2f} segundos")
        print(f"  Velocidad: {summary['documents_per_second']:.2f} docs/seg")
        
        # Document type distribution
        if results['completed']:
            type_counts = {}
            for result in results['completed']:
                doc_type = result.get('document_type', 'unknown')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            print(f"\n{Fore.CYAN}Distribución por tipo:")
            for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {doc_type}: {count}")
        
        print(f"\n{Fore.GREEN}✓ Procesamiento masivo completado\n")
        
        return results
    
    def query_account(self, account_code: str, year: Optional[int] = None):
        """Query account information"""
        print(f"\n{Fore.CYAN}Consultando cuenta {account_code}...")
        
        accounts = self.accounting.query_account(account_code, year)
        
        if not accounts:
            print(f"{Fore.RED}No se encontraron datos para la cuenta {account_code}")
            return
        
        print(f"\n{Fore.GREEN}Resultados:")
        for acc in accounts:
            print(f"\n  Cuenta: {acc['account_code']}")
            print(f"  Nombre: {acc['account_name']}")
            print(f"  Saldo Final: {acc['saldo_final']:,.2f} €")
            print(f"  Suma Debe: {acc['suma_debe']:,.2f} €")
            print(f"  Suma Haber: {acc['suma_haber']:,.2f} €")
    
    def generate_account_detail(self, account_code: str, year: int):
        """Generate detailed working paper for account"""
        print(f"\n{Fore.CYAN}Generando papel de trabajo para cuenta {account_code}...")
        
        wp_path = self.working_papers.generate_account_detail(account_code, year)
        
        if wp_path:
            print(f"{Fore.GREEN}✓ Papel de trabajo generado: {wp_path}")
        else:
            print(f"{Fore.RED}✗ No se pudo generar el papel de trabajo")
    
    def interactive_mode(self):
        """Interactive mode for queries"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  MODO INTERACTIVO")
        print(f"{Fore.CYAN}{'='*60}\n")
        print("Comandos disponibles:")
        print("  query <cuenta> [año]  - Consultar saldo de cuenta")
        print("  detail <cuenta> <año> - Generar papel de trabajo")
        print("  wp <año>              - Generar papeles de trabajo del año")
        print("  exit                  - Salir")
        
        while True:
            try:
                command = input(f"\n{Fore.YELLOW}> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd == 'exit':
                    break
                
                elif cmd == 'query':
                    if len(parts) < 2:
                        print(f"{Fore.RED}Uso: query <cuenta> [año]")
                        continue
                    account = parts[1]
                    year = int(parts[2]) if len(parts) > 2 else None
                    self.query_account(account, year)
                
                elif cmd == 'detail':
                    if len(parts) < 3:
                        print(f"{Fore.RED}Uso: detail <cuenta> <año>")
                        continue
                    account = parts[1]
                    year = int(parts[2])
                    self.generate_account_detail(account, year)
                
                elif cmd == 'wp':
                    if len(parts) < 2:
                        print(f"{Fore.RED}Uso: wp <año>")
                        continue
                    year = int(parts[1])
                    wp_path = self.working_papers.generate_balance_analysis(year)
                    if wp_path:
                        print(f"{Fore.GREEN}✓ Papeles generados: {wp_path}")
                
                else:
                    print(f"{Fore.RED}Comando desconocido: {cmd}")
            
            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Sistema de Procesamiento de Documentos de Auditoría'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Ruta al archivo de configuración'
    )
    parser.add_argument(
        '--load-accounting',
        action='store_true',
        help='Cargar balances y diarios (modo prioritario)'
    )
    parser.add_argument(
        '--process-bulk',
        action='store_true',
        help='Procesar documentos masivamente'
    )
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Modo interactivo'
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        default='./input_documents',
        help='Directorio de entrada'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        system = AuditDocumentSystem(args.config)
        
        if args.load_accounting:
            # Example: Load accounting files
            # User should provide proper file paths
            print(f"\n{Fore.YELLOW}Para cargar documentos contables, proporcione:")
            print("  - Balances de sumas y saldos (Excel)")
            print("  - Diarios contables (Excel)")
            print("  - Para los últimos 3 ejercicios (o el ejercicio a auditar)\n")
            
            # This should be configured by the user
            # Example structure:
            # accounting_files = {
            #     2023: {
            #         'balance': Path('balances/balance_2023.xlsx'),
            #         'ledger': Path('diarios/diario_2023.xlsx')
            #     },
            #     2022: {
            #         'balance': Path('balances/balance_2022.xlsx'),
            #         'ledger': Path('diarios/diario_2022.xlsx')
            #     }
            # }
            # system.load_accounting_core(accounting_files)
        
        if args.process_bulk:
            system.process_bulk_documents(args.input_dir)
        
        if args.interactive:
            system.interactive_mode()
        
        if not (args.load_accounting or args.process_bulk or args.interactive):
            # Default: process all
            print(f"\n{Fore.YELLOW}Modo por defecto: Procesamiento completo")
            print("Para opciones específicas, use --help\n")
            
            # Load accounting first if files are available
            # Then process other documents
            system.process_bulk_documents(args.input_dir)
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Error fatal: {e}")
        logging.exception("Fatal error")
        sys.exit(1)


if __name__ == '__main__':
    main()
