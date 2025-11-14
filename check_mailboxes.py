#!/usr/bin/env python3
"""
Check your current mailbox setup - local vs server-side
"""
from apple_mail import AppleMailClient

def main():
    print("="*70)
    print("YOUR APPLE MAIL MAILBOX SETUP")
    print("="*70)
    print()

    client = AppleMailClient()

    # Get all accounts
    accounts = client.list_accounts()

    print("📧 YOUR EMAIL ACCOUNTS:")
    print("-"*70)
    for i, account in enumerate(accounts, 1):
        print(f"  {i}. {account}")
    print()

    # Check server mailboxes for each account
    print("📁 SERVER-SIDE MAILBOXES (Sync to all devices):")
    print("-"*70)

    for account in accounts:
        script = f'''
        tell application "Mail"
            try
                set boxList to name of every mailbox of account "{account}"
                return boxList as string
            on error
                return "No mailboxes"
            end try
        end tell
        '''
        try:
            result = client._run_applescript(script, timeout=10)
            mailboxes = [m.strip() for m in result.split(',') if m.strip() and m.strip() != "No mailboxes"]

            if mailboxes:
                print(f"\n  {account}:")
                for mailbox in mailboxes:
                    print(f"    • {mailbox}")
            else:
                print(f"\n  {account}: No custom mailboxes")
        except Exception as e:
            print(f"\n  {account}: Error checking - {e}")

    print()
    print()

    # Check local mailboxes
    print("💻 LOCAL MAILBOXES (This Mac only - do NOT sync):")
    print("-"*70)

    script = '''
    tell application "Mail"
        name of every mailbox
    end tell
    '''
    try:
        result = client._run_applescript(script, timeout=10)
        all_mailboxes = [m.strip() for m in result.split(',')]

        # These are the local ones (not under an account)
        local_mailboxes = []
        for mb in all_mailboxes:
            if mb not in ['INBOX', 'Drafts', 'Sent', 'Trash', 'Junk', 'Archive',
                         'Deleted Items', 'Sent Items', 'Junk E-mail', 'Sent Messages',
                         'Deleted Messages', 'Notes', 'Outbox']:
                local_mailboxes.append(mb)

        if local_mailboxes:
            print("\n  On My Mac:")
            for mailbox in sorted(set(local_mailboxes)):
                print(f"    • {mailbox}")
        else:
            print("\n  No custom local mailboxes found")
    except Exception as e:
        print(f"\n  Error checking local mailboxes: {e}")

    print()
    print("="*70)
    print()

    print("⚠️  IMPORTANT:")
    print("-"*70)
    print("  • SERVER mailboxes sync to iPhone, iPad, other Macs, web")
    print("  • LOCAL mailboxes only exist on THIS Mac")
    print()
    print("📖 For detailed explanation, see: MAILBOX_STRATEGY.md")
    print()
    print("💡 RECOMMENDATION:")
    print("-"*70)
    print("  Create folders in your email account (NOT 'On My Mac') for syncing:")
    print()
    print("  1. Open Apple Mail")
    print("  2. Mailbox → New Mailbox...")
    print("  3. Location: Choose your email account (paul@stoute.co)")
    print("  4. Create: Work, Personal, Newsletters, Promotions")
    print()
    print("  Then update config.py to use those folders!")
    print()

if __name__ == "__main__":
    main()
