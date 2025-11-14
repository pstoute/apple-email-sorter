"""
PostgreSQL Storage Backend (Optional)
Use this instead of JSON files for more robust storage and RAG capabilities
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional
import json


class PostgresStorage:
    """PostgreSQL backend for training data and RAG"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "email_sorter",
        user: str = "user",
        password: str = "password"
    ):
        self.connection_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self._ensure_schema()

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.connection_params)

    def _ensure_schema(self):
        """Create tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    # Create tables
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS emails (
                            id SERIAL PRIMARY KEY,
                            email_id TEXT UNIQUE NOT NULL,
                            subject TEXT NOT NULL,
                            normalized_subject TEXT,
                            thread_id TEXT,
                            sender TEXT NOT NULL,
                            sender_domain TEXT,
                            content_preview TEXT,
                            category TEXT NOT NULL,
                            confidence FLOAT,
                            user_decision BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Add columns if they don't exist (migrations)
                    cur.execute("""
                        DO $$
                        BEGIN
                            -- Add account column
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='emails' AND column_name='account'
                            ) THEN
                                ALTER TABLE emails ADD COLUMN account TEXT;
                            END IF;

                            -- Add normalized_subject column
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='emails' AND column_name='normalized_subject'
                            ) THEN
                                ALTER TABLE emails ADD COLUMN normalized_subject TEXT;
                            END IF;

                            -- Add thread_id column
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='emails' AND column_name='thread_id'
                            ) THEN
                                ALTER TABLE emails ADD COLUMN thread_id TEXT;
                            END IF;
                        END $$;
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS classifications (
                            id SERIAL PRIMARY KEY,
                            email_id TEXT NOT NULL,
                            predicted_category TEXT NOT NULL,
                            actual_category TEXT NOT NULL,
                            confidence FLOAT NOT NULL,
                            was_correct BOOLEAN NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS statistics (
                            id SERIAL PRIMARY KEY,
                            session_date DATE DEFAULT CURRENT_DATE,
                            total_reviewed INTEGER DEFAULT 0,
                            manual_review INTEGER DEFAULT 0,
                            suggested INTEGER DEFAULT 0,
                            suggestions_accepted INTEGER DEFAULT 0,
                            suggestions_rejected INTEGER DEFAULT 0,
                            auto_classified INTEGER DEFAULT 0,
                            skipped INTEGER DEFAULT 0
                        )
                    """)

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS email_embeddings (
                            id SERIAL PRIMARY KEY,
                            email_id TEXT NOT NULL REFERENCES emails(email_id),
                            embedding_vector FLOAT[] NOT NULL,
                            model TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Create indexes
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_emails_email_id ON emails(email_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_emails_sender_domain ON emails(sender_domain)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_emails_account ON emails(account)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_emails_normalized_subject ON emails(normalized_subject)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_classifications_email_id ON classifications(email_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_statistics_session_date ON statistics(session_date)")

                conn.commit()
        except psycopg2.OperationalError as e:
            print(f"Warning: Could not connect to PostgreSQL: {e}")
            print("Falling back to JSON storage")
            raise

    def add_email_training(
        self,
        email_id: str,
        subject: str,
        sender: str,
        content_preview: str,
        category: str,
        account: str = None,
        confidence: float = None,
        user_decision: bool = True,
        normalized_subject: str = None,
        thread_id: str = None
    ):
        """Add or update email training data"""
        sender_domain = self._extract_domain(sender)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO emails (
                        email_id, subject, normalized_subject, thread_id,
                        sender, sender_domain, account,
                        content_preview, category, confidence, user_decision
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email_id)
                    DO UPDATE SET
                        category = EXCLUDED.category,
                        account = EXCLUDED.account,
                        normalized_subject = EXCLUDED.normalized_subject,
                        thread_id = EXCLUDED.thread_id,
                        confidence = EXCLUDED.confidence,
                        user_decision = EXCLUDED.user_decision,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    email_id, subject, normalized_subject, thread_id,
                    sender, sender_domain, account,
                    content_preview, category, confidence, user_decision
                ))
            conn.commit()

    def record_classification(
        self,
        email_id: str,
        predicted_category: str,
        actual_category: str,
        confidence: float
    ):
        """Record a classification attempt"""
        was_correct = (predicted_category == actual_category)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO classifications (
                        email_id, predicted_category, actual_category,
                        confidence, was_correct
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (email_id, predicted_category, actual_category, confidence, was_correct))
            conn.commit()

    def get_training_examples_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """Get training examples for a category"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        email_id, subject, sender, sender_domain,
                        content_preview, category, confidence,
                        user_decision, created_at, updated_at
                    FROM emails
                    WHERE category = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (category, limit))
                return [dict(row) for row in cur.fetchall()]

    def get_training_examples_by_domain(self, domain: str, limit: int = 50) -> List[Dict]:
        """Get training examples from a specific domain"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        email_id, subject, sender, sender_domain,
                        content_preview, category, confidence,
                        user_decision, created_at, updated_at
                    FROM emails
                    WHERE sender_domain = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (domain, limit))
                return [dict(row) for row in cur.fetchall()]

    def get_thread_classification(self, thread_id: str) -> Optional[Dict]:
        """Get the most recent classification for a thread"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT category, confidence, user_decision
                    FROM emails
                    WHERE thread_id = %s
                      AND category IS NOT NULL
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (thread_id,))
                result = cur.fetchone()
                return dict(result) if result else None

    def get_recent_examples(self, limit: int = 10) -> List[Dict]:
        """Get most recent training examples"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        email_id, subject, sender, sender_domain,
                        content_preview, category, confidence,
                        user_decision, created_at, updated_at
                    FROM emails
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]

    def get_category_statistics(self, category: str) -> Dict:
        """Get statistics for a category"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total emails in category
                cur.execute("""
                    SELECT COUNT(*) as total
                    FROM emails
                    WHERE category = %s
                """, (category,))
                total = cur.fetchone()['total']

                # Classification accuracy
                cur.execute("""
                    SELECT
                        COUNT(*) as total_classifications,
                        SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct
                    FROM classifications
                    WHERE actual_category = %s
                """, (category,))
                stats = cur.fetchone()

                return {
                    "total": total,
                    "classifications": stats['total_classifications'] or 0,
                    "correct": stats['correct'] or 0,
                    "accuracy": (stats['correct'] / stats['total_classifications'])
                        if stats['total_classifications'] else 0
                }

    def get_overall_statistics(self) -> Dict:
        """Get overall system statistics"""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total emails
                cur.execute("SELECT COUNT(*) as total FROM emails")
                total_emails = cur.fetchone()['total']

                # Per-category counts
                cur.execute("""
                    SELECT category, COUNT(*) as count
                    FROM emails
                    GROUP BY category
                    ORDER BY count DESC
                """)
                categories = {row['category']: row['count'] for row in cur.fetchall()}

                # Overall accuracy
                cur.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct
                    FROM classifications
                """)
                accuracy_data = cur.fetchone()

                return {
                    "total_examples": total_emails,
                    "categories": categories,
                    "total_classifications": accuracy_data['total'] or 0,
                    "correct_predictions": accuracy_data['correct'] or 0,
                    "incorrect_predictions": (accuracy_data['total'] or 0) - (accuracy_data['correct'] or 0),
                    "accuracy": (accuracy_data['correct'] / accuracy_data['total'])
                        if accuracy_data['total'] else 0
                }

    def save_session_statistics(self, stats: Dict):
        """Save session statistics"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO statistics (
                        total_reviewed, manual_review, suggested,
                        suggestions_accepted, suggestions_rejected,
                        auto_classified, skipped
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    stats.get('total_reviewed', 0),
                    stats.get('manual_review', 0),
                    stats.get('suggested', 0),
                    stats.get('suggestions_accepted', 0),
                    stats.get('suggestions_rejected', 0),
                    stats.get('auto_classified', 0),
                    stats.get('skipped', 0)
                ))
            conn.commit()

    def store_embedding(self, email_id: str, embedding: List[float], model: str):
        """Store email embedding for RAG"""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO email_embeddings (email_id, embedding_vector, model)
                    VALUES (%s, %s, %s)
                """, (email_id, embedding, model))
            conn.commit()

    def find_similar_emails(
        self,
        embedding: List[float],
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        Find similar emails using cosine similarity
        Requires pgvector extension for optimal performance
        For now, returns recent examples from category
        """
        # TODO: Implement with pgvector for efficient similarity search
        # For now, fall back to category-based retrieval
        if category:
            return self.get_training_examples_by_category(category, limit)
        else:
            return self.get_recent_examples(limit)

    @staticmethod
    def _extract_domain(sender: str) -> str:
        """Extract domain from email address"""
        if '@' in sender:
            if '<' in sender:
                sender = sender.split('<')[1].split('>')[0]
            return sender.split('@')[1].lower()
        return ""


