
import unittest

from fastapi.testclient import TestClient

from api import app


class ReviewAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_home_page(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Code Review Assistant", response.text)

    def test_detects_zero_index(self):
        code = "def get_first(items):\n    return items[0]"

        response = self.client.post("/review", json={"code": code})

        self.assertEqual(response.status_code, 200)

        findings = response.json()["findings"]

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "PY001")
        self.assertEqual(findings[0]["line_number"], 2)

    def test_detects_mutable_default(self):
        code = "def add_item(item, items=[]):\n    items.append(item)"

        response = self.client.post("/review", json={"code": code})

        self.assertEqual(response.status_code, 200)

        findings = response.json()["findings"]

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "PY002")

    def test_detects_bare_except(self):
        code = "try:\n    print('Hello')\nexcept:\n    pass"

        response = self.client.post("/review", json={"code": code})

        self.assertEqual(response.status_code, 200)

        findings = response.json()["findings"]

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule_id"], "PY003")

    def test_code_without_findings(self):
        code = "print('Hello World')"

        response = self.client.post("/review", json={"code": code})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["findings"], [])

    def test_invalid_python_syntax(self):
        code = "def broken_function("

        response = self.client.post("/review", json={"code": code})

        self.assertEqual(response.status_code, 422)
        self.assertIn("Invalid Python syntax", response.json()["detail"])

    def test_missing_code(self):
        response = self.client.post("/review", json={})

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
