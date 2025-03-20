"""
Configuration file for EmailFollowUpApp
Contains default settings, email templates, and server configurations
"""

# Default IMAP/SMTP server configurations
EMAIL_SERVERS = {
    'gmail': {
        'imap': {
            'server': 'imap.gmail.com',
            'port': 993,
            'ssl': True
        },
        'smtp': {
            'server': 'smtp.gmail.com',
            'port': 587,
            'tls': True
        }
    },
    'outlook': {
        'imap': {
            'server': 'outlook.office365.com',
            'port': 993,
            'ssl': True
        },
        'smtp': {
            'server': 'smtp.office365.com',
            'port': 587,
            'tls': True
        }
    }
}

# Application settings
APP_SETTINGS = {
    'check_interval': 1800,  # 30 minutes in seconds
    'max_retries': 3,
    'retry_delay': 300,  # 5 minutes in seconds
    'auto_start': False,
    'minimize_to_tray': True,
    'debug_mode': False
}

# Email templates
DEFAULT_FOLLOWUP_TEMPLATE = """
Bonjour {DESTINATAIRE},

Je me permets de revenir vers vous concernant mon email du {DATE_ENVOI} à propos de "{SUJET}".

N'ayant pas reçu de réponse, je souhaitais m'assurer que vous aviez bien reçu mon message et que celui-ci avait retenu votre attention.

Cordialement,
{EXPEDITEUR}
"""

# Auto-reply detection patterns
AUTO_REPLY_PATTERNS = [
    "absent du bureau",
    "out of office",
    "en congés",
    "automatique",
    "automatic reply",
    "vacation response",
    "accusé de réception automatique",
    "message automatique"
]

# Database configuration
DATABASE = {
    'filename': 'followup.db',
    'backup_interval': 86400,  # 24 hours in seconds
    'max_backups': 7
}

# Logging configuration
LOGGING = {
    'filename': 'logs/app.log',
    'max_size': 5242880,  # 5MB
    'backup_count': 3,
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}