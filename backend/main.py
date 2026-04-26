from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

try:
    from conversation import ConversationSimulator
    from jd_parser import JDParser
    from matcher import CandidateMatcher
    from scorer import CandidateScorer
except ImportError:
    from .conversation import ConversationSimulator
    from .jd_parser import JDParser
    from .matcher import CandidateMatcher
    from .scorer import CandidateScorer


app = FastAPI(
    title="AI-Powered Talent Scouting & Engagement Agent",
    description="Parses job descriptions, ranks candidates, and simulates recruiter outreach.",
    version="1.0.0",
)

jd_parser = JDParser()
matcher = CandidateMatcher()
conversation_simulator = ConversationSimulator()


class JDInput(BaseModel):
    jd_text: str = Field(..., min_length=20)


class CandidateInput(BaseModel):
    name: str
    skills: str
    experience: str
    role: str
    bio: str


class RankRequest(BaseModel):
    jd_text: str = Field(..., min_length=20)
    top_k: int = Field(default=10, ge=1, le=25)
    match_weight: float = Field(default=0.7, gt=0.0)
    interest_weight: float = Field(default=0.3, gt=0.0)


class ConversationRequest(BaseModel):
    jd_text: str = Field(..., min_length=20)
    candidate: CandidateInput


@app.get("/")
def root() -> dict:
    return {
        "message": "Talent scouting agent backend is running.",
        "dataset": str(Path(__file__).resolve().parents[1] / "data" / "candidates.csv"),
    }


@app.post("/parse-jd")
def parse_jd(payload: JDInput) -> dict:
    parsed = jd_parser.parse(payload.jd_text)
    return {"parsed_jd": parsed}


@app.post("/match-candidates")
def match_candidates(payload: RankRequest) -> dict:
    parsed_jd = jd_parser.parse(payload.jd_text)
    matches = matcher.match_candidates(parsed_jd, top_k=payload.top_k)
    return {
        "parsed_jd": parsed_jd,
        "matches": [
            {
                "candidate": match.candidate,
                "match_score": match.match_score,
                "semantic_score": match.semantic_score,
                "experience_alignment": match.experience_alignment,
                "skill_overlap": match.skill_overlap,
                "missing_skills": match.missing_skills,
                "explanation": match.explanation,
                "why_not_selected": match.why_not_selected,
            }
            for match in matches
        ],
    }


@app.post("/simulate-conversation")
def simulate_conversation(payload: ConversationRequest) -> dict:
    parsed_jd = jd_parser.parse(payload.jd_text)
    simulation = conversation_simulator.simulate(
        candidate=payload.candidate.model_dump(),
        jd_data=parsed_jd,
    )
    return {"parsed_jd": parsed_jd, "conversation": simulation}


@app.post("/rank-candidates")
def rank_candidates(payload: RankRequest) -> dict:
    parsed_jd = jd_parser.parse(payload.jd_text)
    scorer = CandidateScorer(
        match_weight=payload.match_weight,
        interest_weight=payload.interest_weight,
    )
    matches = matcher.match_candidates(parsed_jd, top_k=payload.top_k)

    ranked_results: List[dict] = []
    for match in matches:
        conversation = conversation_simulator.simulate(
            candidate=match.candidate,
            jd_data=parsed_jd,
        )
        final_score = scorer.score(
            match_score=match.match_score,
            interest_score=conversation["interest_score"],
        )
        ranked_results.append(
            {
                "candidate": match.candidate,
                "match_score": match.match_score,
                "interest_score": conversation["interest_score"],
                "final_score": final_score,
                "explanation": {
                    "match": match.explanation,
                    "interest": conversation["interest_explanation"],
                    "why_not_selected": match.why_not_selected,
                },
                "conversation": conversation,
                "skill_overlap": match.skill_overlap,
                "missing_skills": match.missing_skills,
            }
        )

    ranked_results.sort(key=lambda item: item["final_score"], reverse=True)
    return {
        "parsed_jd": parsed_jd,
        "weights": scorer.breakdown(),
        "results": ranked_results,
    }
