from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "candidates.csv"


@dataclass
class CandidateMatch:
    candidate: dict
    match_score: float
    skill_overlap: List[str]
    missing_skills: List[str]
    semantic_score: float
    experience_alignment: float
    explanation: str
    why_not_selected: str


class CandidateMatcher:
    def __init__(self, data_path: Path = DATA_PATH) -> None:
        self.data_path = data_path
        self.candidates = self._load_candidates()

    def _load_candidates(self) -> pd.DataFrame:
        data = pd.read_csv(self.data_path)
        data["skills_list"] = data["skills"].fillna("").apply(
            lambda value: [item.strip() for item in str(value).split(",") if item.strip()]
        )
        data["experience_years"] = data["experience"].apply(self._parse_years)
        return data

    def match_candidates(self, jd_data: dict, top_k: int = 10) -> List[CandidateMatch]:
        jd_skills = jd_data.get("skills", [])
        jd_experience = self._parse_years(jd_data.get("experience", ""))
        jd_role = jd_data.get("role", "")
        jd_keywords = jd_data.get("keywords", [])

        jd_text = " ".join(jd_skills + jd_keywords + ([jd_role] if jd_role else []))
        corpus = [jd_text] + [
            " ".join(row["skills_list"] + [row["role"], row["bio"]])
            for _, row in self.candidates.iterrows()
        ]

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus)
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

        matches: List[CandidateMatch] = []
        for index, row in self.candidates.iterrows():
            candidate_skills = row["skills_list"]
            overlap = self._ordered_intersection(jd_skills, candidate_skills)
            missing = [skill for skill in jd_skills if skill not in overlap]

            skill_score = (
                (len(overlap) / max(len(jd_skills), 1)) * 100 if jd_skills else 55.0
            )
            exp_score = self._experience_score(jd_experience, row["experience_years"])
            semantic_score = float(similarities[index] * 100)
            role_bonus = 10.0 if jd_role and jd_role.lower() == str(row["role"]).lower() else 0.0

            match_score = (
                0.4 * skill_score
                + 0.2 * exp_score
                + 0.3 * semantic_score
                + role_bonus
            )
            match_score = max(0.0, min(100.0, match_score))

            explanation = self._build_explanation(
                row=row,
                overlap=overlap,
                missing=missing,
                experience_score=exp_score,
                semantic_score=semantic_score,
                jd_experience=jd_experience,
            )
            why_not_selected = self._build_why_not_selected(
                missing=missing,
                experience_score=exp_score,
                semantic_score=semantic_score,
                role_match=bool(jd_role and jd_role.lower() == str(row["role"]).lower()),
            )

            matches.append(
                CandidateMatch(
                    candidate=row.drop(labels=["skills_list", "experience_years"]).to_dict(),
                    match_score=round(match_score, 2),
                    skill_overlap=overlap,
                    missing_skills=missing,
                    semantic_score=round(semantic_score, 2),
                    experience_alignment=round(exp_score, 2),
                    explanation=explanation,
                    why_not_selected=why_not_selected,
                )
            )

        deduplicated_matches: Dict[str, CandidateMatch] = {}
        for match in matches:
            candidate_key = self._candidate_key(match.candidate)
            existing_match = deduplicated_matches.get(candidate_key)
            if existing_match is None or match.match_score > existing_match.match_score:
                deduplicated_matches[candidate_key] = match

        unique_matches = list(deduplicated_matches.values())
        unique_matches.sort(key=lambda item: item.match_score, reverse=True)
        return unique_matches[:top_k]

    @staticmethod
    def _ordered_intersection(jd_skills: List[str], candidate_skills: List[str]) -> List[str]:
        candidate_lookup = {skill.lower(): skill for skill in candidate_skills}
        overlap = []
        for skill in jd_skills:
            if skill.lower() in candidate_lookup:
                overlap.append(candidate_lookup[skill.lower()])
        return overlap

    @staticmethod
    def _candidate_key(candidate: dict) -> str:
        fields = (
            str(candidate.get("name", "")).strip().lower(),
            str(candidate.get("role", "")).strip().lower(),
            str(candidate.get("experience", "")).strip().lower(),
            str(candidate.get("bio", "")).strip().lower(),
        )
        return "|".join(fields)

    @staticmethod
    def _parse_years(value: str) -> int:
        match = re.search(r"(\d+)", str(value))
        return int(match.group(1)) if match else 0

    @staticmethod
    def _experience_score(required_years: int, candidate_years: int) -> float:
        if required_years <= 0:
            return 70.0
        gap = candidate_years - required_years
        if gap >= 0:
            return min(100.0, 85.0 + min(gap * 3.0, 15.0))
        return max(25.0, 85.0 - abs(gap) * 18.0)

    @staticmethod
    def _build_explanation(
        row: pd.Series,
        overlap: List[str],
        missing: List[str],
        experience_score: float,
        semantic_score: float,
        jd_experience: int,
    ) -> str:
        parts = []
        if overlap:
            parts.append(f"Shared core skills: {', '.join(overlap[:5])}.")
        else:
            parts.append("Few direct skill overlaps were found, so the match leans on broader profile similarity.")

        if jd_experience:
            parts.append(
                f"Candidate has {row['experience']} compared with a target of about {jd_experience} years."
            )
        else:
            parts.append(f"Candidate brings {row['experience']} of experience.")

        parts.append(f"Profile similarity signal: {semantic_score:.1f}/100.")

        if missing:
            parts.append(f"Notable gaps: {', '.join(missing[:4])}.")
        elif experience_score > 80:
            parts.append("Experience alignment is strong for this role.")

        return " ".join(parts)

    @staticmethod
    def _build_why_not_selected(
        missing: List[str],
        experience_score: float,
        semantic_score: float,
        role_match: bool,
    ) -> str:
        reasons = []
        if missing:
            reasons.append(f"missing some requested skills such as {', '.join(missing[:3])}")
        if experience_score < 60:
            reasons.append("experience appears below the target range")
        if semantic_score < 45:
            reasons.append("overall profile language is not very close to the JD")
        if not role_match:
            reasons.append("current role title differs from the target role")
        if not reasons:
            return "No major red flags surfaced in the matching stage."
        return "Candidate was not stronger because " + "; ".join(reasons) + "."
