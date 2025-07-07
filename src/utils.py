"""
Utilities Module
Common utilities and helper functions
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {str(e)}")


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Default log file
    if log_file is None:
        log_file = logs_dir / "document_agent.log"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Get logger
    logger = logging.getLogger("DocumentAgent")
    logger.info("Logging initialized")
    
    return logger


def ensure_directory(path: str) -> Path:
    """Ensure directory exists and return Path object"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def is_supported_file(file_path: Path, supported_extensions: list = None) -> bool:
    """Check if file extension is supported"""
    if supported_extensions is None:
        supported_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', 
                              '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.txt']
    
    return file_path.suffix.lower() in supported_extensions


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations"""
    import re
    
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
    sanitized = sanitized.strip('.')  # Remove leading/trailing dots
    
    # Ensure filename is not too long
    max_length = 200
    if len(sanitized) > max_length:
        name_part, ext_part = os.path.splitext(sanitized)
        sanitized = name_part[:max_length - len(ext_part)] + ext_part
    
    return sanitized


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def create_summary_report(stats: Dict[str, Any], output_path: str = None) -> str:
    """Create a summary report of processing results"""
    if output_path is None:
        output_path = "logs/processing_summary.txt"
    
    report_lines = [
        "=" * 50,
        "DOCUMENT CLASSIFICATION SUMMARY REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "PROCESSING STATISTICS:",
        f"- Total files processed: {stats.get('processed', 0)}",
        f"- Successfully classified: {stats.get('classified', 0)}",
        f"- Data extracted: {stats.get('extracted', 0)}",
        f"- Errors encountered: {stats.get('errors', 0)}",
        "",
    ]
    
    # Add folder statistics if available
    if 'folder_stats' in stats:
        report_lines.append("FOLDER DISTRIBUTION:")
        for doc_type, folder_info in stats['folder_stats'].items():
            count = folder_info.get('count', 0)
            size_mb = folder_info.get('total_size_mb', 0)
            report_lines.append(f"- {doc_type.capitalize()}: {count} files ({size_mb:.1f} MB)")
        report_lines.append("")
    
    report_lines.extend([
        "=" * 50,
        ""
    ])
    
    report_content = "\n".join(report_lines)
    
    try:
        ensure_directory(Path(output_path).parent)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating summary report: {str(e)}")
    
    return report_content


# Import datetime for report generation
from datetime import datetime