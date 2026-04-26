# AI-Powered Talent Scouting & Engagement Agent

This project is a system that parses a job description, finds matching candidates from a CSV dataset, simulates recruiter outreach, and returns a ranked shortlist with explainable scoring.

## What it does

1. Accepts a raw job description
2. Parses it into structured hiring requirements
3. Matches candidates from a 100-profile dataset
4. Simulates a recruiter asking whether each candidate is open to opportunities
5. Scores each candidate on:
   - Match Score
   - Interest Score
   - Final Score = `(0.7 * Match Score) + (0.3 * Interest Score)` by default
6. Explains both why a candidate matched and why they may not have ranked higher

## Architecture

### Backend: FastAPI

- [backend/main.py](backend/main.py) exposes API endpoints
- [backend/jd_parser.py](backend/jd_parser.py) parses JDs into structured JSON
- [backend/matcher.py](backend/matcher.py) computes similarity and match scores
- [backend/conversation.py](backend/conversation.py) simulates recruiter-candidate conversations
- [backend/scorer.py](backend/scorer.py) combines match and interest into a final score

### Frontend: Streamlit

- [frontend/app.py](frontend/app.py) provides a clean UI to submit a JD and inspect ranked candidates

### Data

- [data/candidates.csv](data/candidates.csv) contains 100 sample candidate profiles
- [scripts/generate_candidates.py](scripts/generate_candidates.py) regenerates the dataset

## Scoring logic

### Match Score

The matching engine combines:

- Skill overlap between JD skills and candidate skills
- Experience alignment based on requested years vs. candidate years
- Semantic similarity using TF-IDF + cosine similarity across role, skills, and bio
- Small role-title bonus when the role matches exactly

The score is normalized to a `0-100` range.

### Interest Score

The recruiter asks:

`Are you open to new opportunities?`

Interest is inferred from a generated or rule-based response. The score depends on:

- Role alignment
- Skill overlap
- Candidate seniority
- Overall conversation tone

### Final Score

Default formula:

`Final Score = (0.7 * Match Score) + (0.3 * Interest Score)`

The backend uses default scoring weights and normalizes them before calculating final scores.

## API endpoints

Run the backend from the `backend` directory:

- `POST /parse-jd`
- `POST /match-candidates`
- `POST /simulate-conversation`
- `POST /rank-candidates`

Example request for `/rank-candidates`:

```json
{
  "jd_text": "We are hiring a Senior AI Engineer with 4+ years of experience in Python, FastAPI, machine learning, AWS, Docker, REST APIs, and prompt engineering.",
  "top_k": 5,
  "match_weight": 0.7,
  "interest_weight": 0.3
}
```

Example response shape:

```json
{
  "parsed_jd": {
    "skills": ["Python", "FastAPI", "AWS", "Machine Learning", "Docker"],
    "experience": "4+ years",
    "role": "AI Engineer",
    "keywords": ["Python", "FastAPI", "AWS", "Machine Learning", "prompt", "engineering"]
  },
  "weights": {
    "match_weight": 0.7,
    "interest_weight": 0.3
  },
  "results": [
    {
      "candidate": {
        "name": "Example Candidate",
        "skills": "Python, FastAPI, AWS",
        "experience": "6 years",
        "role": "AI Engineer",
        "bio": "..."
      },
      "match_score": 88.4,
      "interest_score": 82.0,
      "final_score": 86.48,
      "explanation": {
        "match": "...",
        "interest": "...",
        "why_not_selected": "..."
      },
      "conversation": {
        "recruiter_message": "Are you open to new opportunities?",
        "candidate_response": "Yes, I'm actively exploring...",
        "interest_score": 82.0,
        "interest_explanation": "..."
      }
    }
  ]
}
```

## Local setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate the sample dataset if needed:

```bash
python scripts/generate_candidates.py
```

Start the FastAPI backend:

```bash
cd backend
uvicorn main:app --reload
```

Start the Streamlit frontend in a second terminal:

```bash
cd frontend
streamlit run app.py
```

By default, the Streamlit app talks to `http://127.0.0.1:8000`. You can override this with:

```bash
export API_BASE_URL=http://127.0.0.1:8000
```

On Windows PowerShell:

```powershell
$env:API_BASE_URL="http://127.0.0.1:8000"
```
```

## Sample demo input

```text
We are hiring a Senior AI Engineer to build LLM-powered recruiting workflows.
The ideal candidate has 4+ years of experience in Python, FastAPI, machine learning,
prompt engineering, Docker, AWS, and REST APIs. Experience with RAG, evaluation,
and stakeholder communication is a plus.
```
