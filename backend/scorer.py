from typing import Dict


class CandidateScorer:
    def __init__(self, match_weight: float = 0.7, interest_weight: float = 0.3) -> None:
        total = match_weight + interest_weight
        self.match_weight = match_weight / total
        self.interest_weight = interest_weight / total

    def score(self, match_score: float, interest_score: float) -> float:
        final_score = (
            self.match_weight * match_score + self.interest_weight * interest_score
        )
        return round(final_score, 2)

    def breakdown(self) -> Dict[str, float]:
        return {
            "match_weight": round(self.match_weight, 2),
            "interest_weight": round(self.interest_weight, 2),
        }
