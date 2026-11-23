
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

    def test_flags_none_equality_comparison(self):
        source = "if value == None:\n    pass\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY004"],
        )

    def test_flags_none_inequality_comparison(self):
        source = "if value != None:\n    pass\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY004"],
        )

    def test_ignores_none_identity_comparison(self):
        source = "if value is None:\n    pass\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(findings, [])

    def test_flags_eval_call(self):
        source = "result = eval(expression)\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY005"],
        )

    def test_flags_exec_call(self):
        source = "exec(expression)\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY006"],
        )

    def test_ignores_eval_on_unchanged_line(self):
        source = "expression = '1 + 2'\nresult = eval(expression)\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(findings, [])

    def test_flags_boolean_comparison(self):
        source = "if active == True:\n    pass\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY007"],
        )

    def test_ignores_direct_boolean_condition(self):
        source = "if active:\n    pass\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(findings, [])

    def test_flags_duplicate_dictionary_key(self):
        source = (
            "data = {\n"
            "    'name': 'Alice',\n"
            "    'name': 'Bob',\n"
            "}\n"
        )
        findings = analyze_source("example.py", source, {3})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY008"],
        )
        self.assertEqual(findings[0].line_number, 3)

    def test_ignores_unique_dictionary_keys(self):
        source = "data = {'name': 'Alice', 'age': 25}\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
