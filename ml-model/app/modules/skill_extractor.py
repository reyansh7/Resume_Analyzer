from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List

from app.services.nlp_service import NlpService
from app.utils.skill_dictionary import ROLE_SKILL_MAP


SOFT_SKILL_HINTS = {
    "communication": ["communicat", "present", "stakeholder", "collaborat", "cross-functional"],
    "leadership": ["led", "mentored", "managed", "ownership", "owned"],
    "problem solving": ["solved", "debug", "root cause", "optimized", "improved"],
    "teamwork": ["team", "collaborat", "pair", "coordina"],
    "adaptability": ["adapt", "fast-paced", "learned", "pivot"],
}


@dataclass
class SkillInsight:
    skill: str
    detected_from: str
    confidence: float
    related_missing_skills: List[str]
    improvement_suggestions: str
    resources: List[dict]


class SkillExtractor:
    def __init__(self) -> None:
        self.nlp_service = NlpService()

    def _lines(self, text: str) -> List[str]:
        lines = [line.strip() for line in text.splitlines()]
        lines = [re.sub(r"\s+", " ", line) for line in lines if line.strip()]
        return lines

    def _find_snippet(self, text: str, skill: str) -> str:
        pattern = re.compile(rf"\b{re.escape(skill.lower())}\b", re.IGNORECASE)
        for line in self._lines(text):
            if pattern.search(line):
                return line[:220]
        return f"Detected from skill/entity matching patterns for {skill}."

    def _resource_pack(self, skill: str) -> List[dict]:
        slug = skill.lower().replace(" ", "-")
        return [
            {
                "title": f"{skill} Official Documentation",
                "type": "documentation",
                "link": f"https://www.google.com/search?q={slug}+official+documentation",
            },
            {
                "title": f"{skill} Hands-on Course",
                "type": "course",
                "link": f"https://www.youtube.com/results?search_query={slug}+full+course",
            },
        ]

    def _related_missing(self, role_key: str, present: list[str], skill: str) -> List[str]:
        role_skills = ROLE_SKILL_MAP.get(role_key, ROLE_SKILL_MAP["software engineer"])
        lower_present = {item.lower() for item in present}
        filtered = [item for item in role_skills if item.lower() not in lower_present and item.lower() != skill.lower()]
        return filtered[:3]

    def extract(self, resume_text: str, target_role: str, role_key: str) -> tuple[List[str], List[str], List[SkillInsight]]:
        technical_skills = self.nlp_service.extract_skills(resume_text, role_key)

        soft_skills: List[str] = []
        text_lower = resume_text.lower()
        for skill, hints in SOFT_SKILL_HINTS.items():
            if any(hint in text_lower for hint in hints):
                soft_skills.append(skill)

        insights: List[SkillInsight] = []
        for skill in technical_skills[:18]:
            snippet = self._find_snippet(resume_text, skill)
            confidence = 0.92 if skill.lower() in text_lower else 0.72
            insights.append(
                SkillInsight(
                    skill=skill.title(),
                    detected_from=snippet,
                    confidence=round(confidence, 2),
                    related_missing_skills=self._related_missing(role_key, technical_skills, skill),
                    improvement_suggestions=(
                        f"Deepen {skill} with one production project and measurable impact statements in your resume."
                    ),
                    resources=self._resource_pack(skill),
                )
            )

        # include soft-skill cards if we have room
        for soft_skill in soft_skills:
            if len(insights) >= 22:
                break
            insights.append(
                SkillInsight(
                    skill=soft_skill.title(),
                    detected_from=self._find_snippet(resume_text, soft_skill.split()[0]),
                    confidence=0.66,
                    related_missing_skills=[],
                    improvement_suggestions=f"Support {soft_skill} with quantified outcomes and leadership examples.",
                    resources=self._resource_pack(soft_skill),
                )
            )

        return technical_skills, soft_skills, insights
