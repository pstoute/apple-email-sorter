# Email Sorter - Intelligent Apple Mail Automation

An intelligent email automation system that learns your email organization preferences and automatically sorts emails in Apple Mail using local AI. Built for entrepreneurs and busy professionals to achieve Inbox Zero using the proven Inbox Zero methodology.

## Overview

This tool uses **Ollama AI** (running locally on your Mac) to learn how you classify emails and progressively automates the sorting process. It starts by asking you about every email, learns your patterns, and eventually auto-classifies emails with high confidence.

**Key Benefits:**
- 🎯 Achieve Inbox Zero daily using proven productivity methodology
- 🤖 Local AI - no cloud services, completely private
- 📈 Progressive automation - learns your preferences over time
- 🗄️ Optional PostgreSQL backend for robust data storage
- 📊 Detailed statistics and accuracy tracking
- ⚡ Thread-level classification - classify conversation threads, not individual emails

## Features

### Learning System
- **Learning Mode (0-89% confidence)**: Asks about every email to build training data
- **Suggestion Mode (90-99% confidence)**: Suggests categories with option to override
- **Auto-Classification (100% confidence)**: Automatically sorts highly confident emails

### Inbox Zero Methodology

The system uses the battle-tested **Inbox Zero** approach with 6 action-oriented categories:

