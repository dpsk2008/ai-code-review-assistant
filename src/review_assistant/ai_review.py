
import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:3b"


class AIReviewError(Exception):
    """Raised when Ollama returns an invalid AI review response."""


def review_with_ai(code: str) -> str:
    """Review Python code using a locally running Ollama model."""

    prompt = (
        "You are an experienced Python code reviewer.\n"
        "Analyze the following code without executing it.\n\n"

        "REVIEW GUIDELINES:\n"
        "1. Focus on real bugs, edge cases, and security risks.\n"
        "2. Identify only problems supported by the code.\n"
        "3. Do not claim code is bug-free without checking edge cases.\n"
        "4. Explain problems clearly using simple English.\n"
        "5. Avoid unnecessary complexity or unrelated improvements.\n"
        "6. Suggest the simplest practical fix for each issue.\n"
        "7. Do not repeat the same problem multiple times.\n"
        "8. If no clear issue exists, state that no obvious issues "
        "were found.\n\n"

        "OUTPUT FORMAT:\n"
        "ISSUE: Briefly describe the most important problem.\n"
        "WHY IT MATTERS: Explain what could go wrong.\n"
        "SUGGESTED FIX: Explain the simplest solution.\n"
        "CORRECTED CODE: Provide one corrected Python example "
        "when appropriate.\n\n"

        "Keep the entire response under 250 words.\n"
        "Do not include lengthy introductions or conclusions.\n"
        "Do not invent problems.\n\n"

        "PYTHON CODE TO REVIEW:\n"
        f"```python\n{code}\n```"
    )

    response = httpx.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 450,
            },
        },
        timeout=120.0,
    )

    response.raise_for_status()

    try:
        result = response.json()
    except ValueError as error:
        raise AIReviewError(
            "Ollama returned an invalid JSON response."
        ) from error

    if not isinstance(result, dict):
        raise AIReviewError(
            "Ollama returned an unexpected response format."
        )

    ai_response = result.get("response")

    if not isinstance(ai_response, str):
        raise AIReviewError(
            "Ollama response is missing valid review text."
        )

    if not ai_response.strip():
        raise AIReviewError(
            "Ollama returned an empty review."
        )

    return ai_response
