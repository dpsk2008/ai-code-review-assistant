
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


/* =========================================
   GitHub Repository Review
   ========================================= */

const githubReviewForm =
    document.getElementById("github-review-form");

const githubRepositoryURL =
    document.getElementById("github-repository-url");

const githubReviewButton =
    document.getElementById("github-review-button");

const githubStatusMessage =
    document.getElementById("github-status-message");

const githubIssueCount =
    document.getElementById("github-issue-count");

const githubReviewSummary =
    document.getElementById("github-review-summary");

const githubFindingsList =
    document.getElementById("github-findings-list");

const githubSkippedFiles =
    document.getElementById("github-skipped-files");

let githubRequestVersion = 0;


/* Clear Previous GitHub Results */

function clearGitHubResults(message = "") {
    githubRequestVersion += 1;

    githubStatusMessage.textContent = message;
    githubStatusMessage.classList.remove("error");

    githubIssueCount.textContent = "";

    githubReviewSummary.hidden = true;
    githubReviewSummary.replaceChildren();

    githubFindingsList.replaceChildren();

    githubSkippedFiles.hidden = true;
    githubSkippedFiles.replaceChildren();
}


/* Create a GitHub Finding Card */

function createGitHubFindingCard(finding) {
    const card = document.createElement("article");
    card.className = "finding";

    const header = document.createElement("div");
    header.className = "finding-header";

    const title = document.createElement("h3");
    title.textContent =
        ruleTitles[finding.rule_id] ||
        finding.rule_id ||
        "Finding";

    const severity = document.createElement("span");
    severity.className = "severity-label";
    severity.textContent = finding.severity || "warning";

    header.append(title, severity);

    const metadata = document.createElement("span");
    metadata.className = "finding-meta";
    metadata.textContent =
        `${finding.rule_id} · Line ${finding.line_number}`;

    const description = document.createElement("p");
    description.textContent = finding.message || "";

    const recommendation = document.createElement("div");
    recommendation.className = "recommendation";

    const heading = document.createElement("strong");
    heading.textContent = "Recommendation";

    const advice = document.createElement("p");
    advice.textContent = finding.recommendation || "";

    recommendation.append(heading, advice);

    card.append(
        header,
        metadata,
        description,
        recommendation
    );

    return card;
}


/* Display GitHub Repository Results */


function renderGitHubResults(result) {
    const findings = Array.isArray(result.findings)
        ? result.findings
        : [];

    const scanned = Array.isArray(result.files_scanned)
        ? result.files_scanned
        : [];

    const skipped = Array.isArray(result.skipped_files)
        ? result.skipped_files
        : [];

    const name = typeof result.repository === "string"
        ? result.repository
        : "Repository";

    githubIssueCount.textContent =
        `${findings.length} issue${findings.length === 1 ? "" : "s"} found`;

    const nameText = document.createElement("strong");
    nameText.textContent = name;

    const isPartialScan = skipped.length > 0;
    const scanStatus = isPartialScan
        ? "Partial scan"
        : "Complete scan";

    const counts = document.createElement("span");
    counts.textContent =
        ` · ${scanStatus}` +
        ` · ${scanned.length} Python file${scanned.length === 1 ? "" : "s"} scanned` +
        ` · ${skipped.length} skipped`;

    githubReviewSummary.replaceChildren(
        nameText,
        counts
    );

    githubReviewSummary.hidden = false;

    /* Group findings by filename */

    const byFile = new Map();

    for (const finding of findings) {
        if (!finding || typeof finding !== "object") {
            continue;
        }

        const path =
            typeof finding.file_path === "string"
                ? finding.file_path
                : "Unknown file";

        if (!byFile.has(path)) {
            byFile.set(path, []);
        }

        byFile.get(path).push(finding);
    }

    githubFindingsList.replaceChildren();

    for (const [path, fileFindings] of byFile) {
        const section = document.createElement("section");
        section.className = "github-file-group";

        const heading = document.createElement("h3");
        heading.textContent = path;

        section.appendChild(heading);

        for (const finding of fileFindings) {
            section.appendChild(
                createGitHubFindingCard(finding)
            );
        }

        githubFindingsList.appendChild(section);
    }

    /* Display skipped files */

    if (skipped.length) {
        const details = document.createElement("details");

        const summary = document.createElement("summary");
        summary.textContent =
            `${skipped.length} file${skipped.length === 1 ? "" : "s"} skipped`;

        const explanation = document.createElement("p");
        explanation.textContent =
            "Files may be skipped because of the 10-file scan limit, " +
            "the 64 KB per-file limit, unsupported content, " +
            "or Python parsing errors.";

        const list = document.createElement("ul");

        for (const path of skipped) {
            const item = document.createElement("li");
            item.textContent = String(path);
            list.appendChild(item);
        }

        details.append(
            summary,
            explanation,
            list
        );

        githubSkippedFiles.replaceChildren(details);
        githubSkippedFiles.hidden = false;
    }

    /* Display accurate scan status */

    if (isPartialScan) {
        githubStatusMessage.textContent = findings.length
            ? "Partial scan: some Python files were skipped or not analyzed. " +
              "Findings below apply only to scanned files. " +
              "This is not a full repository review."
            : "Partial scan: no issues were detected in the scanned files, " +
              "but some Python files were skipped. " +
              "This is not a full repository review.";
    } else {
        githubStatusMessage.textContent = findings.length
            ? "Scan complete for the repository's Python files. " +
              "Review the potential findings below."
            : "Scan complete for the repository's Python files. " +
              "No issues detected by the current review rules.";
    }
}


/* Reset Results When URL Changes */

githubRepositoryURL.addEventListener("input", () => {
    clearGitHubResults(
        "Repository URL changed. Run a new review for updated results."
    );
});


/* Submit GitHub Review */

githubReviewForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const repositoryURL = githubRepositoryURL.value.trim();

    clearGitHubResults("");

    const version = githubRequestVersion;

    if (!repositoryURL) {
        githubStatusMessage.textContent =
            "Please enter a GitHub repository URL.";
        return;
    }

    githubReviewButton.disabled = true;
    githubReviewButton.textContent = "Scanning...";

    githubStatusMessage.textContent =
        "Fetching and analyzing public Python files...";

    try {
        const response = await fetch("/review/github", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                repository_url: repositoryURL
            })
        });

        const result = await getAPIResponse(response);

        if (version !== githubRequestVersion) {
            return;
        }

        renderGitHubResults(result);

    } catch (error) {
        if (version !== githubRequestVersion) {
            return;
        }

        githubStatusMessage.classList.add("error");

        githubStatusMessage.textContent =
            error instanceof Error
                ? error.message
                : "Unable to review the GitHub repository.";

    } finally {
        githubReviewButton.disabled = false;
        githubReviewButton.textContent = "Review Repository";
    }
});
