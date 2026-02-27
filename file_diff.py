"""Utility to find and display the differences between two files."""

import difflib
import os
import sys


class FileDiff:
    """Compare two files and report their differences."""

    def __init__(self, file1: str, file2: str):
        self.file1 = file1
        self.file2 = file2
        self._lines1: list[str] = []
        self._lines2: list[str] = []
        self._diff: list[str] = []

    def _validate_files(self) -> None:
        """Raise FileNotFoundError if either file does not exist."""
        for path in (self.file1, self.file2):
            if not os.path.isfile(path):
                raise FileNotFoundError(f"File not found: {path}")

    def _read_file(self, path: str) -> list[str]:
        """Read and return lines from a file."""
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()

    def compare(self) -> list[str]:
        """Compare the two files and return a unified diff."""
        self._validate_files()
        self._lines1 = self._read_file(self.file1)
        self._lines2 = self._read_file(self.file2)
        self._diff = list(
            difflib.unified_diff(
                self._lines1,
                self._lines2,
                fromfile=self.file1,
                tofile=self.file2,
                lineterm="",
            )
        )
        return self._diff

    def summary(self) -> dict:
        """Return a summary of additions, deletions, and unchanged lines."""
        if not self._diff:
            self.compare()

        added = sum(1 for line in self._diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in self._diff if line.startswith("-") and not line.startswith("---"))

        return {
            "file1": self.file1,
            "file2": self.file2,
            "additions": added,
            "deletions": removed,
            "total_changes": added + removed,
            "identical": len(self._diff) == 0,
        }

    def display(self) -> str:
        """Return a human-readable diff output."""
        diff_lines = self.compare()
        if not diff_lines:
            return f"Files '{self.file1}' and '{self.file2}' are identical."

        output_lines = []
        for line in diff_lines:
            if line.startswith("+++") or line.startswith("---"):
                output_lines.append(line)
            elif line.startswith("+"):
                output_lines.append(f"  + {line[1:]}")
            elif line.startswith("-"):
                output_lines.append(f"  - {line[1:]}")
            elif line.startswith("@@"):
                output_lines.append(line)
            else:
                output_lines.append(f"    {line}")

        stats = self.summary()
        output_lines.append("")
        output_lines.append(
            f"Summary: {stats['additions']} addition(s), "
            f"{stats['deletions']} deletion(s), "
            f"{stats['total_changes']} total change(s)"
        )
        return "\n".join(output_lines)


def main():
    if len(sys.argv) != 3:
        print("Usage: python file_diff.py <file1> <file2>")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]
    try:
        differ = FileDiff(file1, file2)
        print(differ.display())
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
