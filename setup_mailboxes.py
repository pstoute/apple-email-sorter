#!/usr/bin/env python3
"""
Setup all mailboxes needed for email sorting
Run this once to create all mailboxes in Apple Mail
"""
from apple_mail import AppleMailClient
from config import MAILBOXES

def main():
    print("Setting up mailboxes in Apple Mail...\n")

    client = AppleMailClient()

    # Get unique mailbox paths (excluding None for Delete)
    mailbox_paths = set()
    for category, mailbox in MAILBOXES.items():
        if mailbox:  # Skip None (Delete category)
            mailbox_paths.add(mailbox)

    success_count = 0
    fail_count = 0

    for mailbox_path in sorted(mailbox_paths):
        print(f"Creating mailbox: {mailbox_path}...")
        if client.create_mailbox(mailbox_path):
            print(f"  ✓ Created/verified: {mailbox_path}")
            success_count += 1
        else:
            print(f"  ✗ Failed: {mailbox_path}")
            fail_count += 1
        print()

    print("\n" + "="*60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print("="*60)

    if fail_count > 0:
        print("\nTo create failed mailboxes manually:")
        print("1. Open Apple Mail")
        print("2. Mailbox → New Mailbox...")
        print("3. Create the mailboxes listed above")
    else:
        print("\n✓ All mailboxes ready!")
        print("\nYou can now run:")
        print("  python3 email_sorter.py --account \"paul@stoute.co\" --limit 10")

if __name__ == "__main__":
    main()
