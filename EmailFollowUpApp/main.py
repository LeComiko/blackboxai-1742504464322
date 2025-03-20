"""
Main entry point for EmailFollowUpApp
"""

import sys
import os
from pathlib import Path
import argparse
import logging

from PyQt5.QtWidgets import QApplication
from ui_main import MainWindow
from log_manager import get_logger
from config import APP_SETTINGS

def setup_environment():
    """Set up application environment"""
    try:
        # Create necessary directories
        Path('logs').mkdir(exist_ok=True)
        
        # Set up logging
        logger = get_logger()
        logger.info("Application environment initialized")
        
        return True
    except Exception as e:
        print(f"Error setting up environment: {e}")
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='EmailFollowUpApp - Application de suivi et relance d\'emails')
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Active le mode debug'
    )
    
    parser.add_argument(
        '--minimize',
        action='store_true',
        help='Démarre l\'application minimisée dans la barre des tâches'
    )
    
    return parser.parse_args()

def main():
    """Main application entry point"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Set up environment
        if not setup_environment():
            sys.exit(1)
        
        # Configure logging level based on debug flag
        logger = get_logger()
        if args.debug:
            logger.setLevel(logging.DEBUG)
            APP_SETTINGS['debug_mode'] = True
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("EmailFollowUpApp")
        app.setStyle('Fusion')
        
        # Create main window
        window = MainWindow()
        
        # Show window (or minimize to tray)
        if args.minimize:
            window.hide()
        else:
            window.show()
        
        # Start application event loop
        logger.info("Application started")
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()