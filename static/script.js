
const codeInput = document.getElementById("code-input");
const lineNumbers = document.getElementById("line-numbers");
const highlightLayer = document.getElementById("highlight-layer");
const highlightedCode = document.getElementById("highlighted-code");

const reviewButton = document.getElementById("review-button");
const aiReviewButton = document.getElementById("ai-review-button");

const statusMessage = document.getElementById("status-message");
const findingsList = document.getElementById("findings-list");
const issueCount = document.getElementById("issue-count");

const aiStatusMessage = document.getElementById("ai-status-message");
const aiReviewOutput = document.getElementById("ai-review-output");
const aiReviewText = document.getElementById("ai-review-text");

const fileInput = document.getElementById("file-input");
const uploadButton = document.getElementById("upload-button");
const clearButton = document.getElementById("clear-button");
const fileName = document.getElementById("file-name");
const fileMessage = document.getElementById("file-message");

const MAX_FILE_SIZE = 1024 * 1024;

const ruleTitles = {
    PY001: "Potential IndexError",
    PY002: "Mutable Default Argument",
    PY003: "Bare Except Clause",
    PY004: "Incorrect None Comparison",
    PY005: "Potentially Unsafe eval()",
    PY006: "Potentially Unsafe exec()",
    PY007: "Unnecessary Boolean Comparison",
    PY008: "Duplicate Dictionary Key"
};

let activeLine = null;
let documentVersion = 0;

/* Active Line Highlight */

const lineHighlight = document.createElement("div");
lineHighlight.className = "active-code-line";
lineHighlight.hidden = true;
lineHighlight.setAttribute("aria-hidden", "true");

codeInput.parentElement.insertBefore(
    lineHighlight,
    highlightLayer
);

/* Editor Functions */

function updateLineNumbers() {
    const totalLines = codeInput.value.split("\n").length;
    const fragment = document.createDocumentFragment();

    for (let number = 1; number <= totalLines; number++) {
        const line = document.createElement("span");
        line.className = "line-number";
        line.textContent = number;

        if (number === activeLine) {
            line.classList.add("active");
        }

        fragment.appendChild(line);
    }

    lineNumbers.replaceChildren(fragment);
}

function updateHighlighting() {
    const code = codeInput.value + "\n";

    if (window.Prism && Prism.languages.python) {
        highlightedCode.innerHTML = Prism.highlight(
            code,
            Prism.languages.python,
            "python"
        );
    } else {
        highlightedCode.textContent = code;
    }
}

function syncEditorScroll() {
    lineNumbers.scrollTop = codeInput.scrollTop;
    highlightLayer.scrollTop = codeInput.scrollTop;
    highlightLayer.scrollLeft = codeInput.scrollLeft;

    if (activeLine !== null) {
        const styles = getComputedStyle(codeInput);
        const lineHeight = parseFloat(styles.lineHeight);
        const paddingTop = parseFloat(styles.paddingTop);

        const top =
            paddingTop +
            (activeLine - 1) * lineHeight -
            codeInput.scrollTop;

        lineHighlight.style.top = `${top}px`;
    }
}

function clearActiveLine() {
    activeLine = null;
    lineHighlight.hidden = true;

    document.querySelectorAll(".finding.active").forEach(
        (card) => {
            card.classList.remove("active");
        }
    );
}

function resetReview(message) {
    clearActiveLine();
    findingsList.replaceChildren();
    issueCount.textContent = "";
    statusMessage.textContent = message;
}

function resetAIReview(message) {
    aiReviewText.textContent = "";
    aiReviewOutput.hidden = true;
    aiStatusMessage.textContent = message;
    aiStatusMessage.classList.remove("error");
}

function updateEditor() {
    updateLineNumbers();
    updateHighlighting();
    syncEditorScroll();
}

function handleCodeChange() {
    documentVersion++;

    resetReview(
        "Code changed. Run a review for updated results."
    );

    resetAIReview(
        "Code changed. Run Review with AI for updated feedback."
    );

    updateEditor();
}

function showFileMessage(message, isError = false) {
    fileMessage.textContent = message;
    fileMessage.classList.toggle("error", isError);
}

/* Go to Line */

function goToLine(number, card) {
    const lines = codeInput.value.split("\n");

    if (number < 1 || number > lines.length) {
        return;
    }

    clearActiveLine();

    activeLine = number;
    lineHighlight.hidden = false;
    card.classList.add("active");

    updateLineNumbers();

    const start = lines
        .slice(0, number - 1)
        .reduce(
            (length, line) => length + line.length + 1,
            0
        );

    const styles = getComputedStyle(codeInput);
    const lineHeight = parseFloat(styles.lineHeight);

    codeInput.focus({ preventScroll: true });
    codeInput.setSelectionRange(start, start);

    codeInput.scrollTop = Math.max(
        0,
        (number - 1) * lineHeight -
        codeInput.clientHeight / 2
    );

    codeInput.scrollLeft = 0;

    syncEditorScroll();

    codeInput.closest(".workspace").scrollIntoView({
        behavior: window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches ? "auto" : "smooth",
        block: "center"
    });
}

