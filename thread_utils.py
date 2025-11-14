"""
Thread/Conversation utilities for grouping related emails
"""
import re
import hashlib
from typing import List, Dict, Tuple


def normalize_subject(subject: str) -> str:
    """
    Normalize an email subject for thread matching

    Removes:
    - Re:, RE:, re: prefixes
    - Fwd:, FW:, fwd: prefixes
    - Multiple spaces
    - Leading/trailing whitespace
    - Case differences

    Args:
        subject: Original email subject

    Returns:
        Normalized subject string
    """
    if not subject:
        return ""

    # Remove Re:, Fwd: and variations (case insensitive)
    # Matches: Re:, RE:, re:, Fwd:, FW:, fw:, etc.
    normalized = re.sub(r'^(re|fwd?|fw):\s*', '', subject, flags=re.IGNORECASE)

    # Keep removing until no more prefixes (handles Re: Re: Re: cases)
    while True:
        new_normalized = re.sub(r'^(re|fwd?|fw):\s*', '', normalized, flags=re.IGNORECASE)
        if new_normalized == normalized:
            break
        normalized = new_normalized

    # Remove extra whitespace and normalize
    normalized = ' '.join(normalized.split())
    normalized = normalized.strip().lower()

    return normalized


def generate_thread_id(normalized_subject: str, sender_domain: str) -> str:
    """
    Generate a unique thread ID based on normalized subject and sender domain

    This creates a consistent ID for emails in the same thread/conversation.
    Emails with the same normalized subject from the same domain are considered
    part of the same thread.

    Args:
        normalized_subject: Normalized email subject
        sender_domain: Domain of the sender (e.g., "example.com")

    Returns:
        Thread ID (SHA256 hash of subject + domain)
    """
    # Create a consistent string for hashing
    thread_key = f"{normalized_subject}|{sender_domain}".lower()

    # Generate SHA256 hash (shortened to first 16 chars for readability)
    thread_hash = hashlib.sha256(thread_key.encode()).hexdigest()[:16]

    return thread_hash


def extract_domain(email: str) -> str:
    """
    Extract domain from email address

    Args:
        email: Email address (can be "Name <email@domain.com>" or "email@domain.com")

    Returns:
        Domain string (e.g., "domain.com")
    """
    # Handle "Name <email@domain.com>" format
    if '<' in email and '>' in email:
        email = email.split('<')[1].split('>')[0]

    # Extract domain
    if '@' in email:
        return email.split('@')[1].lower().strip()

    return ""


def group_emails_by_thread(emails: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group a list of emails by thread ID

    Args:
        emails: List of email dicts with 'subject' and 'sender' keys

    Returns:
        Dict mapping thread_id to list of emails in that thread
    """
    threads = {}

    for email in emails:
        subject = email.get('subject', '')
        sender = email.get('sender', '')

        normalized_subject = normalize_subject(subject)
        sender_domain = extract_domain(sender)
        thread_id = generate_thread_id(normalized_subject, sender_domain)

        # Add thread metadata to email
        email['normalized_subject'] = normalized_subject
        email['thread_id'] = thread_id
        email['sender_domain'] = sender_domain

        # Group by thread
        if thread_id not in threads:
            threads[thread_id] = []
        threads[thread_id].append(email)

    return threads


def get_thread_summary(thread_emails: List[Dict]) -> str:
    """
    Generate a summary for a thread of emails

    Args:
        thread_emails: List of emails in the thread

    Returns:
        Human-readable summary string
    """
    if not thread_emails:
        return "Empty thread"

    count = len(thread_emails)
    first_email = thread_emails[0]
    subject = first_email.get('subject', 'Unknown')
    sender_domain = first_email.get('sender_domain', 'unknown')

    if count == 1:
        return f'"{subject}" from {sender_domain}'
    else:
        return f'"{subject}" from {sender_domain} ({count} emails)'


if __name__ == "__main__":
    # Test the functions
    test_subjects = [
        "Project Update",
        "Re: Project Update",
        "RE: Re: Project Update",
        "Fwd: Project Update",
        "FW: RE: Project Update",
        "  re:  project update  ",  # Different case and spacing
    ]

    print("Subject Normalization Tests:")
    print("=" * 60)
    for subject in test_subjects:
        normalized = normalize_subject(subject)
        print(f'"{subject}" → "{normalized}"')

    print("\n" + "=" * 60)
    print("\nThread ID Generation:")
    print("=" * 60)

    test_emails = [
        {"subject": "Project Update", "sender": "alice@company.com"},
        {"subject": "Re: Project Update", "sender": "bob@company.com"},
        {"subject": "RE: Project Update", "sender": "charlie@company.com"},
        {"subject": "Different Topic", "sender": "alice@company.com"},
    ]

    threads = group_emails_by_thread(test_emails)

    for thread_id, emails in threads.items():
        summary = get_thread_summary(emails)
        print(f"\nThread {thread_id}:")
        print(f"  {summary}")
        for email in emails:
            print(f"    - {email['subject']} from {email['sender']}")
