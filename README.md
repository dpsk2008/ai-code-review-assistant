# AI Code Review Assistant

A Python-based code review application that combines static code analysis with locally hosted AI to detect potential bugs, explain programming issues, and recommend practical improvements.

Built with **Python, FastAPI, JavaScript, HTML, CSS, and Ollama**, the application provides an interactive website for reviewing Python code.

## Features

### 1. Python Static Analysis

Uses Python's Abstract Syntax Tree (AST) to identify common programming issues without executing submitted code.

The analyzer currently supports eight review rules:

| Rule | Description |
|---|---|
| PY001 | Potential IndexError when accessing index zero |
| PY002 | Mutable default function arguments |
| PY003 | Bare exception handlers |
| PY004 | Incorrect comparisons with None |
| PY005 | Potentially unsafe eval() usage |
| PY006 | Potentially unsafe exec() usage |
| PY007 | Unnecessary boolean comparisons |
| PY008 | Duplicate dictionary keys |

### 2. AI-Powered Code Review

Integrates **Ollama and Qwen2.5-Coder 3B** to provide contextual feedback on Python code.

AI reviews include:

- Identification of potential programming issues
- Explanations of why problems matter
- Recommendations for resolving bugs
- Suggested corrected Python code

AI-generated recommendations are presented separately from deterministic static-analysis results.

### 3. Interactive Web Interface

The application provides a responsive code-review interface featuring:

- Python code editor
- Syntax highlighting and line numbers
- Python file uploads
- Navigation to flagged lines
- Static analysis findings with explanations
- AI-generated reviews with formatted code examples
- Clear error and status messages

### 4. Automated Testing

Uses Python's `unittest` framework to test:

- Static analysis rules
- Git diff parsing
- FastAPI endpoints
- AI endpoint behavior using mocked responses

The project currently includes **39 automated tests**.

GitHub Actions runs the test suite automatically as part of the continuous integration workflow.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core analysis engine |
| Python AST | Static code analysis |
| FastAPI | REST API and backend |
| HTML | Website structure |
| CSS | Responsive interface styling |
| JavaScript | Interactive frontend |
| Prism.js | Python syntax highlighting |
| Ollama | Local AI inference |
| Qwen2.5-Coder 3B | AI-powered code review |
| unittest | Automated testing |
| GitHub Actions | Continuous integration |

## Project Structure

```text
ai-code-review-assistant/
├── .github/
│   └── workflows/
│       └── tests.yml
├── samples/
├── src/
│   └── review_assistant/
│       ├── __init__.py
│       ├── ai_review.py
│       ├── diff_parser.py
│       └── rules.py
├── static/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── tests/
│   ├── test_ai_review.py
│   ├── test_api.py
│   ├── test_diff_parser.py
│   └── test_rules.py
├── .gitignore
├── api.py
├── requirements.txt
├── review_diff.py
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12 or a compatible Python 3 version
- Git
- Ollama
- Qwen2.5-Coder 3B model

### 1. Clone the Repository

```bash
git clone https://github.com/dpsk2008/ai-code-review-assistant.git
cd ai-code-review-assistant
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Set Up Ollama

Install Ollama from:

https://ollama.com/download

Download the model:

```bash
ollama pull qwen2.5-coder:3b
```

Make sure the Ollama service is running before requesting AI reviews.

### 5. Start the Application

```bash
python -m uvicorn api:app --reload
```

Open the application:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the application website |
| POST | `/review` | Performs Python AST analysis |
| POST | `/review/ai` | Generates an AI-powered code review |

### Example: Static Analysis

Request:

```json
{
  "code": "def get_first(items):\n    return items[0]"
}
```

The static analyzer identifies a potential `IndexError` when the input sequence is empty.

### Example: AI Review

The same request can be submitted to `/review/ai`.

The AI responds with an explanation of the issue and may suggest a safer implementation.

AI-generated responses can vary and should be reviewed before applying changes.

## Running Tests

Run the full automated test suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The latest locally verified test suite completed successfully with 39 passing tests.

## How It Works

1. The user enters Python code or uploads a `.py` file.
2. The frontend submits the code to the FastAPI backend.
3. The static analyzer parses the Python source using AST.
4. Supported review rules identify potential issues.
5. Findings are returned with line numbers and recommendations.
6. Optionally, the user requests an AI-powered review.
7. Ollama processes the code using Qwen2.5-Coder.
8. The website displays AI feedback separately from static-analysis findings.

Submitted code is analyzed without being executed by the application's review engine.

## Current Limitations

- Static analysis currently supports Python only.
- The rule-based analyzer detects a defined set of patterns rather than every possible bug.
- AI review requires a locally running Ollama service.
- AI-generated recommendations may be inaccurate.
- The application is currently intended for local development and testing, not public production deployment.

## Future Improvements

- GitHub repository and pull-request review integration
- Additional Python analysis rules
- Improved AI response quality and validation
- Expanded automated testing
- Performance, security, and accessibility improvements
- Production deployment support

## Project Status

**Active Development**

The core static analyzer, web interface, local AI integration, and automated test suite are functional.

Additional repository integration, security improvements, and deployment preparation are planned.

## Author

**Deepinder Pal Singh Kalra**

Computer Science Student

Developed as a practical software engineering project exploring static analysis, backend APIs, AI integration, frontend development, automated testing, and continuous integration.