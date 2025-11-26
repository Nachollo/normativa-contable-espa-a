#!/usr/bin/env python3
"""
Document Classification Agent
Main application for classifying and organizing documents
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional

from src.document_classifier import DocumentClassifier
from src.folder_organizer import FolderOrganizer
from src.data_extractor import DataExtractor
from src.utils import setup_logging, load_config


class DocumentAgent:
    """Main document classification and organization agent"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the document agent with configuration"""
        self.config = load_config(config_path)
        self.logger = setup_logging()
        
        # Initialize components
        self.classifier = DocumentClassifier(self.config)
        self.organizer = FolderOrganizer(self.config)
        self.extractor = DataExtractor(self.config)
        
        # Ensure directories exist
        self._setup_directories()
    
    def _setup_directories(self):
        """Create necessary directories if they don't exist"""
        input_dir = Path(self.config['input_folder'])
        output_dir = Path(self.config['output_folder'])
        
        input_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)
        
        # Create subfolders for each document type
        for doc_type in self.config['document_types'].keys():
            (output_dir / doc_type).mkdir(exist_ok=True)
        
        # Create unknown documents folder
        unknown_folder = self.config['classification']['unknown_folder']
        (output_dir / unknown_folder).mkdir(exist_ok=True)
        
        self.logger.info(f"Directories setup complete: {input_dir} -> {output_dir}")
    
    def process_documents(self, watch_mode: bool = False) -> Dict[str, int]:
        """
        Process all documents in the input folder
        
        Args:
            watch_mode: If True, continuously watch for new files
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'processed': 0,
            'classified': 0,
            'extracted': 0,
            'errors': 0
        }
        
        input_path = Path(self.config['input_folder'])
        
        if watch_mode:
            self.logger.info("Starting watch mode...")
            self._watch_folder(input_path, stats)
        else:
            self._process_folder(input_path, stats)
        
        return stats
    
    def _process_folder(self, folder_path: Path, stats: Dict[str, int]):
        """Process all files in a folder"""
        if not folder_path.exists():
            self.logger.error(f"Input folder does not exist: {folder_path}")
            return
        
        # Get all files to process
        files_to_process = []
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                files_to_process.append(file_path)
        
        self.logger.info(f"Found {len(files_to_process)} files to process")
        
        # Process each file
        for file_path in files_to_process:
            try:
                self._process_single_file(file_path, stats)
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {str(e)}")
                stats['errors'] += 1
    
    def _process_single_file(self, file_path: Path, stats: Dict[str, int]):
        """Process a single document file"""
        self.logger.info(f"Processing: {file_path.name}")
        
        # Step 1: Classify the document
        classification_result = self.classifier.classify_document(file_path)
        stats['processed'] += 1
        
        if classification_result['document_type'] != 'unknown':
            stats['classified'] += 1
            
            # Step 2: Move document to appropriate folder
            new_path = self.organizer.organize_document(
                file_path, classification_result['document_type']
            )
            
            # Step 3: Extract data from the document
            if new_path and new_path.exists():
                extraction_result = self.extractor.extract_data(
                    new_path, classification_result['document_type']
                )
                
                if extraction_result['success']:
                    stats['extracted'] += 1
                    self.logger.info(f"Successfully processed: {file_path.name}")
                else:
                    self.logger.warning(f"Failed to extract data from: {file_path.name}")
            else:
                self.logger.error(f"Failed to move document: {file_path.name}")
        else:
            # Move to unknown folder
            self.organizer.organize_document(file_path, 'unknown')
            self.logger.warning(f"Could not classify: {file_path.name}")
    
    def _watch_folder(self, folder_path: Path, stats: Dict[str, int]):
        """Watch folder for new files and process them automatically"""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class DocumentHandler(FileSystemEventHandler):
            def __init__(self, agent):
                self.agent = agent
            
            def on_created(self, event):
                if not event.is_directory:
                    file_path = Path(event.src_path)
                    if not file_path.name.startswith('.'):
                        try:
                            self.agent._process_single_file(file_path, stats)
                        except Exception as e:
                            self.agent.logger.error(f"Error processing {file_path}: {str(e)}")
                            stats['errors'] += 1
        
        event_handler = DocumentHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(folder_path), recursive=True)
        observer.start()
        
        try:
            self.logger.info(f"Watching folder: {folder_path}")
            observer.join()
        except KeyboardInterrupt:
            observer.stop()
            self.logger.info("Watch mode stopped by user")
        observer.join()
    
    def get_statistics(self) -> Dict[str, any]:
        """Get processing statistics and folder contents"""
        output_path = Path(self.config['output_folder'])
        stats = {}
        
        for doc_type in self.config['document_types'].keys():
            folder_path = output_path / doc_type
            if folder_path.exists():
                file_count = len(list(folder_path.glob('*')))
                stats[doc_type] = file_count
        
        # Count unknown documents
        unknown_folder = self.config['classification']['unknown_folder']
        unknown_path = output_path / unknown_folder
        if unknown_path.exists():
            stats['unknown'] = len(list(unknown_path.glob('*')))
        
        return stats


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Document Classification Agent')
    parser.add_argument('--config', default='config.json', 
                       help='Configuration file path')
    parser.add_argument('--watch', action='store_true',
                       help='Watch input folder for new files')
    parser.add_argument('--stats', action='store_true',
                       help='Show current statistics')
    
    args = parser.parse_args()
    
    try:
        agent = DocumentAgent(args.config)
        
        if args.stats:
            stats = agent.get_statistics()
            print("\n=== Document Classification Statistics ===")
            for doc_type, count in stats.items():
                print(f"{doc_type.capitalize()}: {count} documents")
            print("==========================================\n")
        else:
            print("Starting Document Classification Agent...")
            results = agent.process_documents(watch_mode=args.watch)
            
            print("\n=== Processing Results ===")
            print(f"Processed: {results['processed']} documents")
            print(f"Classified: {results['classified']} documents")
            print(f"Data Extracted: {results['extracted']} documents")
            print(f"Errors: {results['errors']} documents")
            print("==========================\n")
            
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()