/* File Upload */

uploadButton.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];

    if (!file) {
        return;
    }

    fileInput.value = "";
    showFileMessage("");

    if (!file.name.toLowerCase().endsWith(".py")) {
        showFileMessage(
            "Please select a Python (.py) file.",
            true
        );
        return;
    }

    if (file.size > MAX_FILE_SIZE) {
        showFileMessage(
            "File size must not exceed 1 MB.",
            true
        );
        return;
    }

    if (
        codeInput.value.trim() &&
        !window.confirm(
            "Replace the current code with this file?"
        )
    ) {
        return;
    }

    const version = ++documentVersion;

    try {
        const buffer = await file.arrayBuffer();

        const content = new TextDecoder("utf-8", {
            fatal: true
        }).decode(buffer);

        if (version !== documentVersion) {
            return;
        }

        codeInput.value = content;
        fileName.textContent = file.name;

        codeInput.scrollTop = 0;
        codeInput.scrollLeft = 0;
        codeInput.setSelectionRange(0, 0);

        resetReview(
            "File loaded. Click Review Code to begin."
        );

        resetAIReview(
            "File loaded. Click Review with AI to begin."
        );

        showFileMessage(
            "Python file loaded successfully."
        );

        updateEditor();

    } catch (error) {
        if (version === documentVersion) {
            showFileMessage(
                "Unable to read the file. Please select a UTF-8 Python file.",
                true
            );
        }
    }
});

/* Clear Editor */

clearButton.addEventListener("click", () => {
    if (
        codeInput.value.trim() &&
        !window.confirm(
            "Clear all code from the editor?"
        )
    ) {
        return;
    }

    documentVersion++;

    codeInput.value = "";
    fileInput.value = "";
    fileName.textContent = "Untitled.py";

    codeInput.scrollTop = 0;
    codeInput.scrollLeft = 0;

    showFileMessage("");

    resetReview(
        "Your review results will appear here."
    );

    resetAIReview(
        "Click Review with AI to generate an additional code review."
    );

    updateEditor();
    codeInput.focus();
});

/* Editor Events */

codeInput.addEventListener("input", handleCodeChange);
codeInput.addEventListener("scroll", syncEditorScroll);
window.addEventListener("resize", syncEditorScroll);

codeInput.addEventListener("keydown", (event) => {
    if (event.key !== "Tab" || event.shiftKey) {
        return;
    }

    event.preventDefault();

    const start = codeInput.selectionStart;
    const end = codeInput.selectionEnd;

    codeInput.setRangeText(
        "    ",
        start,
        end,
        "end"
    );

    handleCodeChange();
});

/* Static Analysis Finding Cards */

function createFindingCard(finding) {
    const card = document.createElement("article");
    card.className = "finding";

    const header = document.createElement("div");
    header.className = "finding-header";

    const title = document.createElement("h3");
    title.textContent =
        ruleTitles[finding.rule_id] || finding.rule_id;

    const severity = document.createElement("span");
    severity.className = "severity-label";
    severity.textContent = finding.severity;

    header.append(title, severity);

    const metadata = document.createElement("span");
    metadata.className = "finding-meta";
    metadata.textContent =
        `${finding.rule_id} · Line ${finding.line_number}`;

    const message = document.createElement("p");
    message.textContent = finding.message;

    const recommendation = document.createElement("div");
    recommendation.className = "recommendation";

    const recommendationTitle =
        document.createElement("strong");
    recommendationTitle.textContent = "Recommendation";

    const recommendationText =
        document.createElement("p");
    recommendationText.textContent =
        finding.recommendation;

    recommendation.append(
        recommendationTitle,
        recommendationText
    );

    const lineButton = document.createElement("button");
    lineButton.type = "button";
    lineButton.className = "goto-line";
    lineButton.textContent =
        `Go to line ${finding.line_number}`;

    lineButton.addEventListener("click", () => {
        goToLine(finding.line_number, card);
    });

    card.append(
        header,
        metadata,
        message,
        recommendation,
        lineButton
    );

    return card;
}

/* Read API Responses */

async function getAPIResponse(response) {
    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            typeof result.detail === "string"
                ? result.detail
                : "Unable to complete the review."
        );
    }

    return result;
}

/* Static Code Review */

