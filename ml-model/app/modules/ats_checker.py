from __future__ import annotations

from collections import Counter
import re
from typing import List


ACTION_VERBS = {
    "built",
    "developed",
    "implemented",
    "optimized",
    "led",
    "designed",
    "improved",
    "automated",
}

WEAK_VERBS = {"worked", "helped", "assisted", "handled", "responsible"}


class AtsChecker:
    def _keyword_density(self, resume_text: str, keywords: List[str]) -> float:
        tokens = re.findall(r"[a-zA-Z0-9+#.]+", resume_text.lower())
        if not tokens:
            return 0.0
        counts = Counter(tokens)
        total_keywords = sum(counts.get(keyword.lower(), 0) for keyword in keywords)
        return total_keywords / max(len(tokens), 1)

    def _status(self, score: float) -> str:
        if score >= 85:
            return "ATS Safe"
        if score >= 70:
            return "Needs Optimization"
        return "High Rejection Risk"

    def evaluate(self, resume_text: str, target_role_skills: List[str]) -> dict:
        lowered = resume_text.lower()
        issues: List[str] = []

        keyword_density = self._keyword_density(resume_text, target_role_skills)
        if keyword_density < 0.018:
            issues.append("Low keyword density for target role skills")

        if not any(section in lowered for section in ["experience", "projects", "skills", "education"]):
            issues.append("Missing standard ATS-friendly section structure")

        if len(resume_text.split()) < 220:
            issues.append("Resume content appears too short for ATS depth")

        weak_found = [verb for verb in WEAK_VERBS if re.search(rf"\b{verb}\b", lowered)]
        if weak_found:
            issues.append("Weak verbs detected")

        strong_verb_present = any(verb in lowered for verb in ACTION_VERBS)
        if not strong_verb_present:
            issues.append("Missing strong action verbs")

        metric_density = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", lowered)) / max(len(lowered.split()), 1)
        if metric_density < 0.01:
            issues.append("Low quantified impact evidence")

        if any(token in lowered for token in ["graphic", "icon", "table", "image"]):
            issues.append("Potentially ATS-unfriendly graphics/table usage")

        if "certification" not in lowered and "certifications" not in lowered:
            issues.append("Missing certifications section")

        font_safety_score = 100 if not any(token in lowered for token in ["comic sans", "papyrus"]) else 45
        structure_score = 100 if all(section in lowered for section in ["experience", "skills", "education"]) else 68
        action_score = 100 if (not weak_found and strong_verb_present and metric_density >= 0.01) else 60
        keyword_score = max(35, min(100, int(keyword_density * 4700)))
        content_depth_score = max(50, min(100, int((len(resume_text.split()) / 550) * 100)))

        ats_score = round(
            (0.15 * font_safety_score)
            + (0.30 * keyword_score)
            + (0.22 * structure_score)
            + (0.18 * action_score)
            + (0.15 * content_depth_score),
            2,
        )

        return {
            "ats_score": ats_score,
            "status": self._status(ats_score),
            "issues": issues[:6],
        }
