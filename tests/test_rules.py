import unittest

from review_assistant.rules import analyze_source


class AnalyzeSourceTests(unittest.TestCase):
    def test_flags_zero_index_on_a_changed_line(self):
        source = "def get_first(users):\n    return users[0]\n"
        findings = analyze_source("example.py", source, {2})

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "PY001")
        self.assertEqual(findings[0].line_number, 2)

    def test_ignores_zero_index_on_an_unchanged_line(self):
        source = "def get_first(users):\n    return users[0]\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(findings, [])

    def test_ignores_nonzero_index(self):
        source = "def get_second(users):\n    return users[1]\n"
        findings = analyze_source("example.py", source, {2})

        self.assertEqual(findings, [])

    def test_flags_mutable_list_default_on_changed_line(self):
        source = (
            "def collect(item, items=[]):\n"
            "    items.append(item)\n"
            "    return items\n"
        )
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY002"],
        )

    def test_flags_bare_except_on_changed_line(self):
        source = (
            "def load_data():\n"
            "    try:\n"
            "        return read_data()\n"
            "    except:\n"
            "        return None\n"
        )
        findings = analyze_source("example.py", source, {4})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY003"],
        )
        self.assertEqual(findings[0].line_number, 4)


if __name__ == "__main__":
    unittest.main()