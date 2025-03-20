"""
Scheduler for EmailFollowUpApp
Handles periodic email checking and followup scheduling
"""

from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from datetime import datetime, timedelta
import threading
from typing import Optional, Callable

from log_manager import get_logger
from config import APP_SETTINGS
from email_manager import get_email_manager

logger = get_logger()

class Scheduler(QObject):
    # Signals for UI updates
    check_started = pyqtSignal()
    check_completed = pyqtSignal(bool)  # bool indicates success/failure
    followup_sent = pyqtSignal(int)  # followup_id
    response_detected = pyqtSignal(int)  # followup_id
    error_occurred = pyqtSignal(str)  # error message

    def __init__(self):
        super().__init__()
        self.email_manager = get_email_manager()
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_emails)
        self.is_running = False
        self._last_check = None
        self._error_count = 0
        self._max_errors = APP_SETTINGS['max_retries']

    def start(self):
        """Start the scheduler"""
        try:
            if not self.is_running:
                # Set up timer for periodic checks
                interval = APP_SETTINGS['check_interval'] * 1000  # Convert to milliseconds
                self.check_timer.start(interval)
                self.is_running = True
                self._last_check = datetime.now()
                self._error_count = 0
                
                logger.info("Scheduler started successfully")
                
                # Perform initial check
                self.check_emails()
            else:
                logger.warning("Scheduler is already running")
                
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            self.error_occurred.emit(f"Failed to start scheduler: {str(e)}")

    def stop(self):
        """Stop the scheduler"""
        try:
            if self.is_running:
                self.check_timer.stop()
                self.is_running = False
                logger.info("Scheduler stopped")
            else:
                logger.warning("Scheduler is not running")
                
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            self.error_occurred.emit(f"Failed to stop scheduler: {str(e)}")

    def check_emails(self):
        """Perform email checking and followup processing"""
        try:
            self.check_started.emit()
            logger.debug("Starting email check cycle")
            
            # Process pending followups
            self.email_manager.process_pending_followups()
            
            self._last_check = datetime.now()
            self._error_count = 0
            self.check_completed.emit(True)
            logger.debug("Email check cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error during email check: {str(e)}")
            self._error_count += 1
            self.check_completed.emit(False)
            self.error_occurred.emit(f"Email check failed: {str(e)}")
            
            # If too many errors occur, stop the scheduler
            if self._error_count >= self._max_errors:
                logger.error("Maximum error count reached, stopping scheduler")
                self.stop()

    def is_active(self) -> bool:
        """
        Check if scheduler is currently active
        
        Returns:
            bool: True if scheduler is running, False otherwise
        """
        return self.is_running

    def get_last_check_time(self) -> Optional[datetime]:
        """
        Get the timestamp of the last check
        
        Returns:
            Optional[datetime]: Timestamp of last check, None if never checked
        """
        return self._last_check

    def get_next_check_time(self) -> Optional[datetime]:
        """
        Get the expected time of next check
        
        Returns:
            Optional[datetime]: Expected time of next check, None if not running
        """
        if not self.is_running or not self._last_check:
            return None
            
        return self._last_check + timedelta(seconds=APP_SETTINGS['check_interval'])

    def force_check(self):
        """Force an immediate email check"""
        if self.is_running:
            # Reset the timer to trigger immediately
            self.check_timer.stop()
            self.check_emails()
            self.check_timer.start()
            logger.info("Forced email check initiated")
        else:
            logger.warning("Cannot force check: scheduler is not running")

    def set_check_interval(self, interval: int):
        """
        Set new check interval
        
        Args:
            interval (int): New interval in seconds
        """
        try:
            if interval < 60:  # Minimum 1 minute
                interval = 60
                
            # Update timer if running
            if self.is_running:
                self.check_timer.setInterval(interval * 1000)
                
            logger.info(f"Check interval updated to {interval} seconds")
            
        except Exception as e:
            logger.error(f"Error setting check interval: {str(e)}")
            self.error_occurred.emit(f"Failed to set check interval: {str(e)}")

    def add_check_listener(self, callback: Callable[[bool], None]):
        """
        Add a callback for check completion
        
        Args:
            callback (Callable[[bool], None]): Callback function
        """
        self.check_completed.connect(callback)

    def add_error_listener(self, callback: Callable[[str], None]):
        """
        Add a callback for error handling
        
        Args:
            callback (Callable[[str], None]): Callback function
        """
        self.error_occurred.connect(callback)

# Global scheduler instance
scheduler = Scheduler()

def get_scheduler() -> Scheduler:
    """
    Get the global scheduler instance
    
    Returns:
        Scheduler: Global scheduler instance
    """
    return scheduler