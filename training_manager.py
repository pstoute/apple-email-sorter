"""
Training Data Management and Confidence Scoring
"""
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from config import (
    TRAINING_DATA_FILE,
    CONFIDENCE_THRESHOLD_SUGGEST,
    CONFIDENCE_THRESHOLD_AUTO,
    MIN_TRAINING_SAMPLES,
    SIMILARITY_THRESHOLD
)


class TrainingManager:
    """Manage training data and compute confidence scores"""

    def __init__(self, data_file: Path = TRAINING_DATA_FILE):
        self.data_file = data_file
        self.training_data = self._load_training_data()

    def _load_training_data(self) -> Dict:
        """Load training data from disk"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "emails": [],
                "statistics": {
                    "total_trained": 0,
                    "correct_predictions": 0,
                    "incorrect_predictions": 0
                }
            }

    def save_training_data(self):
        """Save training data to disk"""
        self.data_file.parent.mkdir(exist_ok=True)
        with open(self.data_file, 'w') as f:
            json.dump(self.training_data, indent=2, fp=f)

    def add_training_example(
        self,
        email_id: str,
        subject: str,
        sender: str,
        content: str,
        category: str,
        user_decision: bool = True
    ):
        """
        Add a new training example

        Args:
            email_id: Unique email identifier
            subject: Email subject
            sender: Email sender
            content: Email content (truncated)
            category: Assigned category
            user_decision: Whether this was a user decision (vs auto-classified)
        """
        # Check if this email is already in training data
        existing = [e for e in self.training_data["emails"] if e["email_id"] == email_id]
        if existing:
            # Update existing entry
            existing[0]["category"] = category
            existing[0]["last_updated"] = datetime.now().isoformat()
            existing[0]["user_decision"] = user_decision
        else:
            # Add new entry
            self.training_data["emails"].append({
                "email_id": email_id,
                "subject": subject,
                "sender": sender,
                "content_preview": content[:200],  # Store preview only
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "user_decision": user_decision,
                "sender_domain": self._extract_domain(sender)
            })

        self.training_data["statistics"]["total_trained"] += 1
        self.save_training_data()

    def _extract_domain(self, sender: str) -> str:
        """Extract domain from email address"""
        if '@' in sender:
            # Handle "Name <email@domain.com>" format
            if '<' in sender:
                sender = sender.split('<')[1].split('>')[0]
            return sender.split('@')[1].lower()
        return ""

    def get_training_examples_for_category(self, category: str) -> List[Dict]:
        """Get all training examples for a specific category"""
        return [
            e for e in self.training_data["emails"]
            if e["category"] == category
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
        """
        Compute final confidence score based on training data

        Args:
            subject: Email subject
            sender: Email sender
            content: Email content
            predicted_category: Category predicted by classifier
            base_confidence: Base confidence from classifier
            similarity_scorer: Function to compute similarity between emails

        Returns:
            Adjusted confidence score (0.0 to 1.0)
        """
        # Get training examples for this category
        category_examples = self.get_training_examples_for_category(predicted_category)

        # Not enough training data
        if len(category_examples) < MIN_TRAINING_SAMPLES:
            return min(base_confidence, 0.85)  # Cap at 85% without enough data

        # Check for exact sender domain match
        sender_domain = self._extract_domain(sender)
        domain_matches = [
            e for e in category_examples
            if e.get("sender_domain") == sender_domain
        ]

        # Strong signal: same domain consistently goes to this category
        if len(domain_matches) >= 3:
            domain_confidence = min(len(domain_matches) / 10.0, 0.95)
            base_confidence = max(base_confidence, domain_confidence)

        # If we have a similarity scorer, check similarity to existing examples
        if similarity_scorer:
            current_email = {
                "subject": subject,
                "sender": sender,
                "content": content
            }

            similarities = []
            for example in category_examples[-10:]:  # Check last 10 examples
                example_email = {
                    "subject": example["subject"],
                    "sender": example["sender"],
                    "content": example.get("content_preview", "")
                }

                similarity = similarity_scorer(current_email, example_email)
                similarities.append(similarity)

            if similarities:
                max_similarity = max(similarities)
                avg_similarity = sum(similarities) / len(similarities)

                # High similarity to existing examples increases confidence
                if max_similarity >= SIMILARITY_THRESHOLD:
                    base_confidence = max(base_confidence, 0.95)
                elif avg_similarity >= 0.7:
                    base_confidence = max(base_confidence, 0.85)

        # Factor in historical accuracy for this category
        category_stats = self._get_category_stats(predicted_category)
        if category_stats["total"] >= 5:
            accuracy = category_stats["correct"] / category_stats["total"]
            base_confidence *= (0.8 + 0.2 * accuracy)  # Scale by accuracy

        return min(base_confidence, 1.0)

    def _get_category_stats(self, category: str) -> Dict:
        """Get accuracy statistics for a category"""
        category_emails = self.get_training_examples_for_category(category)

        return {
            "total": len(category_emails),
            "correct": len([e for e in category_emails if e.get("user_decision", True)]),
            "incorrect": len([e for e in category_emails if not e.get("user_decision", True)])
        }

    def record_prediction_result(self, was_correct: bool):
        """Record whether a prediction was correct"""
        stats = self.training_data["statistics"]
        if was_correct:
            stats["correct_predictions"] += 1
        else:
            stats["incorrect_predictions"] += 1
        self.save_training_data()

    def should_suggest(self, confidence: float) -> bool:
        """Determine if we should make a suggestion to the user"""
        return confidence >= CONFIDENCE_THRESHOLD_SUGGEST

    def should_auto_classify(self, confidence: float) -> bool:
        """Determine if we should automatically classify without asking"""
        return confidence >= CONFIDENCE_THRESHOLD_AUTO

    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        stats = self.training_data["statistics"].copy()
        stats["total_examples"] = len(self.training_data["emails"])
        stats["categories"] = {}

        # Per-category statistics
        for email in self.training_data["emails"]:
            cat = email["category"]
            if cat not in stats["categories"]:
                stats["categories"][cat] = 0
            stats["categories"][cat] += 1

        return stats

    def get_recent_examples(self, limit: int = 10) -> List[Dict]:
        """Get most recent training examples"""
        sorted_emails = sorted(
            self.training_data["emails"],
            key=lambda e: e.get("timestamp", ""),
            reverse=True
        )
        return sorted_emails[:limit]


if __name__ == "__main__":
    # Test training manager
    manager = TrainingManager()
    print(f"Training examples: {len(manager.training_data['emails'])}")
    print(f"Statistics: {manager.get_statistics()}")