class PostgresTrainingManager:
    """Training manager that uses PostgreSQL backend"""

    def __init__(self, storage: PostgresStorage):
        self.storage = storage

    def add_training_example(
        self,
        email_id: str,
        subject: str,
        sender: str,
        content: str,
        category: str,
        account: str = None,
        confidence: float = None,
        user_decision: bool = True,
        normalized_subject: str = None,
        thread_id: str = None
    ):
        """Add training example"""
        content_preview = content[:200] if len(content) > 200 else content
        self.storage.add_email_training(
            email_id=email_id,
            subject=subject,
            sender=sender,
            content_preview=content_preview,
            category=category,
            account=account,
            confidence=confidence,
            user_decision=user_decision,
            normalized_subject=normalized_subject,
            thread_id=thread_id
        )

    def record_prediction_result(self, email_id: str, predicted: str, actual: str, confidence: float):
        """Record prediction result"""
        self.storage.record_classification(
            email_id=email_id,
            predicted_category=predicted,
            actual_category=actual,
            confidence=confidence
        )

    def get_statistics(self) -> Dict:
        """Get statistics"""
        return self.storage.get_overall_statistics()

    def get_recent_examples(self, limit: int = 10) -> List[Dict]:
        """Get recent examples"""
        examples = self.storage.get_recent_examples(limit)
        # Convert to format expected by existing code
        return [
            {
                "email_id": e['email_id'],
                "subject": e['subject'],
                "sender": e['sender'],
                "category": e['category'],
                "content_preview": e.get('content_preview', '')
            }
            for e in examples
        ]

    def compute_confidence(
        self,
        subject: str,
        sender: str,
        content: str,
        predicted_category: str,
        base_confidence: float,
        similarity_scorer=None
    ) -> float:
        """Compute confidence with database-backed data"""
        from config import MIN_TRAINING_SAMPLES, SIMILARITY_THRESHOLD

        # Get category examples
        category_examples = self.storage.get_training_examples_by_category(
            predicted_category,
            limit=100
        )

        if len(category_examples) < MIN_TRAINING_SAMPLES:
            return min(base_confidence, 0.85)

        # Check domain matching
        domain = self.storage._extract_domain(sender)
        domain_examples = self.storage.get_training_examples_by_domain(domain, limit=50)
        domain_category_matches = [e for e in domain_examples if e['category'] == predicted_category]

        if len(domain_category_matches) >= 3:
            domain_confidence = min(len(domain_category_matches) / 10.0, 0.95)
            base_confidence = max(base_confidence, domain_confidence)

        # Category accuracy
        stats = self.storage.get_category_statistics(predicted_category)
        if stats['classifications'] >= 5:
            base_confidence *= (0.8 + 0.2 * stats['accuracy'])

        return min(base_confidence, 1.0)

    def should_suggest(self, confidence: float) -> bool:
        """Should make suggestion"""
        from config import CONFIDENCE_THRESHOLD_SUGGEST
        return confidence >= CONFIDENCE_THRESHOLD_SUGGEST

    def should_auto_classify(self, confidence: float) -> bool:
        """Should auto-classify"""
        from config import CONFIDENCE_THRESHOLD_AUTO
        return confidence >= CONFIDENCE_THRESHOLD_AUTO


def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        storage = PostgresStorage()
        print("✓ Connected to PostgreSQL")

        # Test basic operations
        storage.add_email_training(
            email_id="test_123",
            subject="Test Email",
            sender="test@example.com",
            content_preview="This is a test",
            category="Test",
            user_decision=True
        )
        print("✓ Can write to database")

        stats = storage.get_overall_statistics()
        print(f"✓ Training examples in database: {stats['total_examples']}")

        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False


if __name__ == "__main__":
    test_postgres_connection()
