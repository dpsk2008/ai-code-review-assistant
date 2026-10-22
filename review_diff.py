import argparse
from pathlib import Path
import subprocess

from review_assistant.diff_parser import parse_added_lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show added lines between two Python files."
    )
    parser.add_argument("before", type=Path, help="Path to the original file")
    parser.add_argument("after", type=Path, help="Path to the updated file")
    args = parser.parse_args()

    for path in (args.before, args.after):
        if not path.is_file():
            parser.error(f"File does not exist: {path}")

    result = subprocess.run(
        [
            "git",
            "diff",
            "--no-index",
            "--unified=0",
            "--",
            str(args.before),
            str(args.after),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Git returns 1 when it finds differences; that's expected.
    if result.returncode not in (0, 1):
        print(result.stderr, end="")
        return result.returncode

    added_lines = parse_added_lines(result.stdout)

    if not added_lines:
        print("No added lines found.")
        return 0

    print(f"Added lines ({len(added_lines)}):")
    for line in added_lines:
        print(f"{line.file_path}:{line.line_number}: {line.content}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())