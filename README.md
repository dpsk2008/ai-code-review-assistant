# AI Code Review Assistant

A Python-based code review application that combines **AST-based static analysis**, **locally hosted AI**, and **GitHub repository scanning** to identify potential bugs, explain programming issues, and recommend practical improvements.

Built with Python, FastAPI, JavaScript, HTML, CSS, and Ollama, the application provides an interactive interface for reviewing Python code without executing the submitted code.

## Features

### 1. Python Static Analysis

Uses Python's Abstract Syntax Tree (AST) to detect common programming issues.

The analyzer supports eight review rules:

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

Each finding includes a rule identifier, severity, line number, explanation, and recommended improvement.

### 2. AI-Powered Code Review

Integrates **Ollama** with **Qwen2.5-Coder 3B** to generate contextual feedback.

AI reviews can include:

- Potential programming issues
- Explanations of why issues matter
- Practical recommendations
- Suggested corrected Python code

AI feedback is displayed separately from deterministic static-analysis findings.

The model runs locally through Ollama. It is a pretrained model, not a custom-trained machine learning model.

### 3. GitHub Repository Review

Supports read-only static analysis of public GitHub repositories through the GitHub REST API.

Features include:

- GitHub repository URL validation
- Public repository scanning
- Prioritization of application code over examples and tests
- Analysis of up to 10 eligible Python files
- A 64 KB per-file size limit
- Findings grouped by filename
- Reporting of skipped files
- Complete or partial scan status

Repository code is analyzed without being executed.

The current implementation reviews repository files, not GitHub pull-request changes.

### 4. Interactive Web Interface

The responsive website provides:

- Python code editor
- Syntax highlighting using Prism.js
- Line numbers and issue navigation
- Python file uploads
- Static-analysis results
- Formatted AI-generated feedback
- GitHub repository review interface
- Loading, error, and status messages
- Keyboard navigation and editor indentation support

The website has been checked at a 400-pixel mobile viewport.

### 5. API Validation and Error Handling

The FastAPI backend includes:

- Empty-input validation
- 64 KB submitted-code size limit
- Invalid Python syntax handling
- AI connection and timeout error handling
- AI response validation
- GitHub URL and repository validation
- GitHub API error handling

These protections support local development but do not constitute a complete production security audit.

### 6. Automated Testing and Continuous Integration

The project uses Python's `unittest` framework.

Tests cover static-analysis rules, diff parsing, FastAPI endpoints, AI response handling with mocks, GitHub URL validation, repository scanning, and error handling.

**Latest local verification: 71 automated tests passing.**

GitHub Actions runs automated tests as part of the continuous integration workflow.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core analysis engine |
| Python AST | Static code analysis |
| FastAPI | Backend and REST API |
| HTML and CSS | Responsive user interface |
| JavaScript | Frontend interactions |
| Prism.js | Syntax highlighting |
| Ollama | Local AI inference |
| Qwen2.5-Coder 3B | AI-generated code feedback |
| HTTPX | HTTP requests |
| unittest | Automated tests |
| GitHub REST API | Repository access |
| GitHub Actions | Continuous integration |

## Project Structure

```text
ai-code-review-assistant/
├── .github/
│   └── workflows/
│       └── tests.yml
├── samples/
│   ├── before.py
│   └── after.py
├── src/
│   └── review_assistant/
│       ├── __init__.py
│       ├── ai_review.py
│       ├── diff_parser.py
│       ├── github_review.py
│       └── rules.py
├── static/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── tests/
│   ├── test_ai_review.py
│   ├── test_api.py
│   ├── test_diff_parser.py
│   ├── test_github_api.py
│   ├── test_github_review.py
│   ├── test_ollama_client.py
│   └── test_rules.py
├── .gitignore
├── api.py
├── requirements.txt
├── review_diff.py
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12
- Git
- Ollama
- Qwen2.5-Coder 3B for AI reviews

### 1. Clone the Repository

```bash
git clone https://github.com/dpsk2008/ai-code-review-assistant.git
cd ai-code-review-assistant
```

### 2. Create a Virtual Environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Ollama

Install Ollama from https://ollama.com/download.

Download the model:

```bash
ollama pull qwen2.5-coder:3b
```

Ensure Ollama is running before requesting AI-powered reviews.

### 5. Start the Application

```bash
python -m uvicorn api:app --reload
```

Open the website:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serve the website |
| POST | `/review` | Analyze submitted Python code |
| POST | `/review/ai` | Generate an AI-powered code review |
| POST | `/review/github` | Analyze a public GitHub repository |

### Example: Static Analysis

Request:

```json
{
  "code": "def get_first(items):\n    return items[0]"
}
```

Submit to:

`POST /review`

The analyzer can identify a potential `IndexError` when the sequence is empty.

### Example: GitHub Repository Review

Request:

```json
{
  "repository_url": "https://github.com/dpsk2008/ai-code-review-assistant"
}
```

Submit to:

`POST /review/github`

The response includes the repository name, scanned files, findings, file counts, and skipped files.

### Example: AI Review

Submit Python code to:

`POST /review/ai`

The application sends the submitted code to the locally running Ollama model and returns AI-generated feedback.

AI suggestions can be inaccurate and should be independently reviewed.

## Running Tests

Run the complete test suite:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Latest locally verified result:

```text
Ran 71 tests

OK
```

Check JavaScript syntax:

```bash
node --check static/script.js
```

## How It Works

1. The user enters Python code, uploads a Python file, or supplies a public GitHub repository URL.
2. The FastAPI backend validates the request.
3. The AST analyzer parses Python code without executing it.
4. Static-analysis rules identify potential problems.
5. Findings are returned with explanations and line numbers.
6. The user can optionally request an AI-powered code review.
7. Ollama generates contextual feedback using Qwen2.5-Coder 3B.
8. The frontend displays the results.

For repository reviews, the application retrieves eligible Python files from GitHub and performs static analysis.

## Current Limitations

- Static analysis supports Python only.
- Eight AST rules are currently implemented.
- Static-analysis findings are potential issues, not proof of bugs.
- AI review requires Ollama to be running locally.
- AI-generated recommendations may be incorrect.
- Repository scans are limited to 10 eligible Python files.
- GitHub scanning currently supports accessible public repositories.
- Large or unsupported files may be skipped.
- Pull-request-specific review is not yet implemented.
- The application is primarily intended for local development and demonstration.
- Production authentication, deployment hardening, and comprehensive security auditing are not yet complete.

## Future Improvements

Potential future improvements include:

- Additional static-analysis rules
- More comprehensive regression testing
- Pull-request and changed-line review integration
- Improved AI response validation
- Improved analysis accuracy and reduced false positives
- More detailed code-review reporting
- Production deployment support
- Evaluation of a separately trained machine learning component

A custom ML component remains an optional future enhancement, not a currently implemented feature.

## Project Status

**Working prototype — Final Quality Review**

Implemented functionality includes the Python AST analyzer, local AI integration, interactive website, public GitHub repository scanning, and automated testing.

The project is undergoing final documentation, accessibility, and security review.

## Author

**Deepinder Pal Singh Kalra**

Computer Science Student

Developed as a practical software engineering project exploring static analysis, backend API development, AI integration, frontend engineering, testing, and continuous integration.