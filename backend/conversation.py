import os
from typing import Tuple


class ConversationSimulator:
    POSITIVE_CUES = [
        "actively exploring",
        "interested in hearing more",
        "open to new opportunities",
        "would love to learn more",
        "happy to chat",
    ]
    NEUTRAL_CUES = [
        "selective",
        "curious",
        "depends on the role",
        "open if the fit is strong",
        "willing to discuss",
    ]
    NEGATIVE_CUES = [
        "not actively looking",
        "focused on my current role",
        "not exploring right now",
        "would prefer to stay put",
        "not interested at the moment",
    ]

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")

    def simulate(self, candidate: dict, jd_data: dict) -> dict:
        if self.api_key:
            simulated = self._try_gemini_simulation(candidate, jd_data)
            if simulated:
                return simulated
        return self._rule_based_simulation(candidate, jd_data)

    def _try_gemini_simulation(self, candidate: dict, jd_data: dict) -> dict | None:
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                "You are simulating a concise recruiter-candidate exchange.\n"
                "Recruiter asks: Are you open to new opportunities?\n"
                "Given the candidate profile and target role, respond with JSON keys "
                "candidate_response, interest_score, explanation.\n\n"
                f"Candidate: {candidate}\n"
                f"Target role: {jd_data}"
            )
            response = model.generate_content(prompt)
            import json
            import re

            raw_text = re.sub(r"^```json|```$", "", response.text.strip()).strip()
            data = json.loads(raw_text)
            return {
                "recruiter_message": "Are you open to new opportunities?",
                "candidate_response": data["candidate_response"],
                "interest_score": float(data["interest_score"]),
                "interest_explanation": data["explanation"],
            }
        except Exception:
            return None

    def _rule_based_simulation(self, candidate: dict, jd_data: dict) -> dict:
        candidate_years = self._extract_years(candidate.get("experience", ""))
        jd_role = jd_data.get("role", "")
        skill_overlap = len(
            {
                skill.strip().lower()
                for skill in candidate.get("skills", "").split(",")
                if skill.strip()
            }.intersection({skill.lower() for skill in jd_data.get("skills", [])})
        )

        response_tone, score = self._interest_bucket(
            candidate_years=candidate_years,
            role_match=str(candidate.get("role", "")).lower() == jd_role.lower() if jd_role else False,
            skill_overlap=skill_overlap,
        )

        if response_tone == "positive":
            response = (
                f"Yes, I'm actively exploring roles where I can use my background in {candidate.get('role')} "
                f"and the opportunity sounds aligned with my experience."
            )
            explanation = "Candidate signals clear availability and sees strong alignment with the opportunity."
        elif response_tone == "neutral":
            response = (
                "I'm open to a conversation if the scope, team, and growth path are a strong fit."
            )
            explanation = "Candidate sounds interested but cautious, suggesting moderate intent rather than urgency."
        else:
            response = (
                "Thanks for reaching out. I'm focused on my current role right now, though I could revisit later."
            )
            explanation = "Candidate response shows low current intent to engage, which lowers the interest score."

        return {
            "recruiter_message": "Are you open to new opportunities?",
            "candidate_response": response,
            "interest_score": score,
            "interest_explanation": explanation,
        }

    @staticmethod
    def _extract_years(experience_text: str) -> int:
        digits = "".join(character for character in str(experience_text) if character.isdigit())
        return int(digits) if digits else 0

    @staticmethod
    def _interest_bucket(candidate_years: int, role_match: bool, skill_overlap: int) -> Tuple[str, float]:
        base_score = 40.0
        if role_match:
            base_score += 20.0
        if skill_overlap >= 4:
            base_score += 20.0
        elif skill_overlap >= 2:
            base_score += 10.0
        if 3 <= candidate_years <= 8:
            base_score += 10.0
        elif candidate_years > 8:
            base_score -= 5.0

        if base_score >= 75:
            return "positive", min(95.0, base_score)
        if base_score >= 55:
            return "neutral", base_score
        return "negative", max(20.0, base_score)
