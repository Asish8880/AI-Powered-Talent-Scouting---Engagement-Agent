import json
import os
import re
from typing import List


COMMON_SKILLS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Next.js",
    "Node.js",
    "FastAPI",
    "Django",
    "Flask",
    "SQL",
    "PostgreSQL",
    "MongoDB",
    "Docker",
    "Kubernetes",
    "AWS",
    "GCP",
    "Azure",
    "Machine Learning",
    "scikit-learn",
    "PyTorch",
    "TensorFlow",
    "LLMs",
    "Prompt Engineering",
    "RAG",
    "MLOps",
    "REST APIs",
    "System Design",
    "CI/CD",
    "Terraform",
    "Linux",
    "dbt",
    "Airflow",
]

ROLE_HINTS = [
    "AI Engineer",
    "ML Engineer",
    "Data Scientist",
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "DevOps Engineer",
    "Analytics Engineer",
    "Product Manager",
    "Recruiter",
]


class JDParser:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")

    def parse(self, jd_text: str) -> dict:
        if self.api_key:
            parsed = self._try_gemini_parse(jd_text)
            if parsed:
                return parsed
        return self._mock_parse(jd_text)

    def _try_gemini_parse(self, jd_text: str) -> dict | None:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "Extract structured hiring requirements from the job description. "
                "Return only valid JSON with keys: skills, experience, role, keywords. "
                "Use concise strings and arrays.\n\n"
                f"Job Description:\n{jd_text}"
            )
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            raw_text = re.sub(r"^```json|```$", "", raw_text).strip()
            data = json.loads(raw_text)
            return {
                "skills": data.get("skills", []),
                "experience": data.get("experience", ""),
                "role": data.get("role", ""),
                "keywords": data.get("keywords", []),
            }
        except Exception:
            return None

    def _mock_parse(self, jd_text: str) -> dict:
        text = jd_text.strip()
        lower_text = text.lower()

        detected_skills = [
            skill for skill in COMMON_SKILLS if skill.lower() in lower_text
        ]
        role = next((role for role in ROLE_HINTS if role.lower() in lower_text), "")
        experience = self._extract_experience(text)
        keywords = self._extract_keywords(text, detected_skills, role)

        return {
            "skills": detected_skills,
            "experience": experience,
            "role": role,
            "keywords": keywords[:12],
        }

    @staticmethod
    def _extract_experience(text: str) -> str:
        pattern = re.search(
            r"(\d+\+?\s*(?:to\s*\d+\s*)?(?:years?|yrs?))(?:\s+of)?\s+experience",
            text,
            re.IGNORECASE,
        )
        return pattern.group(1) if pattern else ""

    @staticmethod
    def _extract_keywords(text: str, skills: List[str], role: str) -> List[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
        words = [word.lower() for word in cleaned.split() if len(word) > 3]

        stop_words = {
            "with",
            "that",
            "have",
            "from",
            "this",
            "will",
            "your",
            "about",
            "years",
            "experience",
            "role",
            "team",
            "work",
            "using",
            "build",
            "strong",
        }

        ranked = []
        seen = set()
        seed_terms = skills + ([role] if role else [])

        for item in seed_terms + words:
            normalized = item.lower()
            if normalized in seen or normalized in stop_words:
                continue
            seen.add(normalized)
            ranked.append(item)

        return ranked
