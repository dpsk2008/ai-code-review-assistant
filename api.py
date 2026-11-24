
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

from review_assistant.ai_review import review_with_ai
from review_assistant.rules import analyze_source

app = FastAPI(title="AI Code Review Assistant")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


class ReviewRequest(BaseModel):
    code: str


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.post("/review")
def review_code(request: ReviewRequest):
    try:
        line_numbers = set(range(1, len(request.code.splitlines()) + 1))

        findings = analyze_source(
            file_path="submitted_code.py",
            source=request.code,
            changed_line_numbers=line_numbers,
        )

        return {"findings": [asdict(finding) for finding in findings]}

    except SyntaxError as error:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid Python syntax on line {error.lineno}: {error.msg}",
        ) from error


@app.post("/review/ai")
def review_code_with_ai(request: ReviewRequest):
    if not request.code.strip():
        raise HTTPException(
            status_code=422,
            detail="Please enter Python code to review.",
        )

    try:
        ai_response = review_with_ai(request.code)

        return {"ai_review": ai_response}

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
            detail="The local AI model returned an error.",
        ) from error
