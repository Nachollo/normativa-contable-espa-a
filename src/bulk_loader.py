"""
Bulk Document Loader Module
Handles massive document uploads with parallel processing and queue management
"""

import os
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, PriorityQueue
from threading import Lock
import time
from dataclasses import dataclass, field
from datetime import datetime
import json

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


@dataclass(order=True)
class DocumentTask:
    """Represents a document processing task"""
    priority: int
    file_path: Path = field(compare=False)
    file_size: int = field(compare=False)
    file_hash: str = field(compare=False)
    timestamp: datetime = field(default_factory=datetime.now, compare=False)
    retry_count: int = field(default=0, compare=False)
    metadata: Dict = field(default_factory=dict, compare=False)


class BulkDocumentLoader:
    """Handles bulk document loading and processing with queue management"""
    
    def __init__(self, config: Dict):
        """Initialize bulk loader"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Processing configuration
        self.max_workers = config.get('processing', {}).get('max_workers', 8)
        self.batch_size = config.get('processing', {}).get('batch_size', 100)
        self.max_retries = config.get('processing', {}).get('max_retries', 3)
        self.chunk_size = config.get('processing', {}).get('chunk_size_mb', 100) * 1024 * 1024
        
        # Supported extensions
        self.supported_extensions = self._get_all_supported_extensions()
        
        # Processing queues
        self.task_queue = PriorityQueue()
        self.completed = []
        self.failed = []
        self.lock = Lock()
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'total_size': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Deduplication cache
        self.file_hashes = set()
        self.hash_to_path = {}
    
    def _get_all_supported_extensions(self) -> set:
        """Get all supported file extensions"""
        extensions = {
            # Documents
            '.pdf', '.txt', '.rtf',
            # Microsoft Office
            '.doc', '.docx', '.docm', '.dot', '.dotx',
            '.xls', '.xlsx', '.xlsm', '.xlsb', '.xlt', '.xltx',
            '.ppt', '.pptx', '.pptm', '.pps', '.ppsx',
            # LibreOffice/OpenOffice
            '.odt', '.ods', '.odp', '.odg', '.odf',
            # Images
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif',
            # Email
            '.msg', '.eml',
            # Data
            '.csv', '.tsv', '.json', '.xml',
            # Google formats (exported versions)
            '.gdoc', '.gsheet', '.gslides'
        }
        
        # Add extensions from config
        for doc_type in self.config.get('document_types', {}).values():
            extensions.update(doc_type.get('extensions', []))
        
        return extensions
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Path]:
        """
        Scan directory for supported documents
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of document paths
        """
        self.logger.info(f"Scanning directory: {directory}")
        documents = []
        
        if recursive:
            pattern = '**/*'
        else:
            pattern = '*'
        
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                if file_path.suffix.lower() in self.supported_extensions:
                    documents.append(file_path)
        
        self.logger.info(f"Found {len(documents)} supported documents")
        return documents
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file for deduplication"""
        md5_hash = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash {file_path}: {e}")
            return ""
    
    def is_duplicate(self, file_path: Path) -> bool:
        """Check if file is a duplicate based on hash"""
        file_hash = self.calculate_file_hash(file_path)
        
        if file_hash in self.file_hashes:
            self.logger.info(f"Duplicate file detected: {file_path} (same as {self.hash_to_path.get(file_hash)})")
            return True
        
        self.file_hashes.add(file_hash)
        self.hash_to_path[file_hash] = str(file_path)
        return False
    
    def create_tasks(self, file_paths: List[Path], priority: int = 5) -> List[DocumentTask]:
        """
        Create processing tasks from file paths
        
        Args:
            file_paths: List of file paths
            priority: Task priority (1=highest, 10=lowest)
            
        Returns:
            List of DocumentTask objects
        """
        tasks = []
        
        for file_path in file_paths:
            try:
                # Check for duplicates
                if self.is_duplicate(file_path):
                    self.stats['skipped'] += 1
                    continue
                
                # Get file info
                file_size = file_path.stat().st_size
                file_hash = self.calculate_file_hash(file_path)
                
                # Create task
                task = DocumentTask(
                    priority=priority,
                    file_path=file_path,
                    file_size=file_size,
                    file_hash=file_hash,
                    metadata={
                        'extension': file_path.suffix.lower(),
                        'filename': file_path.name
                    }
                )
                
                tasks.append(task)
                self.stats['total_files'] += 1
                self.stats['total_size'] += file_size
                
            except Exception as e:
                self.logger.error(f"Failed to create task for {file_path}: {e}")
        
        return tasks
    
    def enqueue_tasks(self, tasks: List[DocumentTask]):
        """Add tasks to processing queue"""
        for task in tasks:
            self.task_queue.put(task)
        
        self.logger.info(f"Enqueued {len(tasks)} tasks")
    
    def load_documents_bulk(
        self,
        directory: Path,
        processor_callback: Callable[[DocumentTask], Dict[str, Any]],
        progress_callback: Optional[Callable] = None,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Load and process documents in bulk
        
        Args:
            directory: Directory containing documents
            processor_callback: Function to process each document
            progress_callback: Optional progress callback
            recursive: Whether to scan subdirectories
            
        Returns:
            Processing results and statistics
        """
        self.stats['start_time'] = datetime.now()
        
        # Scan directory
        file_paths = self.scan_directory(directory, recursive)
        
        if not file_paths:
            self.logger.warning("No documents found to process")
            return self._generate_report()
        
        # Create tasks
        tasks = self.create_tasks(file_paths)
        
        # Enqueue tasks
        self.enqueue_tasks(tasks)
        
        # Process tasks in parallel
        self._process_queue(processor_callback, progress_callback)
        
        self.stats['end_time'] = datetime.now()
        
        return self._generate_report()
    
    def _process_queue(
        self,
        processor_callback: Callable[[DocumentTask], Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ):
        """Process tasks from queue using thread pool"""
        total_tasks = self.task_queue.qsize()
        
        # Setup progress bar if available
        if tqdm:
            pbar = tqdm(total=total_tasks, desc="Processing documents", unit="doc")
        else:
            pbar = None
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit initial batch
            futures = {}
            
            while not self.task_queue.empty() or futures:
                # Submit new tasks up to max workers
                while len(futures) < self.max_workers and not self.task_queue.empty():
                    task = self.task_queue.get()
                    future = executor.submit(self._process_task, task, processor_callback)
                    futures[future] = task
                
                # Process completed tasks
                if futures:
                    done, pending = as_completed(futures.keys(), timeout=1), set()
                    
                    for future in done:
                        task = futures.pop(future)
                        
                        try:
                            result = future.result()
                            
                            with self.lock:
                                if result.get('status') == 'success':
                                    self.completed.append(result)
                                    self.stats['processed'] += 1
                                else:
                                    # Retry logic
                                    if task.retry_count < self.max_retries:
                                        task.retry_count += 1
                                        task.priority += 1  # Lower priority for retries
                                        self.task_queue.put(task)
                                        self.logger.info(f"Retrying {task.file_path} (attempt {task.retry_count})")
                                    else:
                                        self.failed.append(result)
                                        self.stats['failed'] += 1
                                
                                if pbar:
                                    pbar.update(1)
                                
                                if progress_callback:
                                    progress_callback(
                                        self.stats['processed'],
                                        total_tasks,
                                        result
                                    )
                        
                        except Exception as e:
                            self.logger.error(f"Task processing error: {e}")
                            with self.lock:
                                self.stats['failed'] += 1
                                if pbar:
                                    pbar.update(1)
        
        if pbar:
            pbar.close()
    
    def _process_task(
        self,
        task: DocumentTask,
        processor_callback: Callable[[DocumentTask], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a single task"""
        try:
            self.logger.debug(f"Processing: {task.file_path}")
            
            # Call the processor callback
            result = processor_callback(task)
            
            # Add task metadata to result
            result['task'] = {
                'file_path': str(task.file_path),
                'file_size': task.file_size,
                'file_hash': task.file_hash,
                'retry_count': task.retry_count,
                'timestamp': task.timestamp.isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process {task.file_path}: {e}")
            return {
                'status': 'error',
                'file_path': str(task.file_path),
                'error': str(e)
            }
    
    def load_from_multiple_sources(
        self,
        directories: List[Path],
        processor_callback: Callable[[DocumentTask], Dict[str, Any]],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Load documents from multiple directories
        
        Args:
            directories: List of directories to scan
            processor_callback: Function to process each document
            progress_callback: Optional progress callback
            
        Returns:
            Combined processing results
        """
        all_files = []
        
        for directory in directories:
            if directory.exists():
                files = self.scan_directory(directory, recursive=True)
                all_files.extend(files)
                self.logger.info(f"Found {len(files)} files in {directory}")
        
        if not all_files:
            self.logger.warning("No documents found in any directory")
            return self._generate_report()
        
        # Create and enqueue tasks
        tasks = self.create_tasks(all_files)
        self.enqueue_tasks(tasks)
        
        # Process
        self.stats['start_time'] = datetime.now()
        self._process_queue(processor_callback, progress_callback)
        self.stats['end_time'] = datetime.now()
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate processing report"""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            docs_per_second = self.stats['processed'] / duration if duration > 0 else 0
        else:
            duration = 0
            docs_per_second = 0
        
        report = {
            'summary': {
                'total_files': self.stats['total_files'],
                'processed': self.stats['processed'],
                'failed': self.stats['failed'],
                'skipped': self.stats['skipped'],
                'total_size_bytes': self.stats['total_size'],
                'total_size_mb': self.stats['total_size'] / (1024 * 1024),
                'duration_seconds': duration,
                'documents_per_second': docs_per_second
            },
            'completed': self.completed,
            'failed': self.failed,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report to file
        report_path = Path('logs') / f'bulk_load_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Processing report saved to {report_path}")
        
        return report
    
    def prioritize_by_size(self, tasks: List[DocumentTask]) -> List[DocumentTask]:
        """Sort tasks by size (process smaller files first for quick wins)"""
        return sorted(tasks, key=lambda t: t.file_size)
    
    def prioritize_by_type(self, tasks: List[DocumentTask], priority_types: List[str]) -> List[DocumentTask]:
        """Sort tasks by file type priority"""
        def get_priority(task):
            ext = task.metadata.get('extension', '')
            try:
                return priority_types.index(ext)
            except ValueError:
                return len(priority_types)
        
        return sorted(tasks, key=get_priority)
