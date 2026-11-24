
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from api import app


class AIReviewAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

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
        response = httpx.Response(500, request=request)
        mock_review.side_effect = httpx.HTTPStatusError(
            "Model error",
            request=request,
            response=response,
        )

        result = self.client.post(
            "/review/ai",
            json={"code": "print('hello')"},
        )

        self.assertEqual(result.status_code, 502)


if __name__ == "__main__":
    unittest.main()
