"""
Configuration for Email Sorter System
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
TRAINING_DATA_FILE = DATA_DIR / "training_data.json"
STATS_FILE = DATA_DIR / "statistics.json"
LOG_FILE = LOG_DIR / "email_sorter.log"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Ollama Configuration
OLLAMA_MODEL = "llama3.2:latest"  # You can change this to any model you prefer
OLLAMA_HOST = "http://localhost:11434"

# Confidence Thresholds
CONFIDENCE_THRESHOLD_SUGGEST = 0.90  # 90% confidence to make suggestions
CONFIDENCE_THRESHOLD_AUTO = 1.00      # 100% confidence to auto-filter

# Email Classification Categories - Inbox Zero Methodology
# Based on proven productivity system: https://www.43folders.com/izero
#
# Philosophy: Every email should tell you what ACTION to take, not just what it is.
#
# Core Categories:
#   1. Action/Do       - Requires action, takes <2 min to complete
#   2. Waiting For     - Waiting on response from others (follow up weekly)
#   3. Read/Reference  - Information to read or reference later (newsletters, docs)
#   4. Archive         - Done/completed, may need later (search, don't browse)
#
# Additional:
#   - Spam            - Junk/unwanted (train spam filters)
#   - Delete          - Truly useless, will be deleted
#
# Process:
#   1. Open email → decide immediately
#   2. Keep Action/Waiting folders SMALL (sign of progress)
#   3. If takes >2 min → add to todo list, not Action folder
#   4. Archive liberally → use search to find later
#   5. Don't over-folderize → these 6 categories are enough!
DEFAULT_CATEGORIES = [
    "Action/Do",           # ✅ Do this now (<2 min) or today
    "Waiting For",         # ⏳ Waiting on someone else
    "Read/Reference",      # 📚 Read later or reference material
    "Archive",             # 📁 Done, keep for search
    "Spam",                # 🚫 Junk/unwanted
    "Delete"               # 🗑️  Truly useless
]

# Apple Mail Mailbox Mappings
# Maps category names to actual Gmail/IMAP folder names
#
# IMPORTANT: These will be created in your account (server-side) and sync to Gmail!
#
# Inbox Zero Best Practices:
#   - Action/Do: Check daily, keep under 20 emails
#   - Waiting For: Review weekly, follow up on old items
#   - Read/Reference: Process during "reading time" blocks
#   - Archive: Almost never browse, just search when needed
MAILBOXES = {
    "Action/Do": "Action",                    # Quick actions, responses
    "Waiting For": "Waiting",                 # Tracking delegated items
    "Read/Reference": "Read",                 # Newsletters, articles, docs
    "Archive": "Archive",                     # Completed items (Gmail's Archive)
    "Spam": "Spam",                           # Junk (trains Gmail spam filter)
    "Delete": None                            # Special case - will delete the email
}

# Learning Parameters
MIN_TRAINING_SAMPLES = 3  # Minimum samples per category before making suggestions
SIMILARITY_THRESHOLD = 0.85  # How similar emails need to be for high confidence

# Database Configuration (Optional - for PostgreSQL backend)
USE_POSTGRES = True  # Set to True to use PostgreSQL instead of JSON
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "email_sorter",
    "user": "user",
    "password": "password"
}

# Account Configuration
# Leave as None to process all accounts (unified inbox with 46,693 messages)
# Or specify an account name to process only that account
# Available accounts: "iCloud", "paul@stoute.co", "paul@hipaacomplianthosting.com"
MAIL_ACCOUNT = None  # Process all accounts
# MAIL_ACCOUNT = "paul@stoute.co"  # Example: Process only this account

# AI Summary Configuration
# Enable AI-generated summaries for better context (adds ~2-3 seconds per email)
ENABLE_AI_SUMMARY = True  # Set to False to skip summaries and process faster
SUMMARY_MAX_LENGTH = 200  # Maximum characters of email content to analyze

# Logging Configuration
ENABLE_LOGGING = True  # Set to False to disable file logging
LOG_LEVEL = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB - rotate logs when they reach this size
LOG_BACKUP_COUNT = 5  # Keep 5 backup log files
