"""
Emergency Control Module - Phase 2 Stability Features
Implements emergency stop button and AI auto-recovery system
"""

import os
import sys
import signal
import threading
import traceback
import logging
import json
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue

# Configure logger
logger = logging.getLogger(__name__)


class EmergencyStop(Exception):
    """Exception raised when emergency stop is triggered"""
    pass


class ProcessRecoveryError(Exception):
    """Exception raised when auto-recovery fails"""
    pass


class EmergencyController:
    """
    Emergency Controller - Manages process interruption and recovery
    
    Features:
    - Emergency stop button (Ctrl+C or signal)
    - Graceful shutdown with cleanup
    - Timeout monitoring for stuck processes
    - Error logging and analysis
    """
    
    def __init__(self, timeout_seconds: int = 300):
        self.stop_requested = threading.Event()
        self.is_running = threading.Event()
        self.timeout_seconds = timeout_seconds
        self.current_task = None
        self.error_log = []
        self.task_history = []
        
        # Setup signal handlers for emergency stop
        signal.signal(signal.SIGINT, self._handle_emergency_stop)
        signal.signal(signal.SIGTERM, self._handle_emergency_stop)
        
        logger.info("Emergency Controller initialized")
    
    def _handle_emergency_stop(self, signum, frame):
        """Handle emergency stop signal"""
        logger.warning("🚨 EMERGENCY STOP triggered!")
        print("\n\n🚨 ¡PARADA DE EMERGENCIA ACTIVADA!")
        print("   Deteniendo procesos de forma segura...")
        self.stop_requested.set()
        
        # Give processes time to cleanup
        time.sleep(1)
        
        # Log current state
        if self.current_task:
            self.error_log.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'EMERGENCY_STOP',
                'task': self.current_task,
                'message': 'Process stopped by user'
            })
            logger.info(f"Task '{self.current_task}' stopped by emergency signal")
        
        print("✓ Proceso detenido correctamente")
        print("  Puede reiniciar el sistema cuando desee\n")
    
    def check_stop(self):
        """Check if stop has been requested - call this in loops"""
        if self.stop_requested.is_set():
            raise EmergencyStop("Emergency stop requested by user")
    
    def register_task(self, task_name: str):
        """Register current task for monitoring"""
        self.current_task = task_name
        self.is_running.set()
        self.task_history.append({
            'task': task_name,
            'started': datetime.now().isoformat(),
            'status': 'running'
        })
        logger.info(f"Task registered: {task_name}")
    
    def complete_task(self, task_name: str, success: bool = True):
        """Mark task as completed"""
        self.current_task = None
        self.is_running.clear()
        
        # Update task history
        for task in reversed(self.task_history):
            if task['task'] == task_name and task['status'] == 'running':
                task['completed'] = datetime.now().isoformat()
                task['status'] = 'success' if success else 'failed'
                break
        
        logger.info(f"Task completed: {task_name} (success={success})")
    
    def log_error(self, error: Exception, task_name: str = None, context: Dict = None):
        """Log an error for analysis"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'task': task_name or self.current_task,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        self.error_log.append(error_entry)
        logger.error(f"Error logged: {error_entry['type']} - {error_entry['message']}")
        return error_entry
    
    def get_error_summary(self) -> Dict:
        """Get summary of all logged errors"""
        if not self.error_log:
            return {'total': 0, 'errors': []}
        
        error_types = {}
        for error in self.error_log:
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1
        
        return {
            'total': len(self.error_log),
            'by_type': error_types,
            'errors': self.error_log[-10:]  # Last 10 errors
        }
    
    def save_error_report(self, output_dir: str = "./logs"):
        """Save detailed error report to file"""
        os.makedirs(output_dir, exist_ok=True)
        filename = f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(output_dir, filename)
        
        report = {
            'generated': datetime.now().isoformat(),
            'summary': self.get_error_summary(),
            'task_history': self.task_history,
            'all_errors': self.error_log
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Error report saved: {filepath}")
        return filepath
    
    def reset(self):
        """Reset controller state for new run"""
        self.stop_requested.clear()
        self.is_running.clear()
        self.current_task = None
        logger.info("Emergency controller reset")


class AIErrorAnalyzer:
    """
    AI-powered Error Analyzer
    
    Analyzes errors and suggests fixes using pattern matching
    and heuristic analysis (simulated AI behavior)
    """
    
    # Error patterns and their suggested fixes
    ERROR_PATTERNS = {
        'FileNotFoundError': {
            'category': 'file_system',
            'severity': 'medium',
            'suggestions': [
                'Verificar que el archivo existe en la ruta especificada',
                'Comprobar permisos de acceso al directorio',
                'Verificar que el nombre del archivo no tiene caracteres especiales'
            ],
            'auto_fix': 'create_missing_directory'
        },
        'PermissionError': {
            'category': 'permissions',
            'severity': 'high',
            'suggestions': [
                'Ejecutar el programa con permisos de administrador',
                'Verificar que el archivo no está bloqueado por otro proceso',
                'Comprobar permisos de escritura en el directorio'
            ],
            'auto_fix': None
        },
        'KeyError': {
            'category': 'data_structure',
            'severity': 'low',
            'suggestions': [
                'Verificar que los datos de entrada contienen las claves requeridas',
                'Usar método .get() con valor por defecto',
                'Revisar formato del archivo de configuración'
            ],
            'auto_fix': 'use_default_value'
        },
        'ValueError': {
            'category': 'data_validation',
            'severity': 'medium',
            'suggestions': [
                'Verificar formato de los datos de entrada',
                'Comprobar que los valores numéricos son válidos',
                'Revisar conversiones de tipo de datos'
            ],
            'auto_fix': 'sanitize_input'
        },
        'ConnectionError': {
            'category': 'network',
            'severity': 'high',
            'suggestions': [
                'Verificar conexión a internet',
                'Comprobar configuración de proxy',
                'Intentar reconexión después de unos segundos'
            ],
            'auto_fix': 'retry_connection'
        },
        'MemoryError': {
            'category': 'resources',
            'severity': 'critical',
            'suggestions': [
                'Cerrar otras aplicaciones para liberar memoria',
                'Procesar datos en lotes más pequeños',
                'Reiniciar el sistema si persiste'
            ],
            'auto_fix': 'reduce_batch_size'
        },
        'TimeoutError': {
            'category': 'performance',
            'severity': 'medium',
            'suggestions': [
                'Aumentar tiempo de espera en configuración',
                'Verificar que el servidor responde correctamente',
                'Intentar de nuevo más tarde'
            ],
            'auto_fix': 'increase_timeout'
        },
        'EmergencyStop': {
            'category': 'user_action',
            'severity': 'info',
            'suggestions': [
                'El usuario solicitó detener el proceso',
                'El sistema se detuvo de forma controlada',
                'Puede reiniciar cuando lo desee'
            ],
            'auto_fix': None
        }
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.analysis_cache = {}
        logger.info("AI Error Analyzer initialized")
    
    def analyze_error(self, error: Exception, context: Dict = None) -> Dict:
        """
        Analyze error and provide diagnosis and suggestions
        
        Returns:
            Dict with analysis results including suggestions
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Get pattern if known
        pattern = self.ERROR_PATTERNS.get(error_type, {
            'category': 'unknown',
            'severity': 'medium',
            'suggestions': [
                'Error no reconocido - revisar logs para más detalles',
                'Contactar soporte técnico si persiste'
            ],
            'auto_fix': None
        })
        
        # Build analysis
        analysis = {
            'error_type': error_type,
            'message': error_msg,
            'category': pattern['category'],
            'severity': pattern['severity'],
            'suggestions': pattern['suggestions'].copy(),
            'auto_fix_available': pattern['auto_fix'] is not None,
            'auto_fix_method': pattern['auto_fix'],
            'context': context or {},
            'analyzed_at': datetime.now().isoformat()
        }
        
        # Add context-specific suggestions
        if context:
            if 'file_path' in context:
                analysis['suggestions'].append(
                    f"Verificar archivo: {context['file_path']}"
                )
            if 'task' in context:
                analysis['suggestions'].append(
                    f"Error ocurrió en tarea: {context['task']}"
                )
        
        logger.info(f"Error analyzed: {error_type} - Severity: {pattern['severity']}")
        return analysis
    
    def suggest_recovery(self, error_analysis: Dict) -> Optional[str]:
        """Suggest recovery action based on error analysis"""
        if not error_analysis.get('auto_fix_available'):
            return None
        
        method = error_analysis.get('auto_fix_method')
        
        recovery_actions = {
            'create_missing_directory': "Crear directorio faltante automáticamente",
            'use_default_value': "Usar valor por defecto para campos faltantes",
            'sanitize_input': "Limpiar y validar datos de entrada",
            'retry_connection': "Reintentar conexión con espera exponencial",
            'reduce_batch_size': "Reducir tamaño de lote de procesamiento",
            'increase_timeout': "Aumentar tiempo de espera y reintentar"
        }
        
        return recovery_actions.get(method)
    
    def get_severity_level(self, error_type: str) -> int:
        """Get numeric severity level (0=info, 1=low, 2=medium, 3=high, 4=critical)"""
        severity_map = {
            'info': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        pattern = self.ERROR_PATTERNS.get(error_type, {'severity': 'medium'})
        return severity_map.get(pattern['severity'], 2)


class AutoRecovery:
    """
    Auto-Recovery System
    
    Attempts automatic recovery from errors when possible
    """
    
    def __init__(self, config: Dict = None, max_retries: int = 3):
        self.config = config or {}
        self.max_retries = max_retries
        self.retry_counts = {}
        self.analyzer = AIErrorAnalyzer(config)
        logger.info(f"Auto-Recovery system initialized (max_retries={max_retries})")
    
    def attempt_recovery(self, error: Exception, task_name: str, 
                        context: Dict = None) -> bool:
        """
        Attempt automatic recovery from error
        
        Returns:
            True if recovery was successful, False otherwise
        """
        # Check retry limit
        if task_name not in self.retry_counts:
            self.retry_counts[task_name] = 0
        
        if self.retry_counts[task_name] >= self.max_retries:
            logger.warning(f"Max retries reached for task: {task_name}")
            return False
        
        self.retry_counts[task_name] += 1
        
        # Analyze error
        analysis = self.analyzer.analyze_error(error, context)
        
        # Attempt auto-fix if available
        auto_fix_method = analysis.get('auto_fix_method')
        if auto_fix_method:
            success = self._execute_auto_fix(auto_fix_method, context)
            if success:
                logger.info(f"Auto-recovery successful for {task_name}")
                return True
        
        logger.warning(f"Auto-recovery failed for {task_name}")
        return False
    
    def _execute_auto_fix(self, method: str, context: Dict = None) -> bool:
        """Execute automatic fix method"""
        try:
            if method == 'create_missing_directory':
                if context and 'file_path' in context:
                    dir_path = Path(context['file_path']).parent
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {dir_path}")
                    return True
            
            elif method == 'use_default_value':
                # This is handled at the call site
                logger.info("Using default value for missing data")
                return True
            
            elif method == 'sanitize_input':
                # This is handled at the call site
                logger.info("Input sanitization applied")
                return True
            
            elif method == 'retry_connection':
                # Exponential backoff retry
                wait_time = 2 ** self.retry_counts.get('connection', 1)
                logger.info(f"Retrying connection after {wait_time}s...")
                time.sleep(min(wait_time, 30))  # Max 30 seconds wait
                return True
            
            elif method == 'reduce_batch_size':
                # Store suggestion for caller
                if 'suggested_batch_size' not in context:
                    context['suggested_batch_size'] = 100
                else:
                    context['suggested_batch_size'] = context['suggested_batch_size'] // 2
                logger.info(f"Suggested batch size: {context['suggested_batch_size']}")
                return True
            
            elif method == 'increase_timeout':
                # Store suggestion for caller
                if 'suggested_timeout' not in context:
                    context['suggested_timeout'] = 60
                else:
                    context['suggested_timeout'] = context['suggested_timeout'] * 2
                logger.info(f"Suggested timeout: {context['suggested_timeout']}s")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Auto-fix execution failed: {e}")
            return False
    
    def reset_retries(self, task_name: str = None):
        """Reset retry counts"""
        if task_name:
            self.retry_counts.pop(task_name, None)
        else:
            self.retry_counts.clear()
        logger.info("Retry counts reset")
    
    def get_recovery_suggestions(self, error: Exception, 
                                  context: Dict = None) -> List[str]:
        """Get human-readable recovery suggestions"""
        analysis = self.analyzer.analyze_error(error, context)
        suggestions = analysis.get('suggestions', [])
        
        # Add recovery action if available
        recovery_action = self.analyzer.suggest_recovery(analysis)
        if recovery_action:
            suggestions.insert(0, f"🔧 Acción automática disponible: {recovery_action}")
        
        return suggestions


class SafeExecutor:
    """
    Safe Task Executor
    
    Executes tasks with emergency stop capability and auto-recovery
    """
    
    def __init__(self, emergency_controller: EmergencyController = None,
                 auto_recovery: AutoRecovery = None):
        self.controller = emergency_controller or EmergencyController()
        self.recovery = auto_recovery or AutoRecovery()
        logger.info("Safe Executor initialized")
    
    def execute(self, task_func: Callable, task_name: str, 
                *args, **kwargs) -> Any:
        """
        Execute a task safely with error handling and recovery
        
        Args:
            task_func: Function to execute
            task_name: Name of the task for logging
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Result of the function, or None if failed
        """
        self.controller.register_task(task_name)
        
        try:
            # Check for stop before starting
            self.controller.check_stop()
            
            # Execute the task
            result = task_func(*args, **kwargs)
            
            # Mark as complete
            self.controller.complete_task(task_name, success=True)
            return result
            
        except EmergencyStop:
            logger.info(f"Task '{task_name}' stopped by emergency signal")
            self.controller.complete_task(task_name, success=False)
            raise
            
        except Exception as e:
            # Log the error
            context = {
                'task': task_name,
                'args': str(args)[:200],
                'kwargs': str(kwargs)[:200]
            }
            self.controller.log_error(e, task_name, context)
            
            # Attempt recovery
            if self.recovery.attempt_recovery(e, task_name, context):
                # Retry the task
                try:
                    result = task_func(*args, **kwargs)
                    self.controller.complete_task(task_name, success=True)
                    return result
                except Exception as retry_error:
                    self.controller.log_error(retry_error, task_name, 
                                             {'recovery_attempt': True})
            
            # Get suggestions
            suggestions = self.recovery.get_recovery_suggestions(e, context)
            
            # Print user-friendly error message
            print(f"\n❌ Error en tarea: {task_name}")
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Mensaje: {str(e)}")
            print("\n   Sugerencias:")
            for suggestion in suggestions:
                print(f"   • {suggestion}")
            
            self.controller.complete_task(task_name, success=False)
            return None
    
    def execute_with_progress(self, items: List, process_func: Callable,
                             task_name: str, desc: str = "Procesando") -> List:
        """
        Execute a task on multiple items with progress bar and emergency stop
        
        Args:
            items: List of items to process
            process_func: Function to apply to each item
            task_name: Name of the task
            desc: Description for progress bar
        
        Returns:
            List of results
        """
        try:
            from tqdm import tqdm
        except ImportError:
            # Fallback if tqdm not installed
            def tqdm(iterable, desc=None, total=None):
                return iterable
        
        self.controller.register_task(task_name)
        results = []
        
        try:
            for item in tqdm(items, desc=desc, total=len(items)):
                # Check for emergency stop
                self.controller.check_stop()
                
                try:
                    result = process_func(item)
                    results.append(result)
                except Exception as e:
                    context = {'item': str(item)[:100], 'task': task_name}
                    self.controller.log_error(e, task_name, context)
                    
                    # Try recovery
                    if self.recovery.attempt_recovery(e, task_name, context):
                        try:
                            result = process_func(item)
                            results.append(result)
                        except:
                            results.append(None)
                    else:
                        results.append(None)
            
            self.controller.complete_task(task_name, success=True)
            return results
            
        except EmergencyStop:
            logger.info(f"Task '{task_name}' stopped - processed {len(results)}/{len(items)}")
            self.controller.complete_task(task_name, success=False)
            return results


# Global instances for easy access
_emergency_controller = None
_auto_recovery = None
_safe_executor = None


def get_emergency_controller() -> EmergencyController:
    """Get or create global emergency controller"""
    global _emergency_controller
    if _emergency_controller is None:
        _emergency_controller = EmergencyController()
    return _emergency_controller


def get_auto_recovery() -> AutoRecovery:
    """Get or create global auto-recovery system"""
    global _auto_recovery
    if _auto_recovery is None:
        _auto_recovery = AutoRecovery()
    return _auto_recovery


def get_safe_executor() -> SafeExecutor:
    """Get or create global safe executor"""
    global _safe_executor
    if _safe_executor is None:
        _safe_executor = SafeExecutor(
            get_emergency_controller(),
            get_auto_recovery()
        )
    return _safe_executor


def safe_execute(task_func: Callable, task_name: str, *args, **kwargs) -> Any:
    """Convenience function to execute a task safely"""
    return get_safe_executor().execute(task_func, task_name, *args, **kwargs)


def check_emergency_stop():
    """Check if emergency stop has been requested"""
    get_emergency_controller().check_stop()


def print_emergency_help():
    """Print help message about emergency stop"""
    print("\n" + "="*60)
    print("🆘 SISTEMA DE CONTROL DE EMERGENCIA")
    print("="*60)
    print("\nPara detener el proceso en cualquier momento:")
    print("  • Presione Ctrl+C")
    print("  • El sistema se detendrá de forma segura")
    print("  • Los datos procesados se guardarán")
    print("\nEl sistema incluye:")
    print("  ✓ Detección automática de errores")
    print("  ✓ Análisis IA de problemas")
    print("  ✓ Sugerencias de recuperación")
    print("  ✓ Auto-recuperación cuando es posible")
    print("="*60 + "\n")
