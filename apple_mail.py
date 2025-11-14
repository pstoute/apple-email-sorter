"""
Apple Mail Integration using AppleScript
"""
import subprocess
import json
from typing import List, Dict, Optional
from logger import setup_logger, log_exception

# Set up logger for this module
logger = setup_logger("apple_mail")


class AppleMailClient:
    """Interface to Apple Mail via AppleScript"""

    def __init__(self, account_name: Optional[str] = None):
        """
        Initialize Apple Mail client

        Args:
            account_name: Optional account name to filter by (e.g., "iCloud", "paul@stoute.co")
                         If None, uses unified inbox (all accounts)
        """
        self.account_name = account_name
        self._validate_account()

    def _validate_account(self):
        """Validate the account exists if one is specified"""
        if self.account_name:
            try:
                accounts = self.list_accounts()
                if self.account_name not in accounts:
                    print(f"Warning: Account '{self.account_name}' not found")
                    print(f"Available accounts: {', '.join(accounts)}")
            except Exception:
                pass  # Will fail later with better error message

    def list_accounts(self) -> List[str]:
        """Get list of all configured accounts"""
        script = 'tell application "Mail" to get name of every account'
        result = self._run_applescript(script, timeout=5)
        return [acc.strip() for acc in result.split(',')]

    def get_available_mailboxes(self, account_name: Optional[str] = None) -> List[str]:
        """
        Get list of all available mailboxes for an account or all accounts

        Args:
            account_name: Optional account name. If None, uses current account or all accounts

        Returns:
            List of mailbox names
        """
        target_account = account_name or self.account_name

        if target_account:
            script = f'''
            tell application "Mail"
                try
                    set boxList to name of every mailbox of account "{target_account}"
                    set AppleScript's text item delimiters to ","
                    set boxString to boxList as text
                    set AppleScript's text item delimiters to ""
                    return boxString
                on error
                    return ""
                end try
            end tell
            '''
        else:
            # Get all mailboxes from all accounts
            script = '''
            tell application "Mail"
                set allBoxes to {}
                repeat with acc in accounts
                    try
                        set boxList to name of every mailbox of acc
                        set allBoxes to allBoxes & boxList
                    end try
                end repeat
                set AppleScript's text item delimiters to ","
                set boxString to allBoxes as text
                set AppleScript's text item delimiters to ""
                return boxString
            end tell
            '''

        try:
            result = self._run_applescript(script, timeout=10)
            if not result:
                return []

            # Parse comma-separated list and clean up
            mailboxes = [mb.strip() for mb in result.split(',') if mb.strip()]

            # Remove duplicates and standard folders, keep user-created ones
            standard_folders = {
                'INBOX', 'Drafts', 'Sent', 'Trash', 'Junk', 'Archive',
                'Deleted Items', 'Sent Items', 'Junk E-mail', 'Sent Mail',
                'Sent Messages', 'Deleted Messages', 'Notes', 'Outbox',
                'All Mail', 'Starred'
            }

            # Filter and sort
            custom_mailboxes = [mb for mb in mailboxes if mb not in standard_folders]
            return sorted(set(custom_mailboxes))

        except Exception as e:
            print(f"Warning: Could not fetch mailboxes: {e}")
            return []

    @staticmethod
    def _run_applescript(script: str, timeout: int = 30) -> str:
        """Execute AppleScript and return output"""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception("AppleScript timeout - Apple Mail may be busy or inbox is very large")
        except subprocess.CalledProcessError as e:
            print(f"AppleScript error: {e.stderr}")
            raise

    def get_inbox_messages(self, limit: Optional[int] = None, unread_only: Optional[bool] = None) -> List[Dict]:
        """
        Get messages from inbox

        Args:
            limit: Maximum number of messages to fetch
            unread_only: If True, only fetch unread messages. If False, only fetch read messages.
                        If None, fetch all messages.

        Returns:
            List of dicts with message details
        """
        # First, check if Mail is running
        check_script = 'tell application "System Events" to (name of processes) contains "Mail"'
        try:
            is_running = self._run_applescript(check_script, timeout=5)
            if is_running.lower() != "true":
                raise Exception("Apple Mail is not running. Please open Mail.app")
        except Exception as e:
            raise Exception(f"Cannot check if Mail is running: {e}")

        # Get count of messages
        if self.account_name:
            print(f"Checking inbox for account: {self.account_name}...")
            count_script = f'''
            tell application "Mail"
                count messages of mailbox "INBOX" of account "{self.account_name}"
            end tell
            '''
        else:
            print("Checking inbox (all accounts)...")
            count_script = 'tell application "Mail" to count messages of inbox'

        try:
            count_str = self._run_applescript(count_script, timeout=10)
            count = int(count_str)
        except Exception as e:
            raise Exception(f"Cannot access inbox: {e}")

        if count == 0:
            return []

        # Apply limit
        if limit:
            count = min(count, limit)

        filter_msg = ""
        if unread_only is True:
            filter_msg = " (unread only)"
        elif unread_only is False:
            filter_msg = " (read only)"

        print(f"Fetching {count} message(s){filter_msg}...")

        # Get messages one at a time for reliability
        return self._get_messages_iterative(count, unread_only=unread_only)

    def _get_messages_iterative(self, count: int, unread_only: Optional[bool] = None) -> List[Dict]:
        """
        Get messages one at a time for reliability

        Args:
            count: Number of messages to fetch
            unread_only: If True, only fetch unread. If False, only fetch read. If None, fetch all.
        """
        messages = []
        fetched_count = 0
        i = 1

        # We may need to iterate more if filtering by read status
        max_iterations = count * 3 if unread_only is not None else count

        while fetched_count < count and i <= max_iterations:
            try:
                # Fetch message details including read status
                if self.account_name:
                    msg_script = f'''
                    tell application "Mail"
                        set msg to message {i} of mailbox "INBOX" of account "{self.account_name}"
                        set subj to subject of msg
                        set sndr to sender of msg
                        set msgId to id of msg as string
                        set msgDate to date received of msg as string
                        set isRead to read status of msg
                        return subj & "||||" & sndr & "||||" & msgId & "||||" & msgDate & "||||" & isRead
                    end tell
                    '''
                else:
                    msg_script = f'''
                    tell application "Mail"
                        set msg to message {i} of inbox
                        set subj to subject of msg
                        set sndr to sender of msg
                        set msgId to id of msg as string
                        set msgDate to date received of msg as string
                        set isRead to read status of msg
                        return subj & "||||" & sndr & "||||" & msgId & "||||" & msgDate & "||||" & isRead
                    end tell
                    '''

                result = self._run_applescript(msg_script, timeout=15)
                parts = result.split("||||")

                if len(parts) >= 5:
                    is_read = parts[4].lower() == "true"

                    # Apply read status filter
                    if unread_only is True and is_read:
                        i += 1
                        continue  # Skip read messages
                    elif unread_only is False and not is_read:
                        i += 1
                        continue  # Skip unread messages

                    messages.append({
                        "subject": parts[0],
                        "sender": parts[1],
                        "id": parts[2],
                        "date": parts[3],
                        "read": is_read
                    })
                    fetched_count += 1

                elif len(parts) >= 4:
                    # Fallback if read status fetch fails
                    messages.append({
                        "subject": parts[0],
                        "sender": parts[1],
                        "id": parts[2],
                        "date": parts[3],
                        "read": False
                    })
                    fetched_count += 1

                # Show progress for larger batches
                if count > 5 and fetched_count % 5 == 0:
                    print(f"  Fetched {fetched_count}/{count}...")

                i += 1

            except Exception as e:
                print(f"Warning: Could not fetch message {i}: {e}")
                i += 1
                continue

        return messages

    def get_message_content(self, message_id: str) -> str:
        """Get the full content of a message by ID"""
        script = f'''
        tell application "Mail"
            set msg to first message of inbox whose id is "{message_id}"
            return content of msg
        end tell
        '''
        try:
            return self._run_applescript(script, timeout=20)
        except Exception:
            return ""  # Return empty string if content can't be fetched

    def move_message_to_mailbox(self, message_id: str, mailbox_path: str) -> bool:
        """
        Move message to specified mailbox
        mailbox_path format: "ParentFolder/ChildFolder" or "Mailbox"
        """
        logger.debug(f"Moving message {message_id} to mailbox: {mailbox_path}")

        # Determine inbox source for faster lookup
        if self.account_name:
            inbox_ref = f'mailbox "INBOX" of account "{self.account_name}"'
            logger.debug(f"Using account-specific inbox: {self.account_name}")
        else:
            inbox_ref = "inbox"
            logger.debug("Using unified inbox")

        # Handle nested mailboxes
        if "/" in mailbox_path:
            parts = mailbox_path.split("/")
            if len(parts) == 2:
                parent, child = parts
                script = f'''
                tell application "Mail"
                    set msg to first message of {inbox_ref} whose id is "{message_id}"
                    set targetMailbox to mailbox "{child}" of mailbox "{parent}"
                    move msg to targetMailbox
                    return "success"
                end tell
                '''
            else:
                logger.error(f"Unsupported mailbox path format: {mailbox_path}")
                print(f"Unsupported mailbox path format: {mailbox_path}")
                return False
        else:
            # For account-specific mailboxes, use iteration approach for Gmail IMAP compatibility
            # Some Gmail mailboxes (Spam, Sent Mail) can't be referenced directly by name
            if self.account_name:
                script = f'''
                tell application "Mail"
                    set acc to account "{self.account_name}"
                    set msg to first message of {inbox_ref} whose id is "{message_id}"

                    -- Find target mailbox by iterating (works with Gmail IMAP)
                    set targetMailbox to missing value
                    repeat with aBox in (every mailbox of acc)
                        if name of aBox is "{mailbox_path}" then
                            set targetMailbox to aBox
                            exit repeat
                        end if
                    end repeat

                    if targetMailbox is missing value then
                        error "Mailbox '{mailbox_path}' not found in account"
                    end if

                    move msg to targetMailbox
                    return "success"
                end tell
                '''
            else:
                script = f'''
                tell application "Mail"
                    set msg to first message of {inbox_ref} whose id is "{message_id}"
                    set targetMailbox to mailbox "{mailbox_path}"
                    move msg to targetMailbox
                    return "success"
                end tell
                '''

        try:
            # Increase timeout for large inboxes
            self._run_applescript(script, timeout=30)
            logger.info(f"Successfully moved message to {mailbox_path}")
            return True
        except Exception as e:
            log_exception(logger, f"Error moving message to {mailbox_path}", e)
            print(f"Error moving message: {e}")
            return False

    def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        script = f'''
        tell application "Mail"
            set msg to first message of inbox whose id is "{message_id}"
            delete msg
            return "success"
        end tell
        '''
        try:
            self._run_applescript(script, timeout=15)
            return True
        except Exception as e:
            print(f"Error deleting message: {e}")
            return False

    def create_mailbox(self, mailbox_path: str) -> bool:
        """
        Create a mailbox if it doesn't exist

        Creates mailbox in the account (server-side) if account_name is set,
        otherwise creates "On My Mac" (local only)
        """
        parts = mailbox_path.split("/")

        try:
            if len(parts) == 1:
                # Top-level mailbox
                if self.account_name:
                    # Create in account (server-side) - syncs to Gmail/IMAP
                    script = f'''
                    tell application "Mail"
                        set acc to account "{self.account_name}"

                        -- Check if mailbox exists in account
                        set mailboxExists to false
                        repeat with aBox in (every mailbox of acc)
                            if name of aBox is "{mailbox_path}" then
                                set mailboxExists to true
                                exit repeat
                            end if
                        end repeat

                        -- Create if doesn't exist
                        if not mailboxExists then
                            make new mailbox at acc with properties {{name:"{mailbox_path}"}}
                        end if
                    end tell
                    '''
                else:
                    # Create On My Mac (local only)
                    script = f'''
                    tell application "Mail"
                        if not (exists mailbox "{mailbox_path}") then
                            make new mailbox with properties {{name:"{mailbox_path}"}}
                        end if
                    end tell
                    '''
                self._run_applescript(script, timeout=15)

            elif len(parts) == 2:
                # Nested mailbox - create in two steps
                parent, child = parts

                if self.account_name:
                    # Create parent in account (server-side)
                    parent_script = f'''
                    tell application "Mail"
                        set acc to account "{self.account_name}"

                        set mailboxExists to false
                        repeat with aBox in (every mailbox of acc)
                            if name of aBox is "{parent}" then
                                set mailboxExists to true
                                exit repeat
                            end if
                        end repeat

                        if not mailboxExists then
                            make new mailbox at acc with properties {{name:"{parent}"}}
                        end if
                    end tell
                    '''
                    self._run_applescript(parent_script, timeout=15)

                    # Then create child in account
                    child_script = f'''
                    tell application "Mail"
                        set acc to account "{self.account_name}"

                        -- Find parent mailbox
                        set parentBox to missing value
                        repeat with aBox in (every mailbox of acc)
                            if name of aBox is "{parent}" then
                                set parentBox to aBox
                                exit repeat
                            end if
                        end repeat

                        if parentBox is not missing value then
                            -- Check if child exists
                            try
                                set childExists to exists mailbox "{child}" of parentBox
                            on error
                                set childExists to false
                            end try

                            if not childExists then
                                make new mailbox at parentBox with properties {{name:"{child}"}}
                            end if
                        end if
                    end tell
                    '''
                    self._run_applescript(child_script, timeout=15)
                else:
                    # Create On My Mac (local only)
                    parent_script = f'''
                    tell application "Mail"
                        if not (exists mailbox "{parent}") then
                            make new mailbox with properties {{name:"{parent}"}}
                        end if
                    end tell
                    '''
                    self._run_applescript(parent_script, timeout=15)

                    child_script = f'''
                    tell application "Mail"
                        set parentBox to mailbox "{parent}"
                        try
                            set childExists to exists mailbox "{child}" of parentBox
                        on error
                            set childExists to false
                        end try
                        if not childExists then
                            make new mailbox at parentBox with properties {{name:"{child}"}}
                        end if
                    end tell
                    '''
                    self._run_applescript(child_script, timeout=15)
            else:
                print(f"Unsupported mailbox path: {mailbox_path}")
                return False

            return True

        except Exception as e:
            print(f"Warning: Could not create mailbox '{mailbox_path}': {e}")
            print(f"You may need to create this mailbox manually in Apple Mail")
            return False


def test_connection():
    """Test Apple Mail connection"""
    client = AppleMailClient()
    try:
        print("Testing Apple Mail connection...")
        messages = client.get_inbox_messages(limit=1)
        print(f"✓ Connected to Apple Mail. Found {len(messages)} test message(s)")
        if messages:
            print(f"  Sample: '{messages[0]['subject']}' from {messages[0]['sender']}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Apple Mail: {e}")
        return False


if __name__ == "__main__":
    test_connection()
