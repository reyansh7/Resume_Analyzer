from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.config.scoring_config import DEFAULT_WEIGHTS
from app.services.embedding_service import EmbeddingService


EDUCATION_KEYWORDS = ["b.tech", "bachelor", "master", "m.tech", "phd", "university", "degree"]
EXPERIENCE_KEYWORDS = ["years", "experience", "engineer", "intern", "worked", "delivered", "built"]


@dataclass
class ScoreBreakdown:
    overall_score: float
    confidence: float
    breakdown: Dict[str, float]
    explanations: Dict[str, str]


class WeightedScorer:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()

    def _safe_similarity(self, a: str, b: str) -> float:
        try:
            embeddings = self.embedding_service.encode([a, b])
            sim = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])
            if np.isnan(sim):
                return 0.0
            return max(0.0, min(1.0, sim))
        except Exception:
            return 0.0

    def _technical_score(self, resume_text: str, role_skills: List[str], extracted_skills: List[str]) -> tuple[float, list[float]]:
        if not role_skills:
            return 0.0, []

        extracted = extracted_skills or []
        extracted_set = {skill.lower() for skill in extracted}
        coverage = sum(1 for skill in role_skills if skill.lower() in extracted_set) / max(len(role_skills), 1)

        # Embedding similarity distribution across role skills for confidence signal.
        sims: list[float] = []
        for role_skill in role_skills:
            if not extracted:
                sims.append(0.0)
                continue
            candidates = [self._safe_similarity(role_skill, extracted_skill) for extracted_skill in extracted]
            sims.append(max(candidates) if candidates else 0.0)

        semantic_fit = float(np.mean(sims)) if sims else 0.0
        score = (0.55 * coverage + 0.45 * semantic_fit) * 100
        return max(0.0, min(100.0, score)), sims

    def _experience_score(self, resume_text: str) -> float:
        lowered = resume_text.lower()
        hits = sum(1 for token in EXPERIENCE_KEYWORDS if token in lowered)
        quant_hits = len(list(filter(None, [part for part in lowered.split() if any(ch.isdigit() for ch in part)])))
        raw = min(1.0, (hits / len(EXPERIENCE_KEYWORDS)) + min(quant_hits, 8) * 0.04)
        return round(max(0.0, min(100.0, raw * 100)), 2)

    def _soft_skill_score(self, soft_skills: List[str]) -> float:
        return round(max(0.0, min(100.0, (len(soft_skills) / 6) * 100)), 2)

    def _education_score(self, resume_text: str) -> float:
        lowered = resume_text.lower()
        hits = sum(1 for token in EDUCATION_KEYWORDS if token in lowered)
        return round(max(0.0, min(100.0, (hits / len(EDUCATION_KEYWORDS)) * 100)), 2)

    def score(self, resume_text: str, role_skills: List[str], extracted_skills: List[str], soft_skills: List[str]) -> ScoreBreakdown:
        technical, similarity_distribution = self._technical_score(resume_text, role_skills, extracted_skills)
        experience = self._experience_score(resume_text)
        soft = self._soft_skill_score(soft_skills)
        education = self._education_score(resume_text)

        weighted_overall = (
            technical * DEFAULT_WEIGHTS.technical_skills
            + experience * DEFAULT_WEIGHTS.experience_match
            + soft * DEFAULT_WEIGHTS.soft_skills
            + education * DEFAULT_WEIGHTS.education_match
        )

        sims = np.array(similarity_distribution) if similarity_distribution else np.array([0.0])
        similarity_mean = float(np.mean(sims))
        similarity_std = float(np.std(sims))
        confidence = max(0.5, min(0.99, similarity_mean - (0.5 * similarity_std) + 0.35))

        explanations = {
            "technical_skills": (
                f"Technical score blends role-skill coverage and embedding similarity. Coverage={round(technical, 1)} on a 0-100 scale."
            ),
            "soft_skills": (
                f"Soft-skills score is inferred from leadership, collaboration, communication and impact language density."
            ),
            "experience_match": (
                "Experience score uses action verbs, measurable achievements and professional context cues."
            ),
            "education_match": (
                "Education score checks degree/academic markers and formal qualification evidence in the resume text."
            ),
        }

        return ScoreBreakdown(
            overall_score=round(max(0.0, min(100.0, weighted_overall)), 2),
            confidence=round(confidence, 2),
            breakdown={
                "technical_skills": round(technical, 2),
                "soft_skills": round(soft, 2),
                "experience_match": round(experience, 2),
                "education_match": round(education, 2),
            },
            explanations=explanations,
        )
