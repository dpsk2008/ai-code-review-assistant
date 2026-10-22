from dataclasses import dataclass
import re


_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class AddedLine:
    file_path: str
    line_number: int
    content: str


def parse_added_lines(diff_text: str) -> list[AddedLine]:
    """Extract added lines and their line numbers in the updated files."""
    added_lines: list[AddedLine] = []
    file_path: str | None = None
    new_line_number: int | None = None

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            file_path = None if path == "/dev/null" else path.removeprefix("b/")
            new_line_number = None

        elif line.startswith("@@ "):
            match = _HUNK_HEADER.match(line)
            if match is None:
                raise ValueError(f"Invalid unified diff hunk header: {line}")
            new_line_number = int(match.group(1))

        elif line.startswith("\\"):
            # Diff metadata, such as "\ No newline at end of file".
            continue

        elif line.startswith("+") and not line.startswith("+++"):
            if file_path is not None and new_line_number is not None:
                added_lines.append(
                    AddedLine(file_path, new_line_number, line[1:])
                )
                new_line_number += 1

        elif line.startswith("-") and not line.startswith("---"):
            # A removed line exists only in the old file, so it doesn't
            # advance the updated file's line number.
            continue

        elif line.startswith(" ") and new_line_number is not None:
            # Context lines exist in both versions.
            new_line_number += 1

    return added_lines