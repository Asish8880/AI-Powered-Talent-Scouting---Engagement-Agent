import csv
from pathlib import Path


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "candidates.csv"


SKILL_GROUPS = {
    "Backend Engineer": [
        "Python",
        "FastAPI",
        "Django",
        "REST APIs",
        "PostgreSQL",
        "Docker",
        "AWS",
        "Microservices",
        "Redis",
        "Unit Testing",
    ],
    "Frontend Engineer": [
        "JavaScript",
        "TypeScript",
        "React",
        "Next.js",
        "CSS",
        "HTML",
        "Redux",
        "UI Design",
        "Testing Library",
        "Responsive Design",
    ],
    "Full Stack Engineer": [
        "Python",
        "JavaScript",
        "React",
        "FastAPI",
        "Node.js",
        "SQL",
        "Docker",
        "AWS",
        "System Design",
        "CI/CD",
    ],
    "Data Scientist": [
        "Python",
        "Pandas",
        "NumPy",
        "scikit-learn",
        "Machine Learning",
        "Statistics",
        "SQL",
        "Data Visualization",
        "Experimentation",
        "Feature Engineering",
    ],
    "ML Engineer": [
        "Python",
        "PyTorch",
        "TensorFlow",
        "MLOps",
        "Machine Learning",
        "Docker",
        "AWS",
        "Model Serving",
        "Feature Stores",
        "scikit-learn",
    ],
    "DevOps Engineer": [
        "AWS",
        "Docker",
        "Kubernetes",
        "Terraform",
        "CI/CD",
        "Linux",
        "Monitoring",
        "Networking",
        "Python",
        "Shell Scripting",
    ],
    "Product Manager": [
        "Roadmapping",
        "Stakeholder Management",
        "User Research",
        "Analytics",
        "Agile",
        "Prioritization",
        "Product Strategy",
        "A/B Testing",
        "Communication",
        "Go-to-Market",
    ],
    "Recruiter": [
        "Talent Sourcing",
        "Screening",
        "Stakeholder Management",
        "ATS",
        "Candidate Experience",
        "Interview Coordination",
        "Negotiation",
        "Employer Branding",
        "Communication",
        "Pipeline Management",
    ],
    "AI Engineer": [
        "Python",
        "LLMs",
        "Prompt Engineering",
        "Vector Databases",
        "FastAPI",
        "RAG",
        "LangChain",
        "MLOps",
        "Docker",
        "Evaluation",
    ],
    "Analytics Engineer": [
        "SQL",
        "dbt",
        "Python",
        "Data Modeling",
        "Looker",
        "ETL",
        "Airflow",
        "Data Warehousing",
        "Business Metrics",
        "Documentation",
    ],
}

FIRST_NAMES = [
    "Aarav",
    "Aisha",
    "Noah",
    "Maya",
    "Rohan",
    "Zara",
    "Liam",
    "Anika",
    "Ethan",
    "Priya",
    "Ishaan",
    "Sophia",
    "Kabir",
    "Meera",
    "Arjun",
    "Nina",
    "Vihaan",
    "Leah",
    "Reyansh",
    "Sara",
]

LAST_NAMES = [
    "Sharma",
    "Patel",
    "Khan",
    "Singh",
    "Brown",
    "Garcia",
    "Lee",
    "Martin",
    "Davis",
    "Wilson",
    "Nguyen",
    "Clark",
    "Hall",
    "Allen",
    "Wright",
]

SUMMARIES = {
    "Backend Engineer": "Builds backend services with an eye for API quality, data modeling, and reliability.",
    "Frontend Engineer": "Creates polished user experiences with strong component thinking and product empathy.",
    "Full Stack Engineer": "Moves comfortably across frontend and backend, shipping end-to-end product features.",
    "Data Scientist": "Turns messy data into models and insights that support product and business decisions.",
    "ML Engineer": "Productionizes machine learning systems and keeps models dependable after launch.",
    "DevOps Engineer": "Automates cloud infrastructure and deployment workflows with a reliability mindset.",
    "Product Manager": "Shapes product direction with structured problem solving and strong stakeholder alignment.",
    "Recruiter": "Builds talent pipelines and keeps candidate experience organized, responsive, and thoughtful.",
    "AI Engineer": "Builds LLM and machine learning features with a focus on evaluation and practical delivery.",
    "Analytics Engineer": "Designs trustworthy data models and pipelines for reporting and decision support.",
}


def build_candidate(index: int, role: str) -> dict:
    first = FIRST_NAMES[index % len(FIRST_NAMES)]
    last = LAST_NAMES[(index * 3) % len(LAST_NAMES)]
    experience_years = 1 + (index % 10)
    skills = SKILL_GROUPS[role][:]

    rotating_skill = [
        "Leadership",
        "Communication",
        "Problem Solving",
        "Mentoring",
        "Scrum",
        "System Design",
        "Customer Focus",
    ][index % 7]
    if rotating_skill not in skills:
        skills = skills[:7] + [rotating_skill] + skills[7:9]

    return {
        "name": f"{first} {last}",
        "skills": ", ".join(skills[:10]),
        "experience": f"{experience_years} years",
        "role": role,
        "bio": (
            f"{SUMMARIES[role]} Has {experience_years} years of experience and has worked on "
            f"{'scaling teams and platforms' if experience_years > 6 else 'fast-moving product initiatives'}."
        ),
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    roles = list(SKILL_GROUPS.keys())

    for index in range(100):
        role = roles[index % len(roles)]
        rows.append(build_candidate(index, role))

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["name", "skills", "experience", "role", "bio"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} candidates to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
