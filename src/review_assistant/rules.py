
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

    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"list", "dict", "set"}
    )


def _has_simple_guard(
    node: ast.Subscript,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    """Check whether indexing is inside a matching if statement."""
    if not isinstance(node.value, ast.Name):
        return False

    variable_name = node.value.id
    current = node

    while current in parents:
        parent = parents[current]

        if isinstance(parent, ast.If):
            if (
                current in parent.body
                and isinstance(parent.test, ast.Name)
                and parent.test.id == variable_name
            ):
                return True

        current = parent

    return False


def analyze_source(
    file_path: str,
    source: str,
    changed_line_numbers: set[int],
) -> list[Finding]:
    tree = ast.parse(source, filename=file_path)
    findings: list[Finding] = []

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

    def add_finding(rule_id, line, message, recommendation):
        if line in changed_line_numbers:
            findings.append(
                Finding(
                    rule_id=rule_id,
                    file_path=file_path,
                    line_number=line,
                    severity="warning",
                    message=message,
                    recommendation=recommendation,
                )
            )

    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            if (
                isinstance(node.slice, ast.Constant)
                and type(node.slice.value) is int
                and node.slice.value == 0
                and not _has_simple_guard(node, parents)
            ):
                add_finding(
                    "PY001",
                    node.lineno,
                    "Indexing at 0 can raise IndexError if the "
                    "sequence is empty.",
                    "Check that the sequence is non-empty before "
                    "indexing, or use a safe lookup.",
                )

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = [
                *node.args.defaults,
                *(
                    default
                    for default in node.args.kw_defaults
                    if default is not None
                ),
            ]

            for default in defaults:
                if _is_mutable_default(default):
                    add_finding(
                        "PY002",
                        default.lineno,
                        "Mutable default arguments are shared across "
                        "function calls, which can cause state to leak.",
                        "Use None as the default, then create a new "
                        "list, dictionary, or set inside the function.",
                    )

        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                add_finding(
                    "PY003",
                    node.lineno,
                    "A bare except catches nearly every exception, "
                    "which can hide unexpected errors.",
                    "Catch the specific exception types the code "
                    "expects to handle.",
                )

        elif isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]

            for index, operator in enumerate(node.ops):
                if not isinstance(operator, (ast.Eq, ast.NotEq)):
                    continue

                left = operands[index]
                right = operands[index + 1]

                if any(
                    isinstance(value, ast.Constant)
                    and value.value is None
                    for value in (left, right)
                ):
                    add_finding(
                        "PY004",
                        node.lineno,
                        "Equality comparisons with None may produce "
                        "unexpected results.",
                        "Use 'is None' or 'is not None' instead.",
                    )

                elif any(
                    isinstance(value, ast.Constant)
                    and type(value.value) is bool
                    for value in (left, right)
                ):
                    add_finding(
                        "PY007",
                        node.lineno,
                        "Comparing a value directly with True or False "
                        "may be unnecessary when the value is already boolean.",
                        "If the value is guaranteed to be boolean, "
                        "consider using the value directly or with 'not'. "
                        "Otherwise, keep the comparison if its exact "
                        "behavior is required.",
                    )

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "eval":
                    add_finding(
                        "PY005",
                        node.lineno,
                        "eval() can execute arbitrary expressions and "
                        "may be unsafe with untrusted input.",
                        "Avoid evaluating untrusted input. Use explicit "
                        "parsing or ast.literal_eval() for Python literals.",
                    )

                elif node.func.id == "exec":
                    add_finding(
                        "PY006",
                        node.lineno,
                        "exec() dynamically executes Python code and "
                        "may introduce security risks.",
                        "Replace dynamic execution with explicit "
                        "functions or controlled logic where possible.",
                    )

        elif isinstance(node, ast.Dict):
            seen_keys = set()

            for key in node.keys:
                if not isinstance(key, ast.Constant):
                    continue

                try:
                    hash(key.value)
                except TypeError:
                    continue

                if key.value in seen_keys:
                    add_finding(
                        "PY008",
                        key.lineno,
                        "A duplicate dictionary key overwrites "
                        "an earlier value.",
                        "Remove the duplicate key or give each "
                        "entry a unique key.",
                    )

                seen_keys.add(key.value)

    return sorted(
        findings,
        key=lambda finding: (finding.line_number, finding.rule_id),
    )
