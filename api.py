
import sys
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

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
