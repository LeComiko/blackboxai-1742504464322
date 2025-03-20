"""
Email manager for EmailFollowUpApp
Coordinates operations between IMAP, SMTP clients and database
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
import time

from log_manager import get_logger
from database import get_db
from imap_client import get_imap_client
from smtp_client import get_smtp_client
from config import DEFAULT_FOLLOWUP_TEMPLATE, APP_SETTINGS
from utils import (
    calculate_followup_date,
    process_template,
    format_date,
    generate_email_id
)

logger = get_logger()

class EmailManager:
    def __init__(self):
        self.db = get_db()
        self.imap = get_imap_client()
        self.smtp = get_smtp_client()
        self._stop_flag = False
        self._check_thread = None

    def connect(self, username: str, password: str, server_type: str = 'gmail') -> bool:
        """
        Connect to email servers
        
        Args:
            username (str): Email username
            password (str): Email password
            server_type (str): Server type (gmail, outlook, etc.)
        
        Returns:
            bool: True if both connections successful, False otherwise
        """
        imap_success = self.imap.connect(username, password, server_type)
        smtp_success = self.smtp.connect(username, password, server_type)
        
        if imap_success and smtp_success:
            logger.info("Successfully connected to email servers")
            return True
        else:
            logger.error("Failed to connect to one or both email servers")
            return False

    def disconnect(self):
        """Disconnect from email servers"""
        self.imap.disconnect()
        self.smtp.disconnect()
        logger.info("Disconnected from email servers")

    def add_followup(self, email_data: Dict) -> Optional[int]:
        """
        Add a new email followup
        
        Args:
            email_data (Dict): Email information including recipient, subject, etc.
        
        Returns:
            Optional[int]: Followup ID if successful, None otherwise
        """
        try:
            # Generate unique email ID
            email_id = generate_email_id(
                email_data['sender'],
                email_data['subject'],
                email_data['sent_date']
            )
            
            # Calculate followup date
            followup_date = calculate_followup_date(
                email_data['sent_date'],
                email_data['delay_days']
            )
            
            # Prepare followup data
            followup_data = {
                'email_id': email_id,
                'sender': email_data['sender'],
                'recipient': email_data['recipient'],
                'subject': email_data['subject'],
                'sent_date': email_data['sent_date'],
                'followup_date': followup_date,
                'delay_days': email_data['delay_days'],
                'metadata': {
                    'original_message_id': email_data.get('message_id'),
                    'template_name': email_data.get('template_name', 'default'),
                    'custom_variables': email_data.get('template_variables', {})
                }
            }
            
            # Add to database
            followup_id = self.db.add_followup(followup_data)
            logger.info(f"Added new followup with ID: {followup_id}")
            return followup_id
            
        except Exception as e:
            logger.error(f"Error adding followup: {str(e)}")
            return None

    def check_for_responses(self, followup_id: int) -> bool:
        """
        Check if an email has received any responses
        
        Args:
            followup_id (int): Followup ID to check
        
        Returns:
            bool: True if response found, False otherwise
        """
        try:
            # Get followup details from database
            followup = self.db.get_followup_by_email_id(followup_id)
            if not followup:
                logger.error(f"Followup not found: {followup_id}")
                return False
            
            # Check for replies
            replies = self.imap.check_for_replies(
                followup['email_id'],
                followup['subject']
            )
            
            if replies:
                # Update followup status
                self.db.update_followup_status(followup_id, 'responded')
                logger.info(f"Response found for followup {followup_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for responses: {str(e)}")
            return False

    def send_followup(self, followup_id: int) -> bool:
        """
        Send a followup email
        
        Args:
            followup_id (int): Followup ID to process
        
        Returns:
            bool: True if followup sent successfully, False otherwise
        """
        try:
            # Get followup details
            followup = self.db.get_followup_by_email_id(followup_id)
            if not followup:
                logger.error(f"Followup not found: {followup_id}")
                return False
            
            # Check for responses first
            if self.check_for_responses(followup_id):
                logger.info(f"Response already received for followup {followup_id}")
                return True
            
            # Prepare template variables
            template_vars = {
                'DESTINATAIRE': followup['recipient'],
                'SUJET': followup['subject'],
                'DATE_ENVOI': format_date(followup['sent_date']),
                'DATE_RELANCE': format_date(followup['followup_date']),
                'EXPEDITEUR': followup['sender']
            }
            
            # Add any custom variables from metadata
            metadata = followup.get('metadata', {})
            if isinstance(metadata, str):
                import json
                metadata = json.loads(metadata)
            template_vars.update(metadata.get('custom_variables', {}))
            
            # Send followup email
            message_id = self.smtp.send_followup(
                original_email={
                    'to': followup['recipient'],
                    'subject': followup['subject'],
                    'message_id': metadata.get('original_message_id')
                },
                followup_template=DEFAULT_FOLLOWUP_TEMPLATE,
                template_vars=template_vars
            )
            
            if message_id:
                # Update followup status
                self.db.update_followup_status(followup_id, 'sent', True)
                logger.info(f"Followup sent successfully for ID {followup_id}")
                return True
            else:
                logger.error(f"Failed to send followup for ID {followup_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending followup: {str(e)}")
            return False

    def process_pending_followups(self):
        """Process all pending followups"""
        try:
            # Get pending followups
            pending = self.db.get_pending_followups()
            
            for followup in pending:
                followup_id = followup['id']
                
                # Skip if already responded
                if self.check_for_responses(followup_id):
                    continue
                
                # Send followup
                self.send_followup(followup_id)
                
        except Exception as e:
            logger.error(f"Error processing pending followups: {str(e)}")

    def start_automatic_checking(self):
        """Start automatic checking for responses and sending followups"""
        if self._check_thread and self._check_thread.is_alive():
            logger.warning("Automatic checking already running")
            return

        def check_loop():
            while not self._stop_flag:
                try:
                    self.process_pending_followups()
                except Exception as e:
                    logger.error(f"Error in check loop: {str(e)}")
                
                # Wait for next check interval
                time.sleep(APP_SETTINGS['check_interval'])

        self._stop_flag = False
        self._check_thread = threading.Thread(target=check_loop, daemon=True)
        self._check_thread.start()
        logger.info("Started automatic followup checking")

    def stop_automatic_checking(self):
        """Stop automatic checking"""
        self._stop_flag = True
        if self._check_thread:
            self._check_thread.join()
        logger.info("Stopped automatic followup checking")

    def get_followup_status(self, followup_id: int) -> Optional[Dict]:
        """
        Get current status of a followup
        
        Args:
            followup_id (int): Followup ID to check
        
        Returns:
            Optional[Dict]: Followup status information
        """
        try:
            followup = self.db.get_followup_by_email_id(followup_id)
            if not followup:
                return None
            
            return {
                'id': followup['id'],
                'status': followup['status'],
                'followup_count': followup['followup_count'],
                'last_check': followup['last_check_date']
            }
            
        except Exception as e:
            logger.error(f"Error getting followup status: {str(e)}")
            return None

# Global email manager instance
email_manager = EmailManager()

def get_email_manager() -> EmailManager:
    """
    Get the global email manager instance
    
    Returns:
        EmailManager: Global email manager instance
    """
    return email_manager