reviewButton.addEventListener("click", async () => {
    const code = codeInput.value;
    const version = documentVersion;

    resetReview("");
    updateLineNumbers();

    if (!code.trim()) {
        statusMessage.textContent =
            "Please enter some Python code first.";
        return;
    }

    reviewButton.disabled = true;
    reviewButton.textContent = "Reviewing...";
    statusMessage.textContent =
        "Analyzing your code...";

    try {
        const response = await fetch("/review", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ code })
        });

        const result = await getAPIResponse(response);

        if (version !== documentVersion) {
            return;
        }

        const findings = result.findings;

        issueCount.textContent =
            `${findings.length} issue${findings.length === 1 ? "" : "s"} found`;

        if (findings.length === 0) {
            statusMessage.textContent =
                "No issues detected by the current review rules.";
            return;
        }

        statusMessage.textContent = "";

        for (const finding of findings) {
            findingsList.appendChild(
                createFindingCard(finding)
            );
        }

    } catch (error) {
        if (version === documentVersion) {
            statusMessage.textContent =
                error instanceof Error
                    ? error.message
                    : "Unable to review the code.";
        }

    } finally {
        reviewButton.disabled = false;
        reviewButton.textContent = "Review Code";
    }
});


/* Format AI Review Results */

function formatAIReview(review) {
    const fragment = document.createDocumentFragment();
    const lines = review.split("\n");

    let codeBlock = null;
    let codeLines = [];
    let inCodeBlock = false;

    function appendCodeBlock() {
        if (codeLines.length === 0) {
            return;
        }

        const pre = document.createElement("pre");
        pre.className = "ai-code-block";

        const code = document.createElement("code");
        code.className = "language-python";
        code.textContent = codeLines.join("\n");

        if (window.Prism && Prism.languages.python) {
            Prism.highlightElement(code);
        }

        pre.appendChild(code);
        fragment.appendChild(pre);

        codeLines = [];
        codeBlock = null;
    }

    for (const line of lines) {
        const trimmed = line.trim();

        if (trimmed.startsWith("```")) {
            if (inCodeBlock) {
                appendCodeBlock();
                inCodeBlock = false;
            } else {
                inCodeBlock = true;
                codeLines = [];
            }

            continue;
        }

        if (inCodeBlock) {
            codeLines.push(line);
            continue;
        }

        if (!trimmed) {
            continue;
        }

        const sections = [
            "ISSUE:",
            "WHY IT MATTERS:",
            "SUGGESTED FIX:",
            "CORRECTED CODE:"
        ];

        const matchedSection = sections.find(
            (section) => trimmed.startsWith(section)
        );

        if (matchedSection) {
            const container = document.createElement("div");
            container.className = "ai-review-section";

            const heading = document.createElement("h4");
            heading.textContent =
                matchedSection.replace(":", "");

            container.appendChild(heading);

            const content = trimmed
                .slice(matchedSection.length)
                .trim();

            if (content) {
                const paragraph = document.createElement("p");
                paragraph.textContent = content;
                container.appendChild(paragraph);
            }

            fragment.appendChild(container);
        } else {
            const paragraph = document.createElement("p");
            paragraph.className = "ai-review-paragraph";
            paragraph.textContent = line;

            fragment.appendChild(paragraph);
        }
    }

    if (inCodeBlock) {
        appendCodeBlock();
    }

    return fragment;
}

/* AI Code Review */

aiReviewButton.addEventListener("click", async () => {
    const code = codeInput.value;
    const version = documentVersion;

    resetAIReview("");

    if (!code.trim()) {
        aiStatusMessage.textContent =
            "Please enter some Python code first.";
        return;
    }

    if (new Blob([code]).size > MAX_FILE_SIZE) {
        aiStatusMessage.textContent =
            "AI review is limited to 1 MB of Python code.";
        return;
    }

    aiReviewButton.disabled = true;
    aiReviewButton.textContent = "Reviewing with AI...";

    aiStatusMessage.textContent =
        "The local AI model is analyzing your code.";

    try {
        const response = await fetch("/review/ai", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ code })
        });

        const result = await getAPIResponse(response);

        if (version !== documentVersion) {
            return;
        }

        if (
            typeof result.ai_review !== "string" ||
            !result.ai_review.trim()
        ) {
            throw new Error(
                "The AI returned an empty review. Please try again."
            );
        }

       // Display structured AI feedback safely.
aiReviewText.replaceChildren(
    formatAIReview(result.ai_review)
);
aiReviewOutput.hidden = false;

        aiStatusMessage.textContent = "";

        aiReviewOutput.scrollIntoView({
            behavior: window.matchMedia(
                "(prefers-reduced-motion: reduce)"
            ).matches ? "auto" : "smooth",
            block: "start"
        });

    } catch (error) {
        if (version === documentVersion) {
            aiReviewOutput.hidden = true;

            aiStatusMessage.textContent =
                error instanceof Error
                    ? error.message
                    : "Unable to complete the AI review.";

            aiStatusMessage.classList.add("error");
        }

    } finally {
        aiReviewButton.disabled = false;
        aiReviewButton.textContent = "Review with AI";
    }
});

/* Initialize Editor */

updateEditor();
