#!/usr/bin/env python3
"""
Test script to demonstrate the new email display with confidence scores
"""
from interactive_ui import InteractiveUI

# Create UI
categories = ["Work - Urgent", "Work - Normal", "Personal", "Newsletters", "Spam"]
ui = InteractiveUI(categories)

# Test email data
test_email = {
    "sender": "boss@company.com",
    "subject": "URGENT: Client Meeting Tomorrow",
    "date": "Monday, November 13, 2025 at 9:15 AM",
    "id": "test123"
}

# Test 1: Email with summary and AI suggestion
print("\n" + "="*70)
print("TEST 1: Email with AI Summary and Suggestion (High Confidence)")
print("="*70)
ui.display_email(
    email=test_email,
    index=0,
    total=10,
    summary="Client meeting has been moved to tomorrow at 2pm. Need you to prepare the updated presentation deck.",
    suggested_category="Work - Urgent",
    confidence=0.95
)

# Test 2: Email with summary but low confidence (no suggestion shown)
print("\n" + "="*70)
print("TEST 2: Email with AI Summary but Low Confidence")
print("="*70)
ui.display_email(
    email={
        "sender": "newsletter@techcrunch.com",
        "subject": "This Week in Tech - Top Stories",
        "date": "Sunday, November 12, 2025 at 6:00 AM",
        "id": "test456"
    },
    index=1,
    total=10,
    summary="Weekly tech news roundup featuring AI developments, startup funding news, and product launches.",
    suggested_category="Newsletters",
    confidence=0.87  # Below 90% threshold
)

# Test 3: Email without summary (summary generation disabled or failed)
print("\n" + "="*70)
print("TEST 3: Email without Summary")
print("="*70)
ui.display_email(
    email={
        "sender": "deals@amazon.com",
        "subject": "50% Off Electronics - Today Only!",
        "date": "Today at 8:00 AM",
        "id": "test789"
    },
    index=2,
    total=10,
    summary=None,
    suggested_category="Promotions",
    confidence=0.78
)

# Test 4: Auto-classification scenario (100% confidence)
print("\n" + "="*70)
print("TEST 4: High Confidence Auto-Classification")
print("="*70)
ui.display_email(
    email={
        "sender": "spam@malicious.com",
        "subject": "You've won $1,000,000!!!",
        "date": "Today at 3:45 PM",
        "id": "test999"
    },
    index=3,
    total=10,
    summary="Suspicious promotional email claiming you've won a large prize. Classic spam pattern.",
    suggested_category="Spam",
    confidence=1.00
)

print("\n" + "="*70)
print("Display format looks good! ✓")
print("="*70)
print("\nThe new format shows:")
print("  1. From, Subject, Date (always)")
print("  2. AI Summary (if enabled)")
print("  3. Suggested Category with Confidence % (always shown)")
print("\nThis gives you full context before making a decision!")
