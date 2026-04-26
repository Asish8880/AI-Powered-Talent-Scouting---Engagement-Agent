from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Talent Scouting Agent",
    page_icon=":mag:",
    layout="wide",
)


def rank_candidates(
    jd_text: str,
    top_k: int,
    match_weight: float,
    interest_weight: float,
) -> Dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/rank-candidates",
        json={
            "jd_text": jd_text,
            "top_k": top_k,
            "match_weight": match_weight,
            "interest_weight": interest_weight,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def render_candidate_card(result: Dict[str, Any], rank: int) -> None:
    candidate = result["candidate"]
    scores_col, profile_col = st.columns([1, 2], vertical_alignment="top")

    with scores_col:
        st.metric("Final Score", f"{result['final_score']:.1f}")
        st.metric("Match Score", f"{result['match_score']:.1f}")
        st.metric("Interest Score", f"{result['interest_score']:.1f}")

    with profile_col:
        st.subheader(f"{rank}. {candidate['name']} - {candidate['role']}")
        st.caption(f"Experience: {candidate['experience']}")
        st.write(candidate["bio"])
        st.write(f"Skills: {candidate['skills']}")

        overlap = ", ".join(result.get("skill_overlap", [])) or "No direct overlaps detected"
        missing = ", ".join(result.get("missing_skills", [])) or "No notable gaps"
        st.write(f"Matched skills: {overlap}")
        st.write(f"Missing skills: {missing}")

        explanation = result["explanation"]
        st.info(explanation["match"])
        st.warning(explanation["why_not_selected"])
        st.success(explanation["interest"])

        with st.expander("Simulated chat preview", expanded=False):
            conversation = result["conversation"]
            st.markdown(f"**Recruiter:** {conversation['recruiter_message']}")
            st.markdown(f"**Candidate:** {conversation['candidate_response']}")


st.title("AI-Powered Talent Scouting & Engagement Agent")
st.write(
    "Paste a job description, parse it into requirements, and generate a ranked shortlist with explainable scores."
)

with st.sidebar:
    st.header("Scoring Controls")
    top_k = st.slider("Candidates to shortlist", min_value=3, max_value=20, value=8)
    match_weight = st.slider("Match weight", min_value=0.1, max_value=0.9, value=0.7, step=0.1)
    interest_weight = st.slider(
        "Interest weight",
        min_value=0.1,
        max_value=0.9,
        value=max(0.1, round(1.0 - match_weight, 1)),
        step=0.1,
    )
    st.caption("Weights are normalized by the backend before final scoring.")

default_jd = """We are hiring a Senior AI Engineer to build LLM-powered recruiting workflows.
The ideal candidate has 4+ years of experience in Python, FastAPI, machine learning,
prompt engineering, Docker, AWS, and REST APIs. Experience with RAG, evaluation,
and stakeholder communication is a plus."""

jd_text = st.text_area("Job Description", value=default_jd, height=220)

if st.button("Find Candidates", type="primary", use_container_width=True):
    if len(jd_text.strip()) < 20:
        st.error("Please provide a fuller job description so the parser has enough signal.")
    else:
        with st.spinner("Ranking candidates..."):
            try:
                result = rank_candidates(
                    jd_text=jd_text,
                    top_k=top_k,
                    match_weight=match_weight,
                    interest_weight=interest_weight,
                )
            except requests.RequestException as error:
                st.error(
                    f"Could not reach the backend at {API_BASE_URL}. Start FastAPI first. Details: {error}"
                )
            else:
                parsed = result["parsed_jd"]
                st.subheader("Parsed JD")
                st.json(parsed)

                st.subheader("Ranked Shortlist")
                for index, candidate_result in enumerate(result["results"], start=1):
                    with st.container(border=True):
                        render_candidate_card(candidate_result, rank=index)
