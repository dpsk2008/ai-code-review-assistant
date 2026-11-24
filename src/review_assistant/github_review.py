
import base64
import binascii
import re
from dataclasses import asdict
from urllib.parse import quote, urlsplit

import httpx

from review_assistant.rules import analyze_source


GITHUB_API = "https://api.github.com"
MAX_FILES = 10
MAX_FILE_BYTES = 64 * 1024

OWNER_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")
REPO_PATTERN = re.compile(r"[A-Za-z0-9_.-]+")
SHA_PATTERN = re.compile(r"[a-fA-F0-9]{40}")


class GitHubReviewError(Exception):
    """Raised when a GitHub repository cannot be reviewed."""


def parse_repository_url(url: str) -> tuple[str, str]:
    """Extract and validate the owner and repository name."""

    try:
        parsed = urlsplit(url.strip())
    except ValueError as error:
        raise GitHubReviewError(
            "Invalid GitHub repository URL."
        ) from error

    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() != "github.com"
        or parsed.query
        or parsed.fragment
    ):
        raise GitHubReviewError(
            "Enter a valid HTTPS GitHub repository URL."
        )

    parts = parsed.path.strip("/").split("/")

    if len(parts) != 2:
        raise GitHubReviewError(
            "Use a repository URL such as "
            "https://github.com/owner/repository"
        )

    owner, repo = parts

    if repo.endswith(".git"):
        repo = repo[:-4]

    if (
        not OWNER_PATTERN.fullmatch(owner)
        or not REPO_PATTERN.fullmatch(repo)
        or repo in {".", ".."}
        or len(repo) > 100
    ):
        raise GitHubReviewError(
            "Invalid GitHub owner or repository name."
        )

    return owner, repo


def github_get(client: httpx.Client, path: str, params=None):
    """Request JSON data from GitHub's REST API."""

    try:
        response = client.get(
            f"{GITHUB_API}{path}",
            params=params,
        )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as error:
        status = error.response.status_code

        if status == 404:
            message = (
                "Repository or file not found. "
                "Only accessible public repositories are supported."
            )
        elif status in (403, 429):
            message = (
                "GitHub API access is limited or unavailable. "
                "Please try again later."
            )
        else:
            message = "GitHub returned an error."

        raise GitHubReviewError(message) from error

    except httpx.RequestError as error:
        raise GitHubReviewError(
            "Unable to connect to GitHub."
        ) from error

    except ValueError as error:
        raise GitHubReviewError(
            "GitHub returned an invalid JSON response."
        ) from error


def review_repository(repository_url: str) -> dict:
    """Run static analysis on Python files in a public repository."""

    owner, repo = parse_repository_url(repository_url)

    api_root = f"/repos/{owner}/{repo}"

    findings = []
    files_scanned = []
    skipped_files = []

    with httpx.Client(
        timeout=15.0,
        follow_redirects=False,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "AI-Code-Review-Assistant",
        },
    ) as client:

        repository = github_get(client, api_root)

        if not isinstance(repository, dict):
            raise GitHubReviewError(
                "GitHub returned invalid repository information."
            )

        if repository.get("private") is not False:
            raise GitHubReviewError(
                "Only public repositories are supported."
            )

        default_branch = repository.get("default_branch")

        if not isinstance(default_branch, str) or not default_branch:
            raise GitHubReviewError(
                "The repository has no valid default branch."
            )

        encoded_branch = quote(default_branch, safe="")

        tree_data = github_get(
            client,
            f"{api_root}/git/trees/{encoded_branch}",
            params={"recursive": "1"},
        )

        if (
            not isinstance(tree_data, dict)
            or not isinstance(tree_data.get("tree"), list)
        ):
            raise GitHubReviewError(
                "Unable to read the repository file tree."
            )

        if tree_data.get("truncated"):
            raise GitHubReviewError(
                "The repository is too large for a complete scan."
            )

        python_files = []

        for entry in tree_data["tree"]:
            if not isinstance(entry, dict):
                continue

            path = entry.get("path")
            size = entry.get("size")
            sha = entry.get("sha")

            if (
                entry.get("type") != "blob"
                or not isinstance(path, str)
                or not path.endswith(".py")
            ):
                continue

            if (
                not isinstance(size, int)
                or size < 0
                or size > MAX_FILE_BYTES
                or not isinstance(sha, str)
                or not SHA_PATTERN.fullmatch(sha)
            ):
                skipped_files.append(path)
                continue

            python_files.append((path, sha))

        python_files.sort()

        selected_files = python_files[:MAX_FILES]

        skipped_files.extend(
            path for path, _ in python_files[MAX_FILES:]
        )

        for path, sha in selected_files:
            blob_data = github_get(
                client,
                f"{api_root}/git/blobs/{sha}",
            )

            if (
                not isinstance(blob_data, dict)
                or blob_data.get("encoding") != "base64"
                or not isinstance(blob_data.get("content"), str)
            ):
                skipped_files.append(path)
                continue

            try:
                content = base64.b64decode(
                    blob_data["content"],
                    validate=False,
                )

                if len(content) > MAX_FILE_BYTES:
                    skipped_files.append(path)
                    continue

                source = content.decode("utf-8-sig")

            except (ValueError, UnicodeError, binascii.Error):
                skipped_files.append(path)
                continue

            try:
                changed_lines = set(
                    range(1, len(source.splitlines()) + 1)
                )

                file_findings = analyze_source(
                    file_path=path,
                    source=source,
                    changed_line_numbers=changed_lines,
                )

                findings.extend(
                    asdict(finding)
                    for finding in file_findings
                )

                files_scanned.append(path)

            except SyntaxError:
                skipped_files.append(path)

    return {
        "repository": f"{owner}/{repo}",
        "files_scanned": files_scanned,
        "files_scanned_count": len(files_scanned),
        "findings_count": len(findings),
        "findings": findings,
        "skipped_files": skipped_files,
    }
