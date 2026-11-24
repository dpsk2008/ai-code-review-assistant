
import unittest
from unittest.mock import patch

import httpx

from review_assistant.ai_review import AIReviewError, review_with_ai


class OllamaClientTests(unittest.TestCase):

    @patch("review_assistant.ai_review.httpx.post")
    def test_valid_ollama_response(self, mock_post):
        mock_post.return_value = httpx.Response(
            200,
            json={"response": "No obvious issues found."},
            request=httpx.Request(
                "POST",
                "http://127.0.0.1:11434/api/generate",
            ),
        )

        result = review_with_ai("print('hello')")

        self.assertEqual(
            result,
            "No obvious issues found.",
        )
        mock_post.assert_called_once()

    @patch("review_assistant.ai_review.httpx.post")
    def test_invalid_json(self, mock_post):
        mock_post.return_value = httpx.Response(
            200,
            text="not valid json",
            request=httpx.Request(
                "POST",
                "http://127.0.0.1:11434/api/generate",
            ),
        )

        with self.assertRaises(AIReviewError):
            review_with_ai("print('hello')")

    @patch("review_assistant.ai_review.httpx.post")
    def test_missing_response_field(self, mock_post):
        mock_post.return_value = httpx.Response(
            200,
            json={"model": "qwen2.5-coder:3b"},
            request=httpx.Request(
                "POST",
                "http://127.0.0.1:11434/api/generate",
            ),
        )

        with self.assertRaises(AIReviewError):
            review_with_ai("print('hello')")

    @patch("review_assistant.ai_review.httpx.post")
    def test_unexpected_response_type(self, mock_post):
        mock_post.return_value = httpx.Response(
            200,
            json=["unexpected", "data"],
            request=httpx.Request(
                "POST",
                "http://127.0.0.1:11434/api/generate",
            ),
        )

        with self.assertRaises(AIReviewError):
            review_with_ai("print('hello')")

    @patch("review_assistant.ai_review.httpx.post")
    def test_empty_response(self, mock_post):
        mock_post.return_value = httpx.Response(
            200,
            json={"response": "   "},
            request=httpx.Request(
                "POST",
                "http://127.0.0.1:11434/api/generate",
            ),
        )

        with self.assertRaises(AIReviewError):
            review_with_ai("print('hello')")


if __name__ == "__main__":
    unittest.main()
