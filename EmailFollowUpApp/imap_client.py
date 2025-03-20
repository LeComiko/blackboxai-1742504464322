"""
IMAP client for EmailFollowUpApp
Handles IMAP connection and email operations
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re

from log_manager import get_logger
from config import EMAIL_SERVERS, AUTO_REPLY_PATTERNS
from utils import sanitize_subject, generate_email_id

logger = get_logger()

class IMAPClient:
    def __init__(self):
        self.connection = None
        self.username = None
        self.is_connected = False

    def connect(self, username: str, password: str, server_type: str = 'gmail') -> bool:
        """
        Connect to IMAP server
        
        Args:
            username (str): Email username
            password (str): Email password or app-specific password
            server_type (str): Server type (gmail, outlook, etc.)
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            server_config = EMAIL_SERVERS.get(server_type, {}).get('imap', {})
            if not server_config:
                raise ValueError(f"Unknown server type: {server_type}")

            self.connection = imaplib.IMAP4_SSL(
                server_config['server'],
                server_config['port']
            )
            
            self.connection.login(username, password)
            self.username = username
            self.is_connected = True
            
            logger.info(f"Successfully connected to IMAP server for {username}")
            return True
            
        except (imaplib.IMAP4.error, ValueError) as e:
            logger.error(f"IMAP connection error: {str(e)}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.logout()
                self.is_connected = False
                logger.info("Disconnected from IMAP server")
            except imaplib.IMAP4.error as e:
                logger.error(f"Error disconnecting from IMAP server: {str(e)}")

    def _decode_email_header(self, header: str) -> str:
        """
        Decode email header
        
        Args:
            header (str): Email header to decode
        
        Returns:
            str: Decoded header
        """
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                except (LookupError, TypeError):
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))
        return ' '.join(decoded_parts)

    def _parse_email_message(self, email_data: Tuple) -> Dict:
        """
        Parse email message data
        
        Args:
            email_data (Tuple): Raw email data
        
        Returns:
            Dict: Parsed email information
        """
        email_body = email_data[0][1]
        message = email.message_from_bytes(email_body)
        
        subject = self._decode_email_header(message.get('subject', ''))
        from_addr = self._decode_email_header(message.get('from', ''))
        date_str = message.get('date', '')
        
        try:
            date = email.utils.parsedate_to_datetime(date_str)
        except (TypeError, ValueError):
            date = datetime.now()

        # Extract email body
        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode()
                    except:
                        continue
        else:
            try:
                body = message.get_payload(decode=True).decode()
            except:
                body = message.get_payload()

        return {
            'subject': subject,
            'from': from_addr,
            'date': date,
            'body': body,
            'message_id': message.get('message-id', ''),
            'in_reply_to': message.get('in-reply-to', ''),
            'references': message.get('references', ''),
            'headers': dict(message.items())
        }

    def check_for_replies(self, original_email_id: str, subject: str) -> List[Dict]:
        """
        Check for replies to a specific email
        
        Args:
            original_email_id (str): ID of the original email
            subject (str): Subject of the original email
        
        Returns:
            List[Dict]: List of reply emails found
        """
        if not self.is_connected:
            logger.error("Not connected to IMAP server")
            return []

        try:
            replies = []
            self.connection.select('INBOX')
            
            # Search for replies based on subject
            sanitized_subject = sanitize_subject(subject)
            search_query = f'SUBJECT "{sanitized_subject}"'
            _, message_numbers = self.connection.search(None, search_query)
            
            for num in message_numbers[0].split():
                _, msg_data = self.connection.fetch(num, '(RFC822)')
                email_info = self._parse_email_message(msg_data)
                
                # Check if this is a reply to our original email
                if (original_email_id in email_info['references'] or 
                    original_email_id in email_info['in_reply_to']):
                    
                    if not self._is_auto_reply(email_info):
                        replies.append(email_info)
            
            return replies
            
        except imaplib.IMAP4.error as e:
            logger.error(f"Error checking for replies: {str(e)}")
            return []

    def _is_auto_reply(self, email_info: Dict) -> bool:
        """
        Check if an email is an automatic reply
        
        Args:
            email_info (Dict): Parsed email information
        
        Returns:
            bool: True if email is an auto-reply, False otherwise
        """
        headers = email_info['headers']
        body = email_info['body'].lower()
        
        # Check common auto-reply headers
        auto_reply_headers = [
            'auto-submitted',
            'x-auto-response-suppress',
            'x-autorespond',
            'x-autoreply'
        ]
        
        for header in auto_reply_headers:
            if header in headers:
                return True
        
        # Check for auto-reply patterns in the body
        for pattern in AUTO_REPLY_PATTERNS:
            if pattern.lower() in body:
                return True
        
        return False

    def get_sent_email(self, email_id: str) -> Optional[Dict]:
        """
        Get details of a sent email
        
        Args:
            email_id (str): Email ID to search for
        
        Returns:
            Optional[Dict]: Email details if found, None otherwise
        """
        if not self.is_connected:
            logger.error("Not connected to IMAP server")
            return None

        try:
            self.connection.select('"[Gmail]/Sent Mail"')
            _, message_numbers = self.connection.search(None, f'HEADER "Message-ID" "{email_id}"')
            
            for num in message_numbers[0].split():
                _, msg_data = self.connection.fetch(num, '(RFC822)')
                return self._parse_email_message(msg_data)
            
            return None
            
        except imaplib.IMAP4.error as e:
            logger.error(f"Error getting sent email: {str(e)}")
            return None

    def search_emails(self, criteria: Dict) -> List[Dict]:
        """
        Search emails based on criteria
        
        Args:
            criteria (Dict): Search criteria (subject, from, to, since, before)
        
        Returns:
            List[Dict]: List of matching emails
        """
        if not self.is_connected:
            logger.error("Not connected to IMAP server")
            return []

        try:
            self.connection.select('INBOX')
            search_query = []
            
            if 'subject' in criteria:
                search_query.append(f'SUBJECT "{criteria["subject"]}"')
            if 'from' in criteria:
                search_query.append(f'FROM "{criteria["from"]}"')
            if 'to' in criteria:
                search_query.append(f'TO "{criteria["to"]}"')
            if 'since' in criteria:
                search_query.append(f'SINCE "{criteria["since"]}"')
            if 'before' in criteria:
                search_query.append(f'BEFORE "{criteria["before"]}"')
            
            _, message_numbers = self.connection.search(None, ' '.join(search_query))
            
            results = []
            for num in message_numbers[0].split():
                _, msg_data = self.connection.fetch(num, '(RFC822)')
                results.append(self._parse_email_message(msg_data))
            
            return results
            
        except imaplib.IMAP4.error as e:
            logger.error(f"Error searching emails: {str(e)}")
            return []

# Global IMAP client instance
imap_client = IMAPClient()

def get_imap_client() -> IMAPClient:
    """
    Get the global IMAP client instance
    
    Returns:
        IMAPClient: Global IMAP client instance
    """
    return imap_client