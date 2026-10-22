import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    rule_id: str
    file_path: str
    line_number: int
    severity: str
    message: str
    recommendation: str


def analyze_source(
    file_path: str,
    source: str,
    changed_line_numbers: set[int],
) -> list[Finding]:
    """Find possible unsafe sequence[0] accesses on changed lines."""
    tree = ast.parse(source, filename=file_path)
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue

        is_zero_index = (
            isinstance(node.slice, ast.Constant)
            and type(node.slice.value) is int
            and node.slice.value == 0
        )
        is_changed_line = node.lineno in changed_line_numbers

        if is_zero_index and is_changed_line:
            findings.append(
                Finding(
                    rule_id="PY001",
                    file_path=file_path,
                    line_number=node.lineno,
                    severity="warning",
                    message=(
                        "Indexing at 0 can raise IndexError if the "
                        "sequence is empty."
                    ),
                    recommendation=(
                        "Check that the sequence is non-empty before "
                        "indexing, or use a safe lookup."
                    ),
                )
            )

    return sorted(findings, key=lambda finding: finding.line_number)