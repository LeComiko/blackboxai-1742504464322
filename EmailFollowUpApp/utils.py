"""
Utility functions for EmailFollowUpApp
Contains helper functions for date calculations, template processing, and email validation
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

# Email validation regex pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email (str): Email address to validate
    
    Returns:
        bool: True if email is valid, False otherwise
    """
    return bool(EMAIL_PATTERN.match(email))

def calculate_followup_date(sent_date: datetime, delay_days: int) -> datetime:
    """
    Calculate the followup date based on sent date and delay
    
    Args:
        sent_date (datetime): Original email sent date
        delay_days (int): Number of days to wait before followup
    
    Returns:
        datetime: Calculated followup date
    """
    return sent_date + timedelta(days=delay_days)

def process_template(template: str, variables: Dict[str, str]) -> str:
    """
    Replace placeholders in email template with actual values
    
    Args:
        template (str): Email template with placeholders
        variables (Dict[str, str]): Dictionary of placeholder values
    
    Returns:
        str: Processed template with replaced values
    """
    try:
        return template.format(**variables)
    except KeyError as e:
        logging.error(f"Missing template variable: {e}")
        return template

def format_date(date: datetime, format_str: str = "%d/%m/%Y %H:%M") -> str:
    """
    Format datetime object to string
    
    Args:
        date (datetime): Date to format
        format_str (str): Format string
    
    Returns:
        str: Formatted date string
    """
    return date.strftime(format_str)

def parse_date(date_str: str, format_str: str = "%d/%m/%Y %H:%M") -> Optional[datetime]:
    """
    Parse date string to datetime object
    
    Args:
        date_str (str): Date string to parse
        format_str (str): Format string
    
    Returns:
        Optional[datetime]: Parsed datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        logging.error(f"Failed to parse date: {date_str}")
        return None

def sanitize_subject(subject: str) -> str:
    """
    Clean and sanitize email subject
    
    Args:
        subject (str): Email subject to sanitize
    
    Returns:
        str: Sanitized subject
    """
    # Remove Re:, Fwd:, etc. and trim whitespace
    cleaned = re.sub(r'^(?:Re|Fwd|FW|Forward):\s*', '', subject, flags=re.IGNORECASE)
    return cleaned.strip()

def generate_email_id(sender: str, subject: str, date: datetime) -> str:
    """
    Generate unique email identifier
    
    Args:
        sender (str): Email sender
        subject (str): Email subject
        date (datetime): Email date
    
    Returns:
        str: Unique email identifier
    """
    from hashlib import md5
    unique_string = f"{sender}{subject}{date.isoformat()}"
    return md5(unique_string.encode()).hexdigest()

def is_working_day(date: datetime) -> bool:
    """
    Check if given date is a working day (Monday-Friday)
    
    Args:
        date (datetime): Date to check
    
    Returns:
        bool: True if working day, False otherwise
    """
    return date.weekday() < 5

def get_next_working_day(date: datetime) -> datetime:
    """
    Get next working day from given date
    
    Args:
        date (datetime): Starting date
    
    Returns:
        datetime: Next working day
    """
    next_day = date + timedelta(days=1)
    while not is_working_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
    
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."