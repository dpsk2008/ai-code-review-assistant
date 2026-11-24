
import sys
from dataclasses import asdict
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

from review_assistant.ai_review import AIReviewError, review_with_ai
from review_assistant.github_review import (
    GitHubReviewError,
    review_repository,
)
from review_assistant.rules import analyze_source


# Maximum submitted Python code size: 64 KB
MAX_CODE_BYTES = 64 * 1024


app = FastAPI(
    title="AI Code Review Assistant",
    description=(
        "Review Python code using static analysis, "
        "a locally running AI model, and public GitHub repositories."
    ),
    version="1.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


class ReviewRequest(BaseModel):
    code: str


class GitHubReviewRequest(BaseModel):
    repository_url: str


def validate_code(code: str) -> None:
    """Validate submitted Python code before analysis."""

    if not code.strip():
        raise HTTPException(
            status_code=422,
            detail="Please enter Python code to review.",
        )

    code_size = len(code.encode("utf-8"))

    if code_size > MAX_CODE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                "Submitted code is too large. "
                "The maximum allowed size is 64 KB."
            ),
        )


@app.get("/")
def home():
    """Serve the code review website."""

    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )


@app.post("/review")
def review_code(request: ReviewRequest):
    """Analyze Python code using AST review rules."""

    validate_code(request.code)

    try:
        line_numbers = set(
            range(
                1,
                len(request.code.splitlines()) + 1,
            )
        )

        findings = analyze_source(
            file_path="submitted_code.py",
            source=request.code,
            changed_line_numbers=line_numbers,
        )

        return {
            "findings": [
                asdict(finding)
                for finding in findings
            ]
        }

    except SyntaxError as error:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid Python syntax on line "
                f"{error.lineno}: {error.msg}"
            ),
        ) from error


@app.post("/review/ai")
def review_code_with_ai(request: ReviewRequest):
    """Analyze Python code using local Ollama AI."""

    validate_code(request.code)

    try:
        ai_response = review_with_ai(
            request.code
        )

        if (
            not isinstance(ai_response, str)
            or not ai_response.strip()
        ):
            raise HTTPException(
                status_code=502,
                detail=(
                    "The AI model returned an empty response. "
                    "Please try again."
                ),
            )

        return {
            "ai_review": ai_response
        }

    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail=(
                "The AI review took too long. "
                "Please try again with shorter code."
            ),
        ) from error

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to connect to the local AI model. "
                "Make sure Ollama is running."
            ),
        ) from error

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "The local AI model returned an error. "
                "Please try again."
            ),
        ) from error

    except AIReviewError as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "The local AI model returned an invalid response. "
                "Please try again."
            ),
        ) from error


@app.post("/review/github")
def review_github_repository(request: GitHubReviewRequest):
    """Analyze Python files from a public GitHub repository."""

    try:
        result = review_repository(
            request.repository_url
        )

        return result

    except GitHubReviewError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
