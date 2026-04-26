import json
import os
import re
from typing import Dict, List


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

ROLE_ALIASES: Dict[str, List[str]] = {
    "AI Engineer": [
        "ai engineer",
        "artificial intelligence engineer",
        "genai engineer",
        "llm engineer",
        "applied ai engineer",
    ],
    "ML Engineer": [
        "ml engineer",
        "machine learning engineer",
        "mlops engineer",
    ],
    "Data Scientist": [
        "data scientist",
    ],
    "Backend Engineer": [
        "backend engineer",
        "backend developer",
        "back end engineer",
        "back end developer",
        "python developer",
        "api engineer",
        "server-side engineer",
    ],
    "Frontend Engineer": [
        "frontend engineer",
        "frontend developer",
        "front end engineer",
        "front end developer",
        "ui engineer",
        "web engineer",
    ],
    "Full Stack Engineer": [
        "full stack engineer",
        "full-stack engineer",
        "full stack developer",
        "full-stack developer",
    ],
    "DevOps Engineer": [
        "devops engineer",
        "site reliability engineer",
        "sre",
        "platform engineer",
        "cloud engineer",
        "infrastructure engineer",
    ],
    "Analytics Engineer": [
        "analytics engineer",
        "data engineer",
        "bi engineer",
        "business intelligence engineer",
    ],
    "Product Manager": [
        "product manager",
        "technical product manager",
        "group product manager",
    ],
    "Recruiter": [
        "recruiter",
        "talent acquisition specialist",
        "talent partner",
        "technical recruiter",
        "sourcer",
    ],
}

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


