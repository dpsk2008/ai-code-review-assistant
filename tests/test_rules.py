import unittest

from review_assistant.rules import analyze_source


class AnalyzeSourceTests(unittest.TestCase):
    def test_flags_zero_index_on_a_changed_line(self):
        source = (
            "def get_first(users):\n"
            "    return users[0]\n"
        )

        findings = analyze_source(
            "samples/after.py",
            source,
            changed_line_numbers={2},
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "PY001")
        self.assertEqual(findings[0].line_number, 2)
        self.assertEqual(findings[0].severity, "warning")

    def test_ignores_zero_index_on_an_unchanged_line(self):
        source = (
            "def get_first(users):\n"
            "    return users[0]\n"
        )

        findings = analyze_source(
            "samples/after.py",
            source,
            changed_line_numbers={1},
        )

        self.assertEqual(findings, [])

    def test_ignores_nonzero_index(self):
        source = (
            "def get_second(users):\n"
            "    return users[1]\n"
        )

        findings = analyze_source(
            "samples/after.py",
            source,
            changed_line_numbers={2},
        )

        self.assertEqual(findings, [])

    def test_flags_mutable_list_default_on_changed_line(self):
        source = (
            "def collect(item, items=[]):\n"
            "    items.append(item)\n"
            "    return items\n"
        )

        findings = analyze_source(
            "example.py",
            source,
            changed_line_numbers={1},
        )

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY002"],
        )


if __name__ == "__main__":
    unittest.main()