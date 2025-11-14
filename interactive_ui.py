"""
Interactive UI for Email Review
"""
import sys
from typing import Dict, List, Optional, Tuple


class InteractiveUI:
    """Terminal-based interactive UI for email review"""

    def __init__(self, categories: List[str], available_mailboxes: Optional[List[str]] = None):
        """
        Initialize UI

        Args:
            categories: List of category names for classification
            available_mailboxes: Optional list of available mailboxes from Apple Mail
        """
        self.categories = categories
        self.available_mailboxes = available_mailboxes or []

    def display_email(
        self,
        email: Dict,
        index: int,
        total: int,
        summary: str = None,
        suggested_category: str = None,
        confidence: float = None
    ):
        """
        Display email details

        Args:
            email: Email dict with sender, subject, date, etc.
            index: Current email index (0-based)
            total: Total number of emails
            summary: Optional AI-generated summary
            suggested_category: Optional AI suggested category
            confidence: Optional confidence score (0-1)
        """
        self._print_separator()
        print(f"\n📧 Email {index + 1} of {total}")
        self._print_separator()
        print(f"From:    {email['sender']}")
        print(f"Subject: {email['subject']}")
        print(f"Date:    {email.get('date', 'Unknown')}")

        if summary:
            print(f"\n📝 AI Summary: {summary}")

        if suggested_category and confidence is not None:
            print(f"\n💡 Suggested Category (Confidence): {suggested_category} ({confidence:.1%})")

        print()

    def get_user_decision(
        self,
        email: Dict,
        suggested_category: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> Tuple[str, bool]:
        """
        Get user decision for email classification

        Returns:
            Tuple of (selected_category, user_accepted_suggestion)
        """
        # Suggestion and confidence are now shown in display_email()
        # No need to repeat them here

        print("What should I do with this email?")
        print()

        # Display categories with numbers
        for i, category in enumerate(self.categories, 1):
            marker = "→" if category == suggested_category else " "
            print(f"  {marker} {i}. {category}")

        print()
        if suggested_category:
            print("  Enter: Accept suggestion")
        print("  s: Skip this email")
        print("  c: Show content preview")
        print("  m: Choose mailbox manually")
        print("  q: Quit")
        print()

        while True:
            choice = input("Your choice: ").strip()

            # Accept suggestion
            if choice == "" and suggested_category:
                return suggested_category, True

            # Quit
            if choice.lower() == "q":
                return "QUIT", False

            # Skip
            if choice.lower() == "s":
                return "SKIP", False

            # Show content
            if choice.lower() == "c":
                self._show_content_preview(email)
                continue

            # Manual mailbox selection
            if choice.lower() == "m":
                mailbox = self._choose_mailbox()
                if mailbox:
                    return mailbox, False
                continue

            # Category selection
            try:
                category_index = int(choice) - 1
                if 0 <= category_index < len(self.categories):
                    selected_category = self.categories[category_index]
                    # Check if user accepted suggestion
                    accepted = (selected_category == suggested_category)
                    return selected_category, accepted
                else:
                    print(f"Invalid choice. Please enter 1-{len(self.categories)}")
            except ValueError:
                print(f"Invalid input. Please enter a number 1-{len(self.categories)}, or s/c/m/q")

    def _choose_mailbox(self) -> Optional[str]:
        """Let user choose from available mailboxes or type a custom name"""
        print("\n" + "="*60)
        print("CHOOSE MAILBOX")
        print("="*60)

        if self.available_mailboxes:
            print("\nAvailable mailboxes:")
            for i, mailbox in enumerate(self.available_mailboxes, 1):
                print(f"  {i}. {mailbox}")
            print()
            print("Enter number to select, or type a custom mailbox name:")
            print("(Press Enter to cancel)")
        else:
            print("\nType the mailbox name where you want to move this email:")
            print("(Press Enter to cancel)")

        print()
        choice = input("Mailbox: ").strip()

        if not choice:
            return None

        # Check if it's a number (selecting from list)
        if self.available_mailboxes:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.available_mailboxes):
                    return self.available_mailboxes[idx]
            except ValueError:
                pass

        # Otherwise, treat as custom mailbox name
        return choice

    def _show_content_preview(self, email: Dict):
        """Show a preview of email content"""
        print("\n" + "="*60)
        print("CONTENT PREVIEW")
        print("="*60)

        # Note: We'd need to fetch full content here
        # For now, show what we have
        if 'content' in email:
            preview = email['content'][:500]
            print(preview)
            if len(email['content']) > 500:
                print("\n... (truncated)")
        else:
            print("(Content not loaded)")

        print("="*60 + "\n")

    def display_summary(self, stats: Dict):
        """Display session summary"""
        self._print_separator("=")
        print("\n📊 SESSION SUMMARY")
        self._print_separator("=")
        print()

        print(f"Total emails reviewed:           {stats['total_reviewed']}")
        print()

        print(f"Emails needing your decision:    {stats['manual_review']}")

        if stats['suggested'] > 0:
            suggestion_accuracy = (stats['suggestions_accepted'] / stats['suggested']) * 100
            print(f"\nEmails with suggestions (90-99%): {stats['suggested']}")
            print(f"  ✓ Accepted:                     {stats['suggestions_accepted']}")
            print(f"  ✗ Changed:                      {stats['suggestions_rejected']}")
            print(f"  Accuracy:                       {suggestion_accuracy:.1f}%")

        if stats['auto_classified'] > 0:
            print(f"\nEmails auto-classified (100%):    {stats['auto_classified']}")

        if stats['skipped'] > 0:
            print(f"\nEmails skipped:                   {stats['skipped']}")

        print()
        self._print_separator("=")
        print()

    def display_category_breakdown(self, breakdown: Dict[str, int]):
        """Display breakdown by category"""
        print("📁 CLASSIFICATION BREAKDOWN")
        self._print_separator()
        for category, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * min(count, 30)
            print(f"{category:.<30} {count:>3} {bar}")
        print()

    def confirm_action(self, message: str) -> bool:
        """Ask user for yes/no confirmation"""
        while True:
            response = input(f"{message} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")

    def display_welcome(self):
        """Display welcome message"""
        self._print_separator("=")
        print("\n✉️  EMAIL SORTER - Learning Mode")
        self._print_separator("=")
        print()
        print("I'll help you sort your emails and learn your preferences.")
        print()
        print("How it works:")
        print("  • Initially, I'll ask you about every email")
        print("  • At 90%+ confidence, I'll suggest what to do")
        print("  • At 100% confidence, I'll handle emails automatically")
        print()
        self._print_separator()
        print()

    def display_progress(self, current: int, total: int):
        """Display progress bar"""
        if total == 0:
            return

        percentage = (current / total) * 100
        bar_length = 40
        filled = int((current / total) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        sys.stdout.write(f"\r  Progress: [{bar}] {percentage:.1f}% ({current}/{total})")
        sys.stdout.flush()

        if current == total:
            print()  # New line when complete

    def _print_separator(self, char: str = "-", length: int = 60):
        """Print a separator line"""
        print(char * length)

    def display_error(self, message: str):
        """Display an error message"""
        print(f"\n❌ Error: {message}\n")

    def display_success(self, message: str):
        """Display a success message"""
        print(f"\n✓ {message}\n")

    def display_info(self, message: str):
        """Display an info message"""
        print(f"\nℹ️  {message}\n")


if __name__ == "__main__":
    # Test UI
    ui = InteractiveUI(["Work", "Personal", "Spam", "Archive"])
    ui.display_welcome()

    test_email = {
        "subject": "Test Email",
        "sender": "test@example.com",
        "date": "2025-01-13"
    }

    ui.display_email(test_email, 0, 1)
    category, accepted = ui.get_user_decision(
        test_email,
        suggested_category="Work",
        confidence=0.92
    )

    print(f"\nSelected: {category}, Accepted: {accepted}")