1. **Action/Do** ✅ - Requires immediate action (< 2 minutes to complete)
2. **Waiting For** ⏳ - Items you're waiting on from others (review weekly)
3. **Read/Reference** 📚 - Newsletters, articles, documentation to read later
4. **Archive** 📁 - Completed items (search when needed, don't browse)
5. **Spam** 🚫 - Junk and unwanted emails (trains filters)
6. **Delete** 🗑️ - Truly useless emails

**Philosophy**: Every email tells you what ACTION to take, not just what category it belongs to.

### Advanced Features
- **Thread Classification**: Groups email conversations and classifies them together
- **PostgreSQL Backend**: Optional robust storage with advanced querying
- **Server-Side Mailbox Sync**: Creates mailboxes in your Gmail/IMAP account, not locally
- **Multi-Account Support**: Process specific accounts or unified inbox
- **AI Summaries**: Optional AI-generated email summaries for better classification
- **Confidence Scoring**: Multiple factors determine classification confidence

## Requirements

- **macOS** with Apple Mail configured
- **Python 3.8+**
- **Ollama** (for local AI processing)
- **PostgreSQL** (optional, for better performance)

## Quick Start

### 1. Install Ollama

```bash
# Install Ollama
brew install ollama

# Download the AI model (this may take a few minutes)
ollama pull llama3.2:latest

# Start Ollama service (in background)
ollama serve &
```

### 2. Install Email Sorter

```bash
# Clone the repository
git clone https://github.com/pstoute/apple-email-sorter.git
cd apple-email-sorter

# Install Python dependencies
pip3 install -r requirements.txt
```

### 3. Configure Your Settings

**IMPORTANT**: If you cloned this repo, you should review `config.py` and update the PostgreSQL credentials:

```python
# In config.py, update these settings:
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "email_sorter",
    "user": "your_postgres_user",     # ⚠️ Change this
    "password": "your_postgres_pass"  # ⚠️ Change this
}
```

**Security Note**: The default PostgreSQL credentials in `config.py` are placeholders. Change them if you plan to use PostgreSQL. For JSON-only mode (no database), set `USE_POSTGRES = False`.

You can also customize categories and other settings in `config.py`:

```python
# Use Inbox Zero categories (recommended)
DEFAULT_CATEGORIES = [
    "Action/Do",           # Quick actions, <2 min
    "Waiting For",         # Tracking delegated items
    "Read/Reference",      # Newsletters, docs
    "Archive",             # Completed items
    "Spam",                # Junk/unwanted
    "Delete"               # Truly useless
]

# Choose your Ollama model
OLLAMA_MODEL = "llama3.2:latest"  # Fast and accurate

# Confidence thresholds
CONFIDENCE_THRESHOLD_SUGGEST = 0.90  # 90% to make suggestions
CONFIDENCE_THRESHOLD_AUTO = 1.00     # 100% to auto-classify
```

### 4. Test the Connection

```bash
# Run setup to verify everything works
python3 email_sorter.py --setup
```

Expected output:
```
✓ Connected to Apple Mail
✓ Connected to Ollama
✓ Test classification successful
✓ Setup complete!
```

### 5. Start Sorting!

```bash
# Try with a few emails first (dry run - won't move emails)
python3 email_sorter.py --limit 5 --dry-run

# Process your first 10 real emails
python3 email_sorter.py --limit 10

# Process specific account only (recommended for Gmail accounts)
python3 email_sorter.py --account "your@email.com" --unread-only true --limit 20
```

## Usage

### Basic Commands

```bash
# Process 10 emails from inbox
python3 email_sorter.py --limit 10

# Process only unread emails
python3 email_sorter.py --unread-only true

# Process specific account
python3 email_sorter.py --account "paul@example.com"

# Dry run (test without moving emails)
python3 email_sorter.py --limit 5 --dry-run

# Combination (recommended for daily use)
python3 email_sorter.py --account "paul@example.com" --unread-only true --limit 50
```

### Interactive Controls

During email review:
- **Type a number (1-6)**: Select that category
- **Press Enter**: Accept the suggested category (when AI is confident)
- **Type 's'**: Skip this email
- **Type 'c'**: Show email content preview
- **Type 'q'**: Quit and show summary

### Daily Inbox Zero Workflow

**Morning (15 minutes):**
```bash
python3 email_sorter.py --account "your@email.com" --unread-only true --limit 50
```

1. Process AI suggestions (Action/Do, Waiting For, Read/Reference, Archive)
2. Complete quick actions immediately (< 2 minutes)
3. Move longer tasks to todo list, then Archive the email
4. Goal: Inbox at 0

**Afternoon (10 minutes):**
- Check Action folder (should be < 20 emails)
- Complete remaining quick actions
- Process any new emails

**Weekly Review (30 minutes, Friday):**
- Review "Waiting For" folder - follow up on items > 3-5 days old
- Review "Read/Reference" folder - read important items
- Archive old newsletters (if unread after 2 weeks, not important)

## Configuration

### Ollama Models

In `config.py`:

```python
# Fast and accurate (recommended)
OLLAMA_MODEL = "llama3.2:latest"

# More powerful (slower)
OLLAMA_MODEL = "llama3.1:latest"

# Alternative models
OLLAMA_MODEL = "mistral:latest"
```

Download a model:
```bash
ollama pull llama3.2:latest
```

### Confidence Thresholds

Adjust how aggressive the AI is:

```python
# Conservative (more training required)
CONFIDENCE_THRESHOLD_SUGGEST = 0.95  # 95% to suggest
CONFIDENCE_THRESHOLD_AUTO = 1.00     # Never auto-classify

# Balanced (default)
CONFIDENCE_THRESHOLD_SUGGEST = 0.90  # 90% to suggest
CONFIDENCE_THRESHOLD_AUTO = 1.00     # 100% to auto-classify

# Aggressive (faster automation)
CONFIDENCE_THRESHOLD_SUGGEST = 0.85  # 85% to suggest
CONFIDENCE_THRESHOLD_AUTO = 0.95     # 95% to auto-classify
```

### Custom Categories

You can define your own categories:

```python
DEFAULT_CATEGORIES = [
    "Urgent",
    "Work",
    "Personal",
    "Later",
    "Trash"
]

MAILBOXES = {
    "Urgent": "Urgent",           # Maps to Apple Mail mailbox name
    "Work": "Work",
    "Personal": "Personal",
    "Later": "Later",
    "Trash": None                 # None = Delete the email
}
```

**Note**: Mailbox names must match folders in Apple Mail, or will be created automatically in your account (server-side).

### Account-Specific Processing

Process a specific email account:

```python
# In config.py
MAIL_ACCOUNT = "paul@example.com"  # Only process this account

# Or leave as None to process all accounts
MAIL_ACCOUNT = None
```

Or use command line:
```bash
python3 email_sorter.py --account "paul@example.com"
```

## PostgreSQL Backend (Optional but Recommended)

For better performance with large email volumes, use PostgreSQL:

### Quick Setup with Docker

```bash
# Start PostgreSQL container
docker run -d \
  --name email_sorter_db \
  -e POSTGRES_DB=email_sorter \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15

# Test connection
python3 db_storage.py
```

Expected output:
```
✓ Connected to PostgreSQL
✓ Can write to database
✓ Training examples in database: 0
```

### Enable in Configuration

Edit `config.py`:

```python
USE_POSTGRES = True

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "email_sorter",
    "user": "postgres",
    "password": "postgres"
}
```

### Why PostgreSQL?

- ⚡ **10x faster** queries with large training datasets
- 📊 **Advanced analytics** - SQL queries for insights
- 🔍 **Better search** - indexed lookups on sender, domain, category
- 🧵 **Thread support** - efficiently group email conversations
- 🔮 **Future ready** - supports vector embeddings for RAG

## How It Works

### Learning Process

1. **Initial Training (First 10-20 emails per category)**
   - System asks about every email
   - You classify each one manually
   - Builds training data from your decisions

2. **Pattern Recognition (After 20+ examples)**
   - AI identifies patterns in subjects, senders, content
   - Starts making suggestions at 90%+ confidence
   - You can accept or override suggestions

3. **Automation (After strong patterns emerge)**
   - Emails with 100% confidence auto-classified
   - No interruption for routine emails
   - You only see uncertain emails

### Confidence Calculation

The AI considers multiple factors:

- **AI Base Confidence**: Initial classification from Ollama
- **Domain History**: Sender domain consistency (e.g., all newsletters from `newsletter.com` → Read/Reference)
- **Content Similarity**: Comparison to previously classified emails
- **Historical Accuracy**: Past performance for this category
- **Thread Context**: Classification of related emails in conversation

### Thread Classification

Emails in the same conversation are grouped and classified together:

**Before Thread Classification:**
```
Email 1: "Project Update" → classify
Email 2: "Re: Project Update" → classify
Email 3: "RE: Project Update" → classify
Total: 3 classifications
```

**After Thread Classification:**
```
Thread: "Project Update" (3 emails) → classify once
All 3 emails get the same classification
Total: 1 classification (3x faster!)
```

### Data Storage

**JSON Mode (default):**
- Training data: `data/training_data.json`
- Statistics: `data/statistics.json`
- Simple, no setup required

**PostgreSQL Mode (recommended):**
- Training data in `emails` table
- Classifications in `classifications` table
- Statistics in `statistics` table
- Better performance, advanced queries

## Example Session

```
✉️  EMAIL SORTER - Inbox Zero Mode
============================================================

📧 Email 1 of 25
------------------------------------------------------------
From:    newsletter@example.com
Subject: Weekly Tech Updates - January 2025
Date:    2025-01-14

💡 Suggestion: Read/Reference
   Confidence: 92.0%

   This sender is typically classified as Read/Reference

What should I do with this email?

  → 1. Action/Do
    2. Waiting For
    3. Read/Reference
    4. Archive
    5. Spam
    6. Delete

  Enter: Accept suggestion
  s: Skip this email
  c: Show content preview
  q: Quit

Your choice: [Enter]
✓ Moved to: Read/Reference

📊 SESSION SUMMARY
============================================================

Total emails reviewed:           25

Emails needing your decision:    10    (40%)
  Manual classifications:        10

Emails with suggestions (90-99%): 12   (48%)
  ✓ Accepted:                     10
  ✗ Changed:                      2
  Suggestion accuracy:            83.3%

Emails auto-classified (100%):    3    (12%)

📁 CLASSIFICATION BREAKDOWN
------------------------------------------------------------
Read/Reference.................. 10 ██████████
Action/Do.......................  8 ████████
Archive.........................  4 ████
Waiting For.....................  2 ██
Spam............................  1 █

⏱️  Time: 3m 45s
📈 Overall accuracy: 87.5%
🎯 Inbox Zero achieved!
```

## Troubleshooting

### Ollama Issues

**Cannot connect to Ollama:**
```bash
# Start Ollama
ollama serve

# Test connection
curl http://localhost:11434/api/tags

# Check if model exists
ollama list
```

**Model not found:**
```bash
ollama pull llama3.2:latest
```

### Apple Mail Issues

**Permission denied:**
1. System Settings → Privacy & Security → Automation
2. Find your terminal app (Terminal, iTerm2, VS Code, etc.)
3. Enable "Mail" checkbox
4. Restart terminal

**Mailbox not found:**
- Mailboxes are created automatically in your account (server-side)
- Check `MAILBOXES` in `config.py` matches desired names
- Ensure Apple Mail is running

**AppleScript timeout (large inboxes):**
```bash
# Process specific account with smaller batches
python3 email_sorter.py --account "your@email.com" --limit 20
```

### PostgreSQL Issues

**Connection refused:**
```bash
# Check if container is running
docker ps | grep postgres

# Start container
docker start email_sorter_db
```

**Database doesn't exist:**
```bash
docker exec -it email_sorter_db psql -U postgres -c "CREATE DATABASE email_sorter;"
```

**Authentication failed:**
- Verify `POSTGRES_CONFIG` in `config.py`
- Check username/password match Docker settings

### Classification Issues

**Low confidence / No suggestions:**
- Need 10+ examples per category
- Be consistent in early classifications
- Reduce number of categories if spread too thin

**Wrong suggestions:**
- Override incorrect suggestions
- System learns from corrections
- Check if you're being consistent

**Slow processing:**
- Use faster model: `llama3.2:latest`
- Process smaller batches: `--limit 10`
- Enable PostgreSQL for better performance

## File Structure

```
email_sorter/
├── email_sorter.py          # Main application
├── config.py                # Configuration (customize this!)
├── apple_mail.py            # Apple Mail integration via AppleScript
├── ollama_classifier.py     # Ollama AI integration
├── training_manager.py      # Learning and confidence logic
├── interactive_ui.py        # User interface
├── db_storage.py            # PostgreSQL backend
├── thread_utils.py          # Thread/conversation grouping
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── data/                    # Created automatically
    ├── training_data.json   # Training examples (JSON mode)
    └── statistics.json      # Session statistics
```

## Privacy & Security

- ✅ **Completely local** - All processing on your Mac
- ✅ **No cloud services** - Ollama runs offline
- ✅ **No data sharing** - Training data stays on your machine
- ✅ **Optional database** - PostgreSQL runs locally (Docker or native)
- ✅ **Open source** - Inspect all code

## Performance Tips

1. **Start Small**: Use `--limit 10` for first few runs
2. **Be Consistent**: Classify similar emails the same way
3. **Use PostgreSQL**: For > 1000 emails, switch to PostgreSQL backend
4. **Process Regularly**: Daily runs prevent backlog
5. **Use Accounts**: Process specific accounts for faster results
6. **Unread Only**: `--unread-only true` focuses on what needs attention
7. **Thread Classification**: Automatically enabled with PostgreSQL

## Contributing

Contributions welcome! Ideas for enhancement:

- [ ] Gmail/IMAP direct integration (bypass Apple Mail)
- [ ] Web-based UI for statistics and management
- [ ] Email rules export for other clients
- [ ] Mobile app notifications
- [ ] Slack/Discord integration for important emails
- [ ] Calendar integration for meeting invites
- [ ] Smart reply suggestions

## License

MIT License - Free to use, modify, and distribute.

## Support

**Issues?**
1. Check Troubleshooting section above
2. Ensure all requirements are met
3. Test with `--dry-run` first
4. Check logs in `logs/email_sorter.log`

**Questions?**
- Review `config.py` for all options
- Test Ollama: `ollama list`
- Test database: `python3 db_storage.py`
- Test Apple Mail: `python3 apple_mail.py`

## Credits

Built with:
- [Ollama](https://ollama.ai) - Local AI models
- [PostgreSQL](https://www.postgresql.org/) - Robust database
- Apple Mail AppleScript - Email automation

Inspired by:
- [Inbox Zero](https://www.43folders.com/izero) methodology by Merlin Mann
- [Getting Things Done (GTD)](https://gettingthingsdone.com/) by David Allen

---

**Ready to achieve Inbox Zero?** Start with:

```bash
python3 email_sorter.py --account "your@email.com" --limit 10
```

Happy sorting! 📬✨
