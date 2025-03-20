"""
SMTP client for EmailFollowUpApp
Handles SMTP connection and email sending operations
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from typing import Optional, List, Dict
import ssl

from log_manager import get_logger
from config import EMAIL_SERVERS
from utils import validate_email

logger = get_logger()

class SMTPClient:
    def __init__(self):
        self.connection = None
        self.username = None
        self.is_connected = False

    def connect(self, username: str, password: str, server_type: str = 'gmail') -> bool:
        """
        Connect to SMTP server
        
        Args:
            username (str): Email username
            password (str): Email password or app-specific password
            server_type (str): Server type (gmail, outlook, etc.)
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            server_config = EMAIL_SERVERS.get(server_type, {}).get('smtp', {})
            if not server_config:
                raise ValueError(f"Unknown server type: {server_type}")

            self.connection = smtplib.SMTP(
                server_config['server'],
                server_config['port']
            )
            
            # Start TLS if required
            if server_config.get('tls'):
                context = ssl.create_default_context()
                self.connection.starttls(context=context)
            
            self.connection.login(username, password)
            self.username = username
            self.is_connected = True
            
            logger.info(f"Successfully connected to SMTP server for {username}")
            return True
            
        except (smtplib.SMTPException, ValueError) as e:
            logger.error(f"SMTP connection error: {str(e)}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from SMTP server"""
        if self.connection:
            try:
                self.connection.quit()
                self.is_connected = False
                logger.info("Disconnected from SMTP server")
            except smtplib.SMTPException as e:
                logger.error(f"Error disconnecting from SMTP server: {str(e)}")

    def send_email(self, 
                  to_email: str, 
                  subject: str, 
                  body: str, 
                  cc: Optional[List[str]] = None,
                  bcc: Optional[List[str]] = None,
                  reply_to: Optional[str] = None,
                  references: Optional[List[str]] = None,
                  in_reply_to: Optional[str] = None) -> Optional[str]:
        """
        Send an email
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body (HTML or plain text)
            cc (List[str], optional): CC recipients
            bcc (List[str], optional): BCC recipients
            reply_to (str, optional): Reply-To address
            references (List[str], optional): Referenced message IDs
            in_reply_to (str, optional): Message ID being replied to
        
        Returns:
            Optional[str]: Message ID if sent successfully, None otherwise
        """
        if not self.is_connected:
            logger.error("Not connected to SMTP server")
            return None

        if not validate_email(to_email):
            logger.error(f"Invalid recipient email address: {to_email}")
            return None

        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Date'] = formatdate(localtime=True)
            
            # Generate a unique Message-ID
            msg_id = make_msgid(domain=self.username.split('@')[1])
            msg['Message-ID'] = msg_id
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if reply_to:
                msg['Reply-To'] = reply_to
            if references:
                msg['References'] = ' '.join(references)
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to

            # Attach body
            msg.attach(MIMEText(body, 'html' if '<html>' in body.lower() else 'plain'))
            
            # Prepare recipients list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Send email
            self.connection.send_message(msg, from_addr=self.username, to_addrs=recipients)
            
            logger.info(f"Email sent successfully to {to_email}")
            return msg_id.strip('<>')
            
        except smtplib.SMTPException as e:
            logger.error(f"Error sending email: {str(e)}")
            return None

    def send_followup(self, 
                     original_email: Dict,
                     followup_template: str,
                     template_vars: Dict[str, str]) -> Optional[str]:
        """
        Send a followup email
        
        Args:
            original_email (Dict): Original email information
            followup_template (str): Template for followup email
            template_vars (Dict[str, str]): Variables for template
        
        Returns:
            Optional[str]: Message ID if sent successfully, None otherwise
        """
        try:
            # Format the template with variables
            body = followup_template.format(**template_vars)
            
            # Add reference to original email
            references = [original_email.get('message_id', '')]
            
            return self.send_email(
                to_email=original_email['to'],
                subject=f"Re: {original_email['subject']}",
                body=body,
                references=references,
                in_reply_to=original_email['message_id']
            )
            
        except (KeyError, ValueError) as e:
            logger.error(f"Error preparing followup email: {str(e)}")
            return None

    def test_connection(self) -> bool:
        """
        Test SMTP connection
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        if not self.is_connected:
            return False
            
        try:
            status = self.connection.noop()[0]
            return status == 250
        except smtplib.SMTPException:
            return False

# Global SMTP client instance
smtp_client = SMTPClient()

def get_smtp_client() -> SMTPClient:
    """
    Get the global SMTP client instance
    
    Returns:
        SMTPClient: Global SMTP client instance
    """
    return smtp_client