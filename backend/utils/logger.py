"""
Logging configuration
Provides centralized logging setup for the application.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from backend.config import Config

def setup_logger(name: str = 'electronic_inventory', config: Config = None) -> logging.Logger:
    """
    Setup application logger with proper formatting and handlers
    """
    if config is None:
        config = Config()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log file is specified)
    if config.LOG_FILE:
        try:
            # Create log directory if it doesn't exist
            log_dir = Path(config.LOG_FILE).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            # Rotating file handler (10MB max, 5 backups)
            file_handler = logging.handlers.RotatingFileHandler(
                config.LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")

    # Suppress noisy loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    return logger

def get_request_logger() -> logging.Logger:
    """Get logger specifically for HTTP requests"""
    logger = logging.getLogger('electronic_inventory.requests')
    if not logger.handlers:
        setup_logger('electronic_inventory.requests')
    return logger

def log_request(logger: logging.Logger, method: str, path: str, status: int, duration: float):
    """Log HTTP request with timing information"""
    level = logging.INFO if status < 400 else logging.WARNING if status < 500 else logging.ERROR
    logger.log(level, f'{method} {path} - {status} - {duration:.2f}s')

def log_database_operation(logger: logging.Logger, operation: str, table: str, record_id: int = None):
    """Log database operations"""
    message = f'DB {operation} on {table}'
    if record_id:
        message += f' (ID: {record_id})'
    logger.info(message)

def log_error_with_context(logger: logging.Logger, error: Exception, context: dict = None):
    """Log error with additional context"""
    message = f'Error: {str(error)}'
    if context:
        context_str = ', '.join(f'{k}={v}' for k, v in context.items())
        message += f' | Context: {context_str}'
    logger.error(message, exc_info=True)
