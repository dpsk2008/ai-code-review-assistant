
import ast
import unittest
from unittest.mock import patch

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

    def test_ignores_zero_index_with_matching_guard(self):
        source = (
            "def get_first(items):\n"
            "    if items:\n"
            "        return items[0]\n"
            "    return None\n"
        )
        findings = analyze_source("example.py", source, {3})

        self.assertEqual(findings, [])

    def test_flags_zero_index_with_different_guard(self):
        source = (
            "def get_first(items, other):\n"
            "    if items:\n"
            "        return other[0]\n"
        )
        findings = analyze_source("example.py", source, {3})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY001"],
        )

    def test_flags_zero_index_in_else_branch(self):
        source = (
            "def get_first(items):\n"
            "    if items:\n"
            "        return None\n"
            "    else:\n"
            "        return items[0]\n"
        )
        findings = analyze_source("example.py", source, {5})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY001"],
        )

    def test_flags_zero_index_with_negated_guard(self):
        source = (
            "def get_first(items):\n"
            "    if not items:\n"
            "        return items[0]\n"
        )
        findings = analyze_source("example.py", source, {3})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY001"],
        )

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

    def test_flags_comparison_to_false(self):
        source = "if active == False:\n    pass\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY007"],
        )

    def test_boolean_warning_explains_type_requirement(self):
        source = "if active == True:\n    pass\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(len(findings), 1)
        self.assertIn(
            "guaranteed to be boolean",
            findings[0].recommendation,
        )

    def test_ignores_boolean_comparison_on_unchanged_line(self):
        source = "if active == True:\n    pass\n"
        findings = analyze_source("example.py", source, {2})

        self.assertEqual(findings, [])

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

    def test_duplicate_keys_with_different_values(self):
        source = "data = {'name': 'Alice', 'age': 25}\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(findings, [])

    def test_duplicate_numeric_dictionary_keys(self):
        source = "data = {1: 'first', 1: 'second'}\n"
        findings = analyze_source("example.py", source, {1})

        self.assertEqual(
            [finding.rule_id for finding in findings],
            ["PY008"],
        )

    def test_unhashable_constant_does_not_crash_analysis(self):
        tree = ast.parse("data = {'key': 1}\n")
        dictionary = tree.body[0].value

        dictionary.keys[0] = ast.copy_location(
            ast.Constant(value=["unhashable"]),
            dictionary.keys[0],
        )

        with patch(
            "review_assistant.rules.ast.parse",
            return_value=tree,
        ):
            findings = analyze_source("example.py", "", {1})

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
