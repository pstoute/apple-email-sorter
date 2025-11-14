#!/usr/bin/env python3
"""
Utility script to list Mail accounts
"""
from apple_mail import AppleMailClient

def main():
    print("Available Mail accounts:")
    print()
    
    client = AppleMailClient()
    accounts = client.list_accounts()
    
    for i, account in enumerate(accounts, 1):
        print(f"  {i}. {account}")
    
    print()
    print("To process a specific account:")
    print(f'  python3 email_sorter.py --account "{accounts[0]}"')
    print()
    print("Or edit config.py and set:")
    print(f'  MAIL_ACCOUNT = "{accounts[0]}"')

if __name__ == "__main__":
    main()
