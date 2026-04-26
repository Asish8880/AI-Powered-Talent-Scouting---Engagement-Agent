import unittest

from backend.jd_parser import JDParser


class JDParserExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = JDParser()

    def test_extracts_ai_engineer_and_plus_experience(self) -> None:
        parsed = self.parser.parse(
            "We are hiring a Senior AI Engineer with 4+ years of experience in Python, FastAPI, RAG, Docker, and AWS."
        )
        self.assertEqual(parsed["role"], "AI Engineer")
        self.assertEqual(parsed["experience"], "4+ years")

    def test_extracts_backend_role_from_developer_wording(self) -> None:
        parsed = self.parser.parse(
            "Looking for a backend developer with at least five years of experience building APIs in Python and FastAPI."
        )
        self.assertEqual(parsed["role"], "Backend Engineer")
        self.assertEqual(parsed["experience"], "5+ years")

    def test_extracts_full_stack_role_and_range_experience(self) -> None:
        parsed = self.parser.parse(
            "Role: Full Stack Developer. Required experience: 3 to 6 years. Must know React, Node.js, SQL, and Docker."
        )
        self.assertEqual(parsed["role"], "Full Stack Engineer")
        self.assertEqual(parsed["experience"], "3-6 years")

    def test_extracts_frontend_role_from_skill_signal(self) -> None:
        parsed = self.parser.parse(
            "We need someone strong in React, TypeScript, Next.js, and UI design. Experience required: 4 years."
        )
        self.assertEqual(parsed["role"], "Frontend Engineer")
        self.assertEqual(parsed["experience"], "4 years")


if __name__ == "__main__":
    unittest.main()
