
import base64
import unittest
from unittest.mock import patch

from review_assistant.github_review import (
    GitHubReviewError,
    parse_repository_url,
    review_repository,
)


class GitHubURLTests(unittest.TestCase):

    def test_valid_repository_url(self):
        owner, repo = parse_repository_url(
            "https://github.com/dpsk2008/ai-code-review-assistant"
        )

        self.assertEqual(owner, "dpsk2008")
        self.assertEqual(repo, "ai-code-review-assistant")

    def test_repository_url_with_git_suffix(self):
        owner, repo = parse_repository_url(
            "https://github.com/dpsk2008/ai-code-review-assistant.git"
        )

        self.assertEqual(owner, "dpsk2008")
        self.assertEqual(repo, "ai-code-review-assistant")

    def test_rejects_non_github_domain(self):
        with self.assertRaises(GitHubReviewError):
            parse_repository_url(
                "https://example.com/user/repository"
            )

    def test_rejects_http_url(self):
        with self.assertRaises(GitHubReviewError):
            parse_repository_url(
                "http://github.com/user/repository"
            )

    def test_rejects_extra_path(self):
        with self.assertRaises(GitHubReviewError):
            parse_repository_url(
                "https://github.com/user/repository/tree/main"
            )

    def test_rejects_missing_repository(self):
        with self.assertRaises(GitHubReviewError):
            parse_repository_url(
                "https://github.com/user"
            )

    def test_rejects_fake_github_domain(self):
        with self.assertRaises(GitHubReviewError):
            parse_repository_url(
                "https://github.com.evil.com/user/repository"
            )

    @patch("review_assistant.github_review.github_get")
    def test_repository_scans_python_file(self, mock_get):
        source = (
            "def get_first(items):\n"
            "    return items[0]\n"
        )

        encoded_source = base64.b64encode(
            source.encode("utf-8")
        ).decode("ascii")

        mock_get.side_effect = [
            {
                "private": False,
                "default_branch": "main",
            },
            {
                "truncated": False,
                "tree": [
                    {
                        "path": "example.py",
                        "type": "blob",
                        "size": len(source.encode("utf-8")),
                        "sha": "a" * 40,
                    },
                ],
            },
            {
                "encoding": "base64",
                "content": encoded_source,
            },
        ]

        result = review_repository(
            "https://github.com/example/project"
        )

        self.assertEqual(
            result["repository"],
            "example/project",
        )

        self.assertEqual(
            result["files_scanned_count"],
            1,
        )

        self.assertEqual(
            result["files_scanned"],
            ["example.py"],
        )

        self.assertEqual(
            result["findings_count"],
            1,
        )

        self.assertEqual(
            result["findings"][0]["rule_id"],
            "PY001",
        )

        self.assertEqual(
            result["findings"][0]["file_path"],
            "example.py",
        )

        self.assertEqual(
            result["findings"][0]["line_number"],
            2,
        )

        self.assertEqual(
            result["skipped_files"],
            [],
        )

        self.assertEqual(mock_get.call_count, 3)

    # Security and Error Handling Tests

    @patch("review_assistant.github_review.github_get")
    def test_rejects_private_repository(self, mock_get):
        mock_get.return_value = {
            "private": True,
            "default_branch": "main",
        }

        with self.assertRaises(GitHubReviewError):
            review_repository(
                "https://github.com/example/private-project"
            )

        mock_get.assert_called_once()

    @patch("review_assistant.github_review.github_get")
    def test_rejects_truncated_repository_tree(self, mock_get):
        mock_get.side_effect = [
            {
                "private": False,
                "default_branch": "main",
            },
            {
                "truncated": True,
                "tree": [],
            },
        ]

        with self.assertRaises(GitHubReviewError):
            review_repository(
                "https://github.com/example/project"
            )

        self.assertEqual(mock_get.call_count, 2)

    @patch("review_assistant.github_review.github_get")
    def test_skips_oversized_python_file(self, mock_get):
        mock_get.side_effect = [
            {
                "private": False,
                "default_branch": "main",
            },
            {
                "truncated": False,
                "tree": [
                    {
                        "path": "large.py",
                        "type": "blob",
                        "size": 64 * 1024 + 1,
                        "sha": "a" * 40,
                    },
                ],
            },
        ]

        result = review_repository(
            "https://github.com/example/project"
        )

        self.assertEqual(
            result["files_scanned_count"],
            0,
        )

        self.assertEqual(
            result["findings_count"],
            0,
        )

        self.assertEqual(
            result["skipped_files"],
            ["large.py"],
        )

        self.assertEqual(mock_get.call_count, 2)

    @patch("review_assistant.github_review.github_get")
    def test_handles_github_api_failure(self, mock_get):
        mock_get.side_effect = GitHubReviewError(
            "GitHub API access is limited."
        )

        with self.assertRaises(GitHubReviewError):
            review_repository(
                "https://github.com/example/project"
            )

        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
