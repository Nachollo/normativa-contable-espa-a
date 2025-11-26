"""
Folder Organizer Module
Handles document organization and folder management
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class FolderOrganizer:
    """Organizes documents into appropriate folders based on classification"""
    
    def __init__(self, config: Dict):
        """Initialize organizer with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.output_folder = Path(config['output_folder'])
        self.backup_folder = Path(config['classification']['backup_folder'])
        self.unknown_folder = config['classification']['unknown_folder']
        
        # Create backup folder if it doesn't exist
        self.backup_folder.mkdir(exist_ok=True)
    
    def organize_document(self, file_path: Path, document_type: str) -> Optional[Path]:
        """
        Move document to appropriate folder based on its type
        
        Args:
            file_path: Source file path
            document_type: Classified document type
            
        Returns:
            New file path if successful, None otherwise
        """
        try:
            # Determine target folder
            if document_type == 'unknown':
                target_folder = self.output_folder / self.unknown_folder
            else:
                target_folder = self.output_folder / document_type
            
            # Ensure target folder exists
            target_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename if file already exists
            new_file_path = self._get_unique_path(target_folder, file_path.name)
            
            # Create backup before moving
            backup_path = self._backup_file(file_path)
            
            # Move the file
            shutil.move(str(file_path), str(new_file_path))
            
            self.logger.info(f"Moved {file_path.name} to {new_file_path}")
            
            # Log the organization action
            self._log_organization(file_path, new_file_path, document_type, backup_path)
            
            return new_file_path
            
        except Exception as e:
            self.logger.error(f"Error organizing {file_path}: {str(e)}")
            return None
    
    def _get_unique_path(self, folder: Path, filename: str) -> Path:
        """Generate a unique file path to avoid conflicts"""
        base_path = folder / filename
        
        if not base_path.exists():
            return base_path
        
        # File exists, add timestamp suffix
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            name, extension = name_parts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{name}_{timestamp}.{extension}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{filename}_{timestamp}"
        
        return folder / new_filename
    
    def _backup_file(self, file_path: Path) -> Optional[Path]:
        """Create a backup copy of the file before moving"""
        try:
            # Create date-based backup subfolder
            backup_date = datetime.now().strftime("%Y-%m-%d")
            date_backup_folder = self.backup_folder / backup_date
            date_backup_folder.mkdir(parents=True, exist_ok=True)
            
            # Generate unique backup path
            backup_path = self._get_unique_path(date_backup_folder, file_path.name)
            
            # Copy file to backup
            shutil.copy2(str(file_path), str(backup_path))
            
            self.logger.debug(f"Backed up {file_path.name} to {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.warning(f"Could not backup {file_path}: {str(e)}")
            return None
    
    def _log_organization(self, original_path: Path, new_path: Path, 
                         document_type: str, backup_path: Optional[Path]):
        """Log organization action to a file"""
        try:
            log_file = self.output_folder / "organization_log.txt"
            timestamp = datetime.now().isoformat()
            
            log_entry = (
                f"{timestamp} | "
                f"Original: {original_path} | "
                f"New: {new_path} | "
                f"Type: {document_type} | "
                f"Backup: {backup_path or 'None'}\n"
            )
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            self.logger.warning(f"Could not write organization log: {str(e)}")
    
    def create_folder_structure(self) -> bool:
        """Create the complete folder structure for document organization"""
        try:
            # Create main output folder
            self.output_folder.mkdir(parents=True, exist_ok=True)
            
            # Create folders for each document type
            for doc_type in self.config['document_types'].keys():
                type_folder = self.output_folder / doc_type
                type_folder.mkdir(exist_ok=True)
                self.logger.debug(f"Created folder: {type_folder}")
            
            # Create unknown documents folder
            unknown_folder = self.output_folder / self.unknown_folder
            unknown_folder.mkdir(exist_ok=True)
            
            # Create backup folder
            self.backup_folder.mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Folder structure created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating folder structure: {str(e)}")
            return False
    
    def get_folder_statistics(self) -> Dict[str, Dict[str, any]]:
        """Get statistics about organized documents"""
        stats = {}
        
        try:
            # Stats for each document type
            for doc_type in self.config['document_types'].keys():
                type_folder = self.output_folder / doc_type
                if type_folder.exists():
                    files = list(type_folder.glob('*'))
                    total_size = sum(f.stat().st_size for f in files if f.is_file())
                    
                    stats[doc_type] = {
                        'count': len([f for f in files if f.is_file()]),
                        'total_size_mb': total_size / (1024 * 1024),
                        'folder_path': str(type_folder)
                    }
                else:
                    stats[doc_type] = {
                        'count': 0,
                        'total_size_mb': 0,
                        'folder_path': str(type_folder)
                    }
            
            # Stats for unknown documents
            unknown_folder = self.output_folder / self.unknown_folder
            if unknown_folder.exists():
                files = list(unknown_folder.glob('*'))
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                
                stats['unknown'] = {
                    'count': len([f for f in files if f.is_file()]),
                    'total_size_mb': total_size / (1024 * 1024),
                    'folder_path': str(unknown_folder)
                }
            
        except Exception as e:
            self.logger.error(f"Error getting folder statistics: {str(e)}")
        
        return stats
    
    def restore_from_backup(self, backup_date: str = None) -> bool:
        """
        Restore files from backup
        
        Args:
            backup_date: Date string (YYYY-MM-DD) or None for today
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if backup_date is None:
                backup_date = datetime.now().strftime("%Y-%m-%d")
            
            backup_source = self.backup_folder / backup_date
            
            if not backup_source.exists():
                self.logger.error(f"Backup folder not found: {backup_source}")
                return False
            
            # List available backups
            backup_files = list(backup_source.glob('*'))
            self.logger.info(f"Found {len(backup_files)} files in backup {backup_date}")
            
            # Note: This is a basic implementation
            # In practice, you might want more sophisticated restore logic
            for backup_file in backup_files:
                if backup_file.is_file():
                    self.logger.info(f"Backup available: {backup_file.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during restore: {str(e)}")
            return False
    
    def cleanup_empty_folders(self) -> int:
        """Remove empty folders and return count of removed folders"""
        removed_count = 0
        
        try:
            for folder_path in self.output_folder.rglob('*'):
                if folder_path.is_dir() and not any(folder_path.iterdir()):
                    folder_path.rmdir()
                    removed_count += 1
                    self.logger.debug(f"Removed empty folder: {folder_path}")
            
            self.logger.info(f"Cleaned up {removed_count} empty folders")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
        
        return removed_count