from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreWeights:
    technical_skills: float = 0.50
    experience_match: float = 0.25
    soft_skills: float = 0.15
    education_match: float = 0.10


DEFAULT_WEIGHTS = ScoreWeights()
