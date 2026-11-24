
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app
from review_assistant.github_review import GitHubReviewError


class GitHubAPITests(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    @patch("api.review_repository")
    def test_github_review_success(self, mock_review):
        mock_review.return_value = {
            "repository": "example/project",
            "files_scanned": ["example.py"],
            "files_scanned_count": 1,
            "findings_count": 1,
            "findings": [
                {
                    "rule_id": "PY001",
                    "file_path": "example.py",
                    "line_number": 2,
                    "severity": "warning",
                    "message": "Potential IndexError",
                    "recommendation": "Check the sequence.",
                }
            ],
            "skipped_files": [],
        }

        response = self.client.post(
            "/review/github",
            json={
                "repository_url": "https://github.com/example/project"
            },
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()

        self.assertEqual(result["repository"], "example/project")
        self.assertEqual(result["files_scanned_count"], 1)
        self.assertEqual(result["findings_count"], 1)
        self.assertEqual(result["findings"][0]["rule_id"], "PY001")

        mock_review.assert_called_once_with(
            "https://github.com/example/project"
        )

    @patch("api.review_repository")
    def test_github_review_invalid_url(self, mock_review):
        mock_review.side_effect = GitHubReviewError(
            "Invalid GitHub repository URL."
        )

        response = self.client.post(
            "/review/github",
            json={"repository_url": "invalid-url"},
        )

        self.assertEqual(response.status_code, 422)
        mock_review.assert_called_once()

    @patch("api.review_repository")
    def test_github_review_private_repository(self, mock_review):
        mock_review.side_effect = GitHubReviewError(
            "Only public repositories are supported."
        )

        response = self.client.post(
            "/review/github",
            json={
                "repository_url": "https://github.com/example/private"
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn(
            "public repositories",
            response.json()["detail"],
        )

    @patch("api.review_repository")
    def test_github_review_missing_url(self, mock_review):
        response = self.client.post(
            "/review/github",
            json={},
        )

        self.assertEqual(response.status_code, 422)
        mock_review.assert_not_called()


if __name__ == "__main__":
    unittest.main()
