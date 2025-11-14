"""
Email Classification using Ollama
"""
import requests
import json
from typing import Dict, List, Tuple, Optional
from config import OLLAMA_HOST, OLLAMA_MODEL
from logger import setup_logger, log_exception

# Set up logger for this module
logger = setup_logger("ollama_classifier")


class OllamaClassifier:
    """Use Ollama LLM for email classification"""

    def __init__(self, model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host
        self.api_url = f"{host}/api/generate"

    def test_connection(self) -> bool:
        """Test connection to Ollama"""
        try:
            logger.debug(f"Testing connection to Ollama at {self.host}")
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            success = response.status_code == 200
            if success:
                logger.info(f"Successfully connected to Ollama at {self.host}")
            else:
                logger.warning(f"Ollama connection failed with status {response.status_code}")
            return success
        except Exception as e:
            log_exception(logger, "Failed to connect to Ollama", e)
            print(f"Failed to connect to Ollama: {e}")
            return False

    def classify_email(
        self,
        subject: str,
        sender: str,
        content: str,
        categories: List[str],
        training_examples: Optional[List[Dict]] = None
    ) -> Tuple[str, float]:
        """
        Classify an email into one of the categories

        Returns:
            Tuple of (category, confidence_score)
        """
        # Build prompt with training examples if available
        prompt = self._build_classification_prompt(
            subject, sender, content, categories, training_examples
        )

        try:
            logger.debug(f"Classifying email from {sender} with subject: {subject[:50]}...")

            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                category, confidence = self._parse_classification_response(result['response'], categories)
                logger.info(f"Classified email as '{category}' with {confidence:.1%} base confidence")
                return category, confidence
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                print(f"Ollama API error: {response.status_code}")
                return categories[0], 0.0

        except Exception as e:
            log_exception(logger, "Error during email classification", e)
            print(f"Error during classification: {e}")
            return categories[0], 0.0

    def _build_classification_prompt(
        self,
        subject: str,
        sender: str,
        content: str,
        categories: List[str],
        training_examples: Optional[List[Dict]]
    ) -> str:
        """Build the prompt for email classification"""

        # Truncate content to avoid token limits
        content_preview = content[:500] if len(content) > 500 else content

        prompt = f"""You are an email classification assistant. Analyze the following email and classify it into one of the given categories.

Email Details:
Subject: {subject}
From: {sender}
Content Preview: {content_preview}

Available Categories:
{json.dumps(categories, indent=2)}
"""

        # Add training examples if available
        if training_examples and len(training_examples) > 0:
            prompt += "\n\nPrevious Classification Examples:\n"
            for example in training_examples[-10:]:  # Last 10 examples
                prompt += f"- Subject: '{example['subject']}' → Category: '{example['category']}'\n"

        prompt += """
Based on the email details and any previous examples, determine:
1. The most appropriate category
2. Your confidence level (0.0 to 1.0)

Respond ONLY with valid JSON in this exact format:
{
  "category": "selected_category_name",
  "confidence": 0.95,
  "reasoning": "brief explanation"
}
"""

        return prompt

    def _parse_classification_response(
        self,
        response: str,
        categories: List[str]
    ) -> Tuple[str, float]:
        """Parse the JSON response from Ollama"""
        try:
            # Try to parse as JSON
            data = json.loads(response)
            category = data.get("category", categories[0])
            confidence = float(data.get("confidence", 0.0))

            # Validate category
            if category not in categories:
                # Try to find closest match
                category = self._find_closest_category(category, categories)

            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))

            return category, confidence

        except json.JSONDecodeError:
            # Fallback: try to extract category from text
            print(f"Failed to parse JSON response: {response[:200]}")
            for cat in categories:
                if cat.lower() in response.lower():
                    return cat, 0.5
            return categories[0], 0.0

    def _find_closest_category(self, suggested: str, categories: List[str]) -> str:
        """Find closest matching category"""
        suggested_lower = suggested.lower()
        for cat in categories:
            if cat.lower() in suggested_lower or suggested_lower in cat.lower():
                return cat
        return categories[0]

    def compute_similarity(self, email1: Dict, email2: Dict) -> float:
        """
        Compute similarity between two emails using Ollama
        Returns a score between 0.0 and 1.0
        """
        prompt = f"""Compare these two emails and rate their similarity from 0.0 to 1.0.
Consider: sender domain, subject patterns, content topics, and purpose.

Email 1:
Subject: {email1['subject']}
From: {email1['sender']}

Email 2:
Subject: {email2['subject']}
From: {email2['sender']}

Respond with ONLY a JSON object:
{{"similarity": 0.85, "reasoning": "brief explanation"}}
"""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=20
            )

            if response.status_code == 200:
                result = response.json()
                data = json.loads(result['response'])
                return float(data.get("similarity", 0.0))
            else:
                return 0.0

        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0

    def summarize_email(
        self,
        subject: str,
        sender: str,
        content: str,
        max_length: int = 150
    ) -> str:
        """
        Generate a brief summary of the email content

        Args:
            subject: Email subject
            sender: Email sender
            content: Email content
            max_length: Maximum length of content to analyze

        Returns:
            Brief summary string
        """
        # Truncate content to avoid token limits
        content_preview = content[:max_length] if len(content) > max_length else content

        prompt = f"""Summarize this email in 1-2 short sentences (max 50 words). Focus on the key point or action needed.

Subject: {subject}
From: {sender}
Content: {content_preview}

Summary:"""

        try:
            logger.debug(f"Generating summary for email from {sender}: {subject[:50]}...")

            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Summary API response: {result}")

                # Extract summary from response
                if 'response' in result:
                    summary = result['response'].strip()
                    # Clean up the summary
                    if summary.startswith("Summary:"):
                        summary = summary[8:].strip()

                    if summary:
                        logger.info(f"Generated summary: {summary[:100]}...")
                        return summary
                    else:
                        logger.warning("Empty summary received from Ollama")
                        return "No summary available"
                else:
                    logger.error(f"Unexpected response structure: {result}")
                    return "Summary unavailable"
            else:
                logger.error(f"Ollama summary API error: {response.status_code} - {response.text}")
                return "Summary unavailable"

        except Exception as e:
            log_exception(logger, "Error generating email summary", e)
            return f"Summary error: {str(e)[:50]}"


def test_ollama():
    """Test Ollama connection and classification"""
    classifier = OllamaClassifier()

    print("Testing Ollama connection...")
    if not classifier.test_connection():
        print("✗ Cannot connect to Ollama. Make sure it's running: ollama serve")
        return False

    print("✓ Connected to Ollama")

    # Test classification
    print("\nTesting email classification...")
    test_categories = ["Work", "Personal", "Spam"]
    category, confidence = classifier.classify_email(
        subject="Meeting tomorrow at 2pm",
        sender="boss@company.com",
        content="Hi, let's meet tomorrow to discuss the project.",
        categories=test_categories
    )

    print(f"✓ Test classification: {category} (confidence: {confidence:.2f})")
    return True


if __name__ == "__main__":
    test_ollama()
