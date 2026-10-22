import unittest

from review_assistant.diff_parser import AddedLine, parse_added_lines


class ParseAddedLinesTests(unittest.TestCase):
    def test_tracks_added_lines_after_a_deletion(self):
        diff = (
            "diff --git a/example.py b/example.py\n"
            "--- a/example.py\n"
            "+++ b/example.py\n"
            "@@ -1,3 +1,4 @@\n"
            " def greet():\n"
            '-    return "hi"\n'
            '+    message = "hello"\n'
            "+    return message\n"
        )

        self.assertEqual(
            parse_added_lines(diff),
            [
                AddedLine("example.py", 2, '    message = "hello"'),
                AddedLine("example.py", 3, "    return message"),
            ],
        )

    def test_tracks_line_numbers_across_hunks(self):
        diff = (
            "--- a/example.py\n"
            "+++ b/example.py\n"
            "@@ -1 +1 @@\n"
            " first_line()\n"
            "@@ -9 +9,2 @@\n"
            " ninth_line()\n"
            "+tenth_line()\n"
        )

        self.assertEqual(
            parse_added_lines(diff),
            [AddedLine("example.py", 10, "tenth_line()")],
        )

    def test_handles_a_new_file(self):
        diff = (
            "--- /dev/null\n"
            "+++ b/new_file.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+first_line()\n"
            "+second_line()\n"
        )

        self.assertEqual(
            parse_added_lines(diff),
            [
                AddedLine("new_file.py", 1, "first_line()"),
                AddedLine("new_file.py", 2, "second_line()"),
            ],
        )


if __name__ == "__main__":
    unittest.main()