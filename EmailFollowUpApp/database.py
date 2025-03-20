"""
Database manager for EmailFollowUpApp
Handles SQLite database operations for email followups
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path

from log_manager import get_logger
from config import DATABASE

logger = get_logger()

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize_db()
        return cls._instance

    def _initialize_db(self):
        """Initialize the SQLite database and create necessary tables"""
        try:
            self.conn = sqlite3.connect(DATABASE['filename'])
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            self._create_tables()
            
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def _create_tables(self):
        """Create the necessary database tables"""
        try:
            # Followups table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS followups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT UNIQUE,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    sent_date TIMESTAMP NOT NULL,
                    followup_date TIMESTAMP NOT NULL,
                    delay_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    followup_count INTEGER DEFAULT 0,
                    last_check_date TIMESTAMP,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Email templates table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    subject TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Settings table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.conn.commit()
            logger.debug("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def add_followup(self, followup_data: Dict) -> int:
        """
        Add a new followup to the database
        
        Args:
            followup_data (Dict): Followup data including email details and followup settings
        
        Returns:
            int: ID of the newly created followup
        """
        try:
            metadata = json.dumps(followup_data.get('metadata', {}))
            
            self.cursor.execute('''
                INSERT INTO followups (
                    email_id, sender, recipient, subject, sent_date,
                    followup_date, delay_days, status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                followup_data['email_id'],
                followup_data['sender'],
                followup_data['recipient'],
                followup_data['subject'],
                followup_data['sent_date'],
                followup_data['followup_date'],
                followup_data['delay_days'],
                'pending',
                metadata
            ))
            
            self.conn.commit()
            followup_id = self.cursor.lastrowid
            logger.info(f"Added new followup with ID: {followup_id}")
            return followup_id
        except sqlite3.Error as e:
            logger.error(f"Error adding followup: {e}")
            self.conn.rollback()
            raise

    def update_followup_status(self, followup_id: int, status: str, increment_count: bool = False) -> bool:
        """
        Update the status of a followup
        
        Args:
            followup_id (int): ID of the followup to update
            status (str): New status value
            increment_count (bool): Whether to increment the followup count
        
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if increment_count:
                self.cursor.execute('''
                    UPDATE followups 
                    SET status = ?, followup_count = followup_count + 1,
                        last_check_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, followup_id))
            else:
                self.cursor.execute('''
                    UPDATE followups 
                    SET status = ?, last_check_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, followup_id))
            
            self.conn.commit()
            logger.debug(f"Updated followup {followup_id} status to {status}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating followup status: {e}")
            self.conn.rollback()
            return False

    def get_pending_followups(self) -> List[Dict]:
        """
        Get all pending followups that need to be processed
        
        Returns:
            List[Dict]: List of pending followups
        """
        try:
            self.cursor.execute('''
                SELECT * FROM followups 
                WHERE status = 'pending' 
                AND followup_date <= CURRENT_TIMESTAMP
                ORDER BY followup_date ASC
            ''')
            
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching pending followups: {e}")
            return []

    def get_followup_by_email_id(self, email_id: str) -> Optional[Dict]:
        """
        Get followup details by email ID
        
        Args:
            email_id (str): Unique email identifier
        
        Returns:
            Optional[Dict]: Followup details if found, None otherwise
        """
        try:
            self.cursor.execute('SELECT * FROM followups WHERE email_id = ?', (email_id,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching followup by email ID: {e}")
            return None

    def delete_followup(self, followup_id: int) -> bool:
        """
        Delete a followup from the database
        
        Args:
            followup_id (int): ID of the followup to delete
        
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            self.cursor.execute('DELETE FROM followups WHERE id = ?', (followup_id,))
            self.conn.commit()
            logger.info(f"Deleted followup with ID: {followup_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting followup: {e}")
            self.conn.rollback()
            return False

    def get_all_followups(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get all followups with pagination
        
        Args:
            limit (int): Maximum number of records to return
            offset (int): Number of records to skip
        
        Returns:
            List[Dict]: List of followups
        """
        try:
            self.cursor.execute('''
                SELECT * FROM followups 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching all followups: {e}")
            return []

    def save_template(self, name: str, subject: str, content: str) -> bool:
        """
        Save or update an email template
        
        Args:
            name (str): Template name
            subject (str): Email subject template
            content (str): Email content template
        
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            self.cursor.execute('''
                INSERT INTO email_templates (name, subject, content)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    subject = excluded.subject,
                    content = excluded.content,
                    updated_at = CURRENT_TIMESTAMP
            ''', (name, subject, content))
            
            self.conn.commit()
            logger.info(f"Saved email template: {name}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error saving email template: {e}")
            self.conn.rollback()
            return False

    def get_template(self, name: str) -> Optional[Dict]:
        """
        Get an email template by name
        
        Args:
            name (str): Template name
        
        Returns:
            Optional[Dict]: Template details if found, None otherwise
        """
        try:
            self.cursor.execute('SELECT * FROM email_templates WHERE name = ?', (name,))
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching email template: {e}")
            return None

    def close(self):
        """Close the database connection"""
        try:
            self.conn.close()
            logger.debug("Database connection closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")

# Global database instance
db = DatabaseManager()

def get_db() -> DatabaseManager:
    """
    Get the global database instance
    
    Returns:
        DatabaseManager: Global database instance
    """
    return db