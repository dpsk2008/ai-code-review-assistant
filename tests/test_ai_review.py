
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from api import app
from review_assistant.ai_review import AIReviewError


class AIReviewAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    @patch("api.review_with_ai")
    def test_ai_review_success(self, mock_review):
        mock_review.return_value = "Potential IndexError on line 2."

        response = self.client.post(
            "/review/ai",
            json={"code": "items[0]"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"ai_review": "Potential IndexError on line 2."},
        )
        mock_review.assert_called_once_with("items[0]")

    @patch("api.review_with_ai")
    def test_ai_review_rejects_empty_code(self, mock_review):
        response = self.client.post(
            "/review/ai",
            json={"code": "   "},
        )

        self.assertEqual(response.status_code, 422)
        mock_review.assert_not_called()

    @patch("api.review_with_ai")
    def test_ai_review_rejects_oversized_code(self, mock_review):
        oversized_code = "x" * (64 * 1024 + 1)

        response = self.client.post(
            "/review/ai",
            json={"code": oversized_code},
        )

        self.assertEqual(response.status_code, 413)
        self.assertIn(
            "64 KB",
            response.json()["detail"],
        )
        mock_review.assert_not_called()

    @patch("api.review_with_ai")
    def test_ai_review_connection_failure(self, mock_review):
        mock_review.side_effect = httpx.ConnectError(
            "Connection refused"
        )

        response = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn(
            "Ollama",
            response.json()["detail"],
        )

    @patch("api.review_with_ai")
    def test_ai_review_model_error(self, mock_review):
        request = httpx.Request(
            "POST",
            "http://127.0.0.1:11434/api/generate",
        )

        model_response = httpx.Response(
            500,
            request=request,
        )

        mock_review.side_effect = httpx.HTTPStatusError(
            "Model error",
            request=request,
            response=model_response,
        )

        response = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(response.status_code, 502)

    @patch("api.review_with_ai")
    def test_ai_review_timeout(self, mock_review):
        mock_review.side_effect = httpx.ReadTimeout(
            "The AI model timed out"
        )

        response = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(response.status_code, 504)
        self.assertIn(
            "too long",
            response.json()["detail"],
        )

    @patch("api.review_with_ai")
    def test_ai_review_empty_response(self, mock_review):
        mock_review.return_value = "   "

        response = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn(
            "empty response",
            response.json()["detail"],
        )

    @patch("api.review_with_ai")
    def test_ai_review_missing_code(self, mock_review):
        response = self.client.post(
            "/review/ai",
            json={},
        )

        self.assertEqual(response.status_code, 422)
        mock_review.assert_not_called()

    # Ollama Response Validation Tests

    @patch("api.review_with_ai")
    def test_ai_invalid_json_error(self, mock_review):
        mock_review.side_effect = AIReviewError(
            "Ollama returned an invalid JSON response."
        )

        response = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn(
            "invalid response",
            response.json()["detail"],
        )

    @patch("api.review_with_ai")
    def test_ai_missing_response_field_error(self, mock_review):
        mock_review.side_effect = AIReviewError(
            "Ollama response is missing valid review text."
        )

        response = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn(
            "invalid response",
            response.json()["detail"],
        )

    @patch("api.review_with_ai")
    def test_ai_unexpected_response_type_error(self, mock_review):
        mock_review.side_effect = AIReviewError(
            "Ollama returned an unexpected response format."
        )

        response = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn(
            "invalid response",
            response.json()["detail"],
        )


if __name__ == "__main__":
    unittest.main()
