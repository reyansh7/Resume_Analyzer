from dataclasses import dataclass
from typing import Dict, List

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.services.embedding_service import EmbeddingService
from app.services.nlp_service import NlpService
from app.utils.skill_dictionary import ROLE_SKILL_MAP, GENERIC_TRANSFERABLE_SKILLS, ROLE_CERTIFICATIONS


@dataclass
class AnalysisResult:
    parsed_resume: Dict[str, object]
    match_score: float
    strengths: List[str]
    skill_gaps: List[str]
    transferable_skills: List[str]
    roadmap: List[Dict[str, str]]
    certifications: List[str]


class AnalyzePipeline:
    def __init__(self) -> None:
        self.nlp_service = NlpService()
        self.embedding_service = EmbeddingService()

    def run(self, resume_text: str, target_role: str, current_skills: List[str], profession: str, level: str) -> AnalysisResult:
        # Resolve role-specific benchmark skills from our curated dictionary.
        role_key = target_role.lower().strip()
        role_skills = ROLE_SKILL_MAP.get(role_key, ROLE_SKILL_MAP["software engineer"])

        extracted_skills = self.nlp_service.extract_skills(resume_text, role_key)
        known_skills = sorted(set([s.lower() for s in extracted_skills + current_skills]))

        missing_skills = [skill for skill in role_skills if skill not in known_skills]
        strengths = [skill for skill in known_skills if skill in role_skills][:8]

        # Semantic similarity compares full resume context against target role skill profile.
        embeddings = self.embedding_service.encode([resume_text, " ".join(role_skills)])
        similarity = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])

        # Final score balances semantic fit and explicit role skill coverage.
        role_coverage = len(strengths) / max(len(role_skills), 1)
        match_score = max(0.0, min(100.0, (0.7 * similarity + 0.3 * role_coverage) * 100))

        transferable = [skill for skill in GENERIC_TRANSFERABLE_SKILLS if skill in resume_text.lower()]
        if not transferable:
            transferable = GENERIC_TRANSFERABLE_SKILLS[:3]

        roadmap = [
            {
                "title": f"Master {skill.title()}",
                "description": f"Build practical projects and measurable proficiency in {skill} for {target_role}."
            }
            for skill in missing_skills[:5]
        ]

        certs = ROLE_CERTIFICATIONS.get(role_key, ROLE_CERTIFICATIONS["software engineer"])

        # Parsed structure is persisted in PostgreSQL JSONB for dashboard rendering.
        parsed_resume = {
            "profession": profession,
            "experienceLevel": level,
            "skillsExtracted": extracted_skills,
            "wordCount": len(resume_text.split())
        }

        return AnalysisResult(
            parsed_resume=parsed_resume,
            match_score=round(match_score, 2),
            strengths=strengths,
            skill_gaps=missing_skills,
            transferable_skills=transferable,
            roadmap=roadmap,
            certifications=certs,
        )
