#!/usr/bin/env python3
"""
Main Email Sorter Application
"""
import sys
import argparse
from typing import Dict, List
from datetime import datetime

from apple_mail import AppleMailClient
from ollama_classifier import OllamaClassifier
from training_manager import TrainingManager
from interactive_ui import InteractiveUI
from logger import setup_logger, log_exception
from thread_utils import group_emails_by_thread, get_thread_summary
from config import (
    DEFAULT_CATEGORIES,
    MAILBOXES,
    CONFIDENCE_THRESHOLD_SUGGEST,
    CONFIDENCE_THRESHOLD_AUTO,
    USE_POSTGRES,
    POSTGRES_CONFIG,
    MAIL_ACCOUNT,
    ENABLE_AI_SUMMARY,
    SUMMARY_MAX_LENGTH,
    LOG_FILE
)

# Set up logger for this module
logger = setup_logger("email_sorter")

# Optional PostgreSQL support
if USE_POSTGRES:
    try:
        from db_storage import PostgresStorage, PostgresTrainingManager
        POSTGRES_AVAILABLE = True
    except ImportError:
        print("Warning: psycopg2 not installed. Falling back to JSON storage.")
        POSTGRES_AVAILABLE = False
else:
    POSTGRES_AVAILABLE = False


class EmailSorter:
    """Main email sorting application"""

    def __init__(self, categories: List[str] = None, dry_run: bool = False, account: str = None):
        self.categories = categories or DEFAULT_CATEGORIES
        self.dry_run = dry_run

        # Initialize components
        self.mail_client = AppleMailClient(account_name=account or MAIL_ACCOUNT)
        self.classifier = OllamaClassifier()

        # Initialize storage backend
        if USE_POSTGRES and POSTGRES_AVAILABLE:
            try:
                storage = PostgresStorage(**POSTGRES_CONFIG)
                self.training_manager = PostgresTrainingManager(storage)
                self.using_postgres = True
                print("✓ Using PostgreSQL storage backend")
            except Exception as e:
                print(f"Warning: PostgreSQL connection failed: {e}")
                print("Falling back to JSON storage")
                self.training_manager = TrainingManager()
                self.using_postgres = False
        else:
            self.training_manager = TrainingManager()
            self.using_postgres = False

        # Fetch available mailboxes dynamically
        print("📁 Fetching available mailboxes...")
        self.available_mailboxes = self.mail_client.get_available_mailboxes()
        if self.available_mailboxes:
            print(f"   Found {len(self.available_mailboxes)} custom mailboxes")
        else:
            print("   No custom mailboxes found (will use standard folders)")

        self.ui = InteractiveUI(self.categories, available_mailboxes=self.available_mailboxes)

        # Session statistics
        self.stats = {
            "total_reviewed": 0,
            "manual_review": 0,
            "suggested": 0,
            "suggestions_accepted": 0,
            "suggestions_rejected": 0,
            "auto_classified": 0,
            "skipped": 0,
            "by_category": {}
        }

    def run(self, limit: int = None, unread_only: bool = None):
        """
        Run the email sorter

        Args:
            limit: Maximum number of emails to process
            unread_only: If True, only process unread emails. If False, only process read emails.
                        If None, process all emails.
        """
        self.ui.display_welcome()

        # Check connections
        if not self._check_connections():
            return False

        # Get emails from inbox
        self.ui.display_info("Fetching emails from inbox...")
        emails = self.mail_client.get_inbox_messages(limit=limit, unread_only=unread_only)

        if not emails:
            self.ui.display_info("No emails found in inbox.")
            return True

        self.ui.display_success(f"Found {len(emails)} emails to process")

        # Process each email
        for i, email in enumerate(emails):
            self.ui.display_progress(i, len(emails))

            result = self._process_email(email, i, len(emails))

            if result == "QUIT":
                print("\n\nQuitting...")
                break
            elif result == "SKIP":
                self.stats["skipped"] += 1

            self.stats["total_reviewed"] += 1

        # Display final summary
        self._display_final_report()

        return True

    def _check_connections(self) -> bool:
        """Check connections to required services"""
        # Check Ollama
        if not self.classifier.test_connection():
            self.ui.display_error(
                "Cannot connect to Ollama. Please ensure it's running:\n"
                "  $ ollama serve"
            )
            return False

        # Check Apple Mail
        try:
            self.mail_client.get_inbox_messages(limit=1)
        except Exception as e:
            self.ui.display_error(
                f"Cannot connect to Apple Mail. Please ensure it's running.\n"
                f"Error: {e}"
            )
            return False

        return True

    def _process_email(self, email: Dict, index: int, total: int) -> str:
        """
        Process a single email

        Returns:
            "OK", "SKIP", or "QUIT"
        """
        # Get email content (for classification and summary)
        try:
            content = self.mail_client.get_message_content(email['id'])
        except Exception as e:
            print(f"Warning: Could not fetch email content: {e}")
            content = ""

        # Generate AI summary for context (if enabled)
        summary = None
        if ENABLE_AI_SUMMARY:
            print("⏳ Generating summary...")
            try:
                summary = self.classifier.summarize_email(
                    subject=email['subject'],
                    sender=email['sender'],
                    content=content,
                    max_length=SUMMARY_MAX_LENGTH
                )
                logger.debug(f"Summary generated successfully: {summary[:50]}...")
            except Exception as e:
                log_exception(logger, "Failed to generate email summary", e)
                print(f"Note: Summary unavailable - check {LOG_FILE} for details")
                summary = None

        # Classify email (always do this to show prediction)
        training_examples = self.training_manager.get_recent_examples(limit=10)
        predicted_category, base_confidence = self.classifier.classify_email(
            subject=email['subject'],
            sender=email['sender'],
            content=content,
            categories=self.categories,
            training_examples=training_examples
        )

        # Compute adjusted confidence with training data
        adjusted_confidence = self.training_manager.compute_confidence(
            subject=email['subject'],
            sender=email['sender'],
            content=content,
            predicted_category=predicted_category,
            base_confidence=base_confidence,
            similarity_scorer=self.classifier.compute_similarity
        )

        # Display email with summary AND AI prediction
        self.ui.display_email(
            email,
            index,
            total,
            summary=summary,
            suggested_category=predicted_category,
            confidence=adjusted_confidence
        )

        # Determine action based on confidence
        if self.training_manager.should_auto_classify(adjusted_confidence):
            # Auto-classify with 100% confidence
            return self._handle_auto_classification(
                email, content, predicted_category, adjusted_confidence
            )
        elif self.training_manager.should_suggest(adjusted_confidence):
            # Suggest with 90-99% confidence
            return self._handle_suggested_classification(
                email, content, predicted_category, adjusted_confidence
            )
        else:
            # Ask user (learning mode)
            return self._handle_manual_classification(
                email, content, predicted_category, adjusted_confidence
            )

    def _handle_auto_classification(
        self,
        email: Dict,
        content: str,
        category: str,
        confidence: float
    ) -> str:
        """Handle automatic classification (100% confidence)"""
        print(f"🤖 Auto-classifying as: {category} ({confidence:.1%} confidence)")

        # Apply classification
        success = self._apply_classification(email['id'], category)

        if success:
            self.stats["auto_classified"] += 1
            self._update_category_stats(category)

            # Record in training data
            if self.using_postgres:
                self.training_manager.add_training_example(
                    email_id=email['id'],
                    subject=email['subject'],
                    sender=email['sender'],
                    content=content,
                    category=category,
                    account=self.mail_client.account_name,
                    confidence=confidence,
                    user_decision=False  # Auto-classified
                )
            else:
                self.training_manager.add_training_example(
                    email_id=email['id'],
                    subject=email['subject'],
                    sender=email['sender'],
                    content=content,
                    category=category,
                    user_decision=False  # Auto-classified
                )

            print("✓ Done\n")
        else:
            print("✗ Failed to classify\n")

        return "OK"

    def _handle_suggested_classification(
        self,
        email: Dict,
        content: str,
        suggested_category: str,
        confidence: float
    ) -> str:
        """Handle suggested classification (90-99% confidence)"""
        self.stats["suggested"] += 1

        # Ask user with suggestion
        selected_category, accepted = self.ui.get_user_decision(
            email,
            suggested_category=suggested_category,
            confidence=confidence
        )

        if selected_category == "QUIT":
            return "QUIT"
        elif selected_category == "SKIP":
            return "SKIP"

        # Track whether suggestion was accepted
        if accepted:
            self.stats["suggestions_accepted"] += 1
            if self.using_postgres:
                self.training_manager.record_prediction_result(
                    email_id=email['id'],
                    predicted=suggested_category,
                    actual=selected_category,
                    confidence=confidence
                )
            else:
                self.training_manager.record_prediction_result(was_correct=True)
        else:
            self.stats["suggestions_rejected"] += 1
            if self.using_postgres:
                self.training_manager.record_prediction_result(
                    email_id=email['id'],
                    predicted=suggested_category,
                    actual=selected_category,
                    confidence=confidence
                )
            else:
                self.training_manager.record_prediction_result(was_correct=False)

        # Apply classification
        success = self._apply_classification(email['id'], selected_category)

        if success:
            self._update_category_stats(selected_category)

            # Record in training data
            if self.using_postgres:
                self.training_manager.add_training_example(
                    email_id=email['id'],
                    subject=email['subject'],
                    sender=email['sender'],
                    content=content,
                    category=selected_category,
                    account=self.mail_client.account_name,
                    confidence=confidence,
                    user_decision=True
                )
            else:
                self.training_manager.add_training_example(
                    email_id=email['id'],
                    subject=email['subject'],
                    sender=email['sender'],
                    content=content,
                    category=selected_category,
                    user_decision=True
                )

            print(f"✓ Classified as: {selected_category}\n")
        else:
            print("✗ Failed to classify\n")

        return "OK"

    def _handle_manual_classification(
        self,
        email: Dict,
        content: str,
        suggested_category: str,
        confidence: float
    ) -> str:
        """Handle manual classification (learning mode)"""
        self.stats["manual_review"] += 1

        # Ask user
        selected_category, _ = self.ui.get_user_decision(
            email,
            suggested_category=suggested_category,
            confidence=confidence
        )

        if selected_category == "QUIT":
            return "QUIT"
        elif selected_category == "SKIP":
            return "SKIP"

        # Apply classification
        success = self._apply_classification(email['id'], selected_category)

        if success:
            self._update_category_stats(selected_category)

            # Record in training data
            if self.using_postgres:
                self.training_manager.add_training_example(
                    email_id=email['id'],
                    subject=email['subject'],
                    sender=email['sender'],
                    content=content,
                    category=selected_category,
                    account=self.mail_client.account_name,
                    confidence=confidence,
                    user_decision=True
                )
            else:
                self.training_manager.add_training_example(
                    email_id=email['id'],
                    subject=email['subject'],
                    sender=email['sender'],
                    content=content,
                    category=selected_category,
                    user_decision=True
                )

            print(f"✓ Classified as: {selected_category}\n")
        else:
            print("✗ Failed to classify\n")

        return "OK"

    def _apply_classification(self, email_id: str, category: str) -> bool:
        """
        Apply the classification to the email

        Args:
            email_id: Email message ID
            category: Either a category name (mapped via MAILBOXES) or a direct mailbox name

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"[DRY RUN] Would move email to: {category}")
            return True

        # Check if this is a mapped category or a direct mailbox name
        if category in MAILBOXES:
            # This is a category - use the mapping
            mailbox = MAILBOXES[category]
            if mailbox is None:
                # Delete category
                return self.mail_client.delete_message(email_id)
        elif category in self.available_mailboxes:
            # This is a direct mailbox name from the dynamic list
            mailbox = category
        else:
            # Treat as a custom mailbox name (user typed it manually)
            mailbox = category

        # Move to mailbox
        # First ensure mailbox exists (create if it doesn't)
        self.mail_client.create_mailbox(mailbox)
        return self.mail_client.move_message_to_mailbox(email_id, mailbox)

    def _update_category_stats(self, category: str):
        """Update category statistics"""
        if category not in self.stats["by_category"]:
            self.stats["by_category"][category] = 0
        self.stats["by_category"][category] += 1

    def _display_final_report(self):
        """Display final session report"""
        print("\n")
        self.ui.display_summary(self.stats)

        if self.stats["by_category"]:
            self.ui.display_category_breakdown(self.stats["by_category"])

        # Save session statistics to database
        if self.using_postgres:
            try:
                storage = self.training_manager.storage
                storage.save_session_statistics(self.stats)
                logger.debug(f"Saved session statistics to database: {self.stats}")
            except Exception as e:
                logger.warning(f"Could not save session statistics: {e}")

        # Display training statistics
        training_stats = self.training_manager.get_statistics()
        print("📚 LEARNING PROGRESS")
        self.ui._print_separator()
        print(f"Total training examples: {training_stats['total_examples']}")
        print()

        if training_stats.get('correct_predictions', 0) > 0 or training_stats.get('incorrect_predictions', 0) > 0:
            total_predictions = training_stats['correct_predictions'] + training_stats['incorrect_predictions']
            accuracy = (training_stats['correct_predictions'] / total_predictions) * 100
            print(f"Suggestion accuracy:     {accuracy:.1f}%")
            print(f"  ✓ Correct:             {training_stats['correct_predictions']}")
            print(f"  ✗ Incorrect:           {training_stats['incorrect_predictions']}")
            print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Intelligent email sorter using Ollama AI"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of emails to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually move/delete emails"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup mailboxes and test connections"
    )
    parser.add_argument(
        "--account",
        type=str,
        help="Process only this account (e.g., 'iCloud', 'paul@stoute.co')"
    )
    parser.add_argument(
        "--list-accounts",
        action="store_true",
        help="List all available Mail accounts"
    )
    parser.add_argument(
        "--unread-only",
        type=lambda x: x.lower() == "true",
        default=None,
        metavar="true|false",
        help="Filter emails by read status: 'true' for unread only, 'false' for read only, omit for all"
    )

    args = parser.parse_args()

    if args.list_accounts:
        print("Available Mail accounts:")
        from apple_mail import AppleMailClient
        client = AppleMailClient()
        accounts = client.list_accounts()
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. {account}")
        print(f"\nTo use a specific account, add: --account \"{accounts[0]}\"")
        return

    if args.setup:
        print("Running setup...\n")
        # Test connections
        from apple_mail import test_connection as test_mail
        from ollama_classifier import test_ollama

        test_mail()
        print()
        test_ollama()

        print("\n✓ Setup complete!")
        return

    # Run email sorter
    sorter = EmailSorter(dry_run=args.dry_run, account=args.account if hasattr(args, "account") else None)
    sorter.run(limit=args.limit, unread_only=args.unread_only)


if __name__ == "__main__":
    main()
