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


def _is_mutable_default(node: ast.expr) -> bool:
    """Return whether an AST expression creates a mutable default value."""
    mutable_literals = (
        ast.List,
        ast.Dict,
        ast.Set,
        ast.ListComp,
        ast.DictComp,
        ast.SetComp,
    )

    if isinstance(node, mutable_literals):
        return True

    # Also catch defaults such as list(), dict(), and set().
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "dict", "set"}
    )


def analyze_source(
    file_path: str,
    source: str,
    changed_line_numbers: set[int],
) -> list[Finding]:
    """Find supported issues on changed lines in Python source."""
    tree = ast.parse(source, filename=file_path)
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
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

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = [
                *node.args.defaults,
                *(default for default in node.args.kw_defaults if default is not None),
            ]

            for default in defaults:
                if (
                    _is_mutable_default(default)
                    and default.lineno in changed_line_numbers
                ):
                    findings.append(
                        Finding(
                            rule_id="PY002",
                            file_path=file_path,
                            line_number=default.lineno,
                            severity="warning",
                            message=(
                                "Mutable default arguments are shared across "
                                "function calls, which can cause state to leak."
                            ),
                            recommendation=(
                                "Use None as the default, then create a new "
                                "list, dictionary, or set inside the function."
                            ),
                        )
                    )

    return sorted(
        findings,
        key=lambda finding: (finding.line_number, finding.rule_id),
    )