class JDParser:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")

    def parse(self, jd_text: str) -> dict:
        fallback = self._mock_parse(jd_text)
        if self.api_key:
            parsed = self._try_gemini_parse(jd_text)
            if parsed:
                return self._merge_with_fallback(parsed, fallback)
        return fallback

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
                "skills": self._ensure_list(data.get("skills", [])),
                "experience": str(data.get("experience", "")).strip(),
                "role": str(data.get("role", "")).strip(),
                "keywords": self._ensure_list(data.get("keywords", [])),
            }
        except Exception:
            return None

    def _mock_parse(self, jd_text: str) -> dict:
        text = jd_text.strip()
        lower_text = text.lower()

        detected_skills = [
            skill for skill in COMMON_SKILLS if skill.lower() in lower_text
        ]
        role = self._extract_role(text, detected_skills)
        experience = self._extract_experience(text)
        keywords = self._extract_keywords(text, detected_skills, role)

        return {
            "skills": detected_skills,
            "experience": experience,
            "role": role,
            "keywords": keywords[:12],
        }

    def _merge_with_fallback(self, parsed: dict, fallback: dict) -> dict:
        skills = parsed.get("skills") or fallback["skills"]
        role = self._normalize_role(parsed.get("role", ""), fallback["skills"]) or fallback["role"]
        experience = self._normalize_experience(parsed.get("experience", "")) or fallback["experience"]
        keywords = parsed.get("keywords") or fallback["keywords"]

        return {
            "skills": skills,
            "experience": experience,
            "role": role,
            "keywords": keywords[:12],
        }

    def _extract_role(self, text: str, detected_skills: List[str]) -> str:
        lower_text = text.lower()

        for canonical_role, aliases in ROLE_ALIASES.items():
            if any(alias in lower_text for alias in aliases):
                return canonical_role

        title_patterns = [
            r"(?:we are hiring|we're hiring|hiring|looking for|seeking)\s+(?:an?|the)\s+([a-zA-Z/\-\s]{3,60}?)(?:\s+(?:with|to|who|for|in)\b|[\n\.,:])",
            r"(?:role|position|job title)\s*[:\-]\s*([a-zA-Z/\-\s]{3,60}?)(?:[\n\.,]|$)",
        ]

        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_role = match.group(1).strip()
                normalized_role = self._normalize_role(extracted_role, detected_skills)
                if normalized_role:
                    return normalized_role

        return self._infer_role_from_skills_and_text(detected_skills, lower_text)

    def _normalize_role(self, value: str, detected_skills: List[str]) -> str:
        cleaned = re.sub(r"\b(senior|sr|junior|jr|lead|principal|staff)\b", "", value, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:/").lower()
        if not cleaned:
            return ""

        for canonical_role, aliases in ROLE_ALIASES.items():
            if cleaned == canonical_role.lower() or cleaned in aliases:
                return canonical_role

        return self._infer_role_from_skills_and_text(detected_skills, cleaned)

    @staticmethod
    def _infer_role_from_skills_and_text(detected_skills: List[str], text: str) -> str:
        lowered_skills = {skill.lower() for skill in detected_skills}

        if any(term in text for term in ["ai", "llm", "rag", "prompt engineering", "generative ai"]):
            return "AI Engineer"
        if "machine learning" in text or "mlops" in text:
            return "ML Engineer"
        if "data scientist" in text:
            return "Data Scientist"
        if "product manager" in text:
            return "Product Manager"
        if any(term in text for term in ["recruiter", "talent acquisition", "sourcer"]):
            return "Recruiter"
        if any(term in text for term in ["devops", "site reliability", "sre", "platform engineer", "cloud engineer"]):
            return "DevOps Engineer"
        if any(term in text for term in ["analytics engineer", "data engineer", "bi engineer"]):
            return "Analytics Engineer"
        if "full stack" in text or "full-stack" in text:
            return "Full Stack Engineer"
        if any(term in text for term in ["frontend", "front end", "ui engineer", "web engineer"]):
            return "Frontend Engineer"
        if any(term in text for term in ["backend", "back end", "api engineer", "python developer"]):
            return "Backend Engineer"

        has_frontend = bool({"react", "next.js", "javascript", "typescript"} & lowered_skills)
        has_backend = bool({"python", "fastapi", "django", "flask", "node.js", "sql"} & lowered_skills)

        if has_frontend and has_backend:
            return "Full Stack Engineer"
        if has_frontend:
            return "Frontend Engineer"
        if has_backend:
            return "Backend Engineer"
        return ""

    @staticmethod
    def _extract_experience(text: str) -> str:
        normalized_text = JDParser._normalize_number_words(text)
        patterns = [
            r"(\d+\s*\+\s*(?:years?|yrs?))(?:\s+of)?\s+experience",
            r"(\d+\s*[-to]+\s*\d+\s*(?:years?|yrs?))(?:\s+of)?\s+experience",
            r"((?:at least|minimum|min\.?)\s+\d+\s*(?:years?|yrs?))(?:\s+of)?\s+experience",
            r"(\d+\s*(?:years?|yrs?))(?:\s+of)?\s+experience",
            r"experience\s+(?:of\s+)?(\d+\s*\+\s*(?:years?|yrs?))",
            r"experience\s+(?:of\s+)?(\d+\s*[-to]+\s*\d+\s*(?:years?|yrs?))",
            r"experience\s+(?:of\s+)?((?:at least|minimum|min\.?)\s+\d+\s*(?:years?|yrs?))",
            r"experience\s+(?:of\s+)?(\d+\s*(?:years?|yrs?))",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                return JDParser._normalize_experience(match.group(1))

        loose_match = re.search(
            r"(\d+\s*\+\s*(?:years?|yrs?)|\d+\s*[-to]+\s*\d+\s*(?:years?|yrs?)|(?:at least|minimum|min\.?)\s+\d+\s*(?:years?|yrs?)|\d+\s*(?:years?|yrs?))",
            normalized_text,
            re.IGNORECASE,
        )
        if loose_match:
            return JDParser._normalize_experience(loose_match.group(1))

        return ""

    @staticmethod
    def _normalize_experience(value: str) -> str:
        cleaned = str(value).strip().lower().replace("yrs", "years").replace("yr", "year")
        cleaned = cleaned.replace("–", "-").replace("—", "-")
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"(minimum|min\.?|at least)\s+(\d+)\s+years?", r"\2+ years", cleaned)
        cleaned = re.sub(r"(\d+)\s*to\s*(\d+)\s+years?", r"\1-\2 years", cleaned)
        cleaned = re.sub(r"(\d+)\s*-\s*(\d+)\s+years?", r"\1-\2 years", cleaned)
        cleaned = re.sub(r"(\d+)\s*\+\s*years?", r"\1+ years", cleaned)
        cleaned = re.sub(r"(\d+)\s+years?", r"\1 years", cleaned)
        return cleaned.strip()

    @staticmethod
    def _normalize_number_words(text: str) -> str:
        normalized = text
        for word, number in NUMBER_WORDS.items():
            normalized = re.sub(rf"\b{word}\b", str(number), normalized, flags=re.IGNORECASE)
        return normalized

    @staticmethod
    def _ensure_list(value: object) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

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
