"""
Log manager for EmailFollowUpApp
Handles logging configuration and provides logging interface
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from config import LOGGING

class LogManager:
    _instance: Optional['LogManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the logger with configuration from config.py"""
        # Create logs directory if it doesn't exist
        log_dir = Path(LOGGING['filename']).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(LOGGING['level'])

        # Create formatters
        file_formatter = logging.Formatter(LOGGING['format'])
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')

        # File handler (with rotation)
        file_handler = logging.handlers.RotatingFileHandler(
            LOGGING['filename'],
            maxBytes=LOGGING['max_size'],
            backupCount=LOGGING['backup_count']
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        self.logger = logger

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Get the singleton logger instance"""
        if cls._instance is None:
            cls()
        return cls._instance.logger

    def log_error(self, message: str, exc: Optional[Exception] = None):
        """
        Log an error message with optional exception details
        
        Args:
            message (str): Error message
            exc (Exception, optional): Exception object
        """
        if exc:
            self.logger.error(f"{message}: {str(exc)}", exc_info=True)
        else:
            self.logger.error(message)

    def log_info(self, message: str):
        """
        Log an info message
        
        Args:
            message (str): Info message
        """
        self.logger.info(message)

    def log_warning(self, message: str):
        """
        Log a warning message
        
        Args:
            message (str): Warning message
        """
        self.logger.warning(message)

    def log_debug(self, message: str):
        """
        Log a debug message
        
        Args:
            message (str): Debug message
        """
        self.logger.debug(message)

    def log_email_event(self, event_type: str, email_id: str, details: str):
        """
        Log an email-related event
        
        Args:
            event_type (str): Type of event (sent, received, followup, etc.)
            email_id (str): Unique email identifier
            details (str): Event details
        """
        self.logger.info(f"Email Event [{event_type}] - ID: {email_id} - {details}")

    def log_system_event(self, event_type: str, details: str):
        """
        Log a system-related event
        
        Args:
            event_type (str): Type of event (startup, shutdown, config change, etc.)
            details (str): Event details
        """
        self.logger.info(f"System Event [{event_type}] - {details}")

# Global logger instance
logger = LogManager.get_logger()

def get_logger() -> logging.Logger:
    """
    Get the global logger instance
    
    Returns:
        logging.Logger: Global logger instance
    """
    return logger