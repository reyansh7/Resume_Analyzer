from __future__ import annotations

import re
from typing import List


WEAK_VERBS = {
    "worked",
    "helped",
    "assisted",
    "involved",
    "responsible",
    "handled",
    "did",
}

STRONG_VERBS = ["Built", "Engineered", "Optimized", "Delivered", "Implemented", "Led", "Developed"]

NOISE_PATTERNS = [
    r"^\s*(email|phone|linkedin|github|portfolio)\b",
    r"^\s*(experience|projects|education|skills|certifications?)\s*$",
    r"\|\s*(founding member|member|executive|operations?)\b",
]


class ResumeRewriteEngine:
    def _candidate_lines(self, text: str) -> List[str]:
        lines = [line.strip(" -•\t") for line in text.splitlines()]
        lines = [re.sub(r"\s+", " ", line).strip() for line in lines if line.strip()]
        filtered: List[str] = []
        for line in lines:
            lower = line.lower()
            if any(re.search(pattern, lower) for pattern in NOISE_PATTERNS):
                continue
            if len(line.split()) < 6 or len(line.split()) > 36:
                continue
            if line.endswith(":"):
                continue
            filtered.append(line)
        return filtered

    def _contains_metric(self, line: str) -> bool:
        return bool(re.search(r"\b\d+(?:\.\d+)?%?\b", line))

    def _contains_action_verb(self, line: str) -> bool:
        return bool(re.search(r"\b(built|engineered|developed|implemented|optimized|delivered|led|designed|automated)\b", line.lower()))

    def _extract_or_default_metric(self, line: str, index: int) -> str:
        found = re.findall(r"\b\d+(?:\.\d+)?%?\b", line)
        if found:
            return found[0] if found[0].endswith("%") else f"{found[0]}%"
        defaults = ["18%", "22%", "27%", "31%", "35%"]
        return defaults[index % len(defaults)]

    def _cleanup(self, line: str) -> str:
        line = re.sub(r"\s*\|\s*", " ", line)
        line = re.sub(r"\s+-\s+", " ", line)
        line = re.sub(r"\s+", " ", line).strip().rstrip(".")
        return line

    def _improvement_type(self, line: str) -> str:
        weak = any(re.search(rf"\b{verb}\b", line.lower()) for verb in WEAK_VERBS)
        has_metric = self._contains_metric(line)
        has_action = self._contains_action_verb(line)
        if weak and not has_metric:
            return "impact_quantification"
        if not has_action:
            return "verb_strengthening"
        if not has_metric:
            return "metric_enrichment"
        return "clarity_refinement"

    def _template(self, normalized: str, metric: str, index: int, improvement_type: str) -> str:
        verb = STRONG_VERBS[index % len(STRONG_VERBS)]

        if improvement_type == "verb_strengthening":
            return f"{verb} {normalized.lower()} with clear ownership and measurable outcomes, improving efficiency by {metric}."

        if improvement_type == "metric_enrichment":
            return f"{verb} {normalized.lower()}, resulting in a {metric} improvement in delivery quality and team productivity."

        if improvement_type == "clarity_refinement":
            return f"{verb} {normalized.lower()} while driving consistent execution and stakeholder alignment."

        return f"{verb} {normalized.lower()}, reducing turnaround time by {metric} through measurable process improvements."

    def _rewrite(self, line: str, index: int) -> tuple[str, str]:
        normalized = self._cleanup(line)
        metric = self._extract_or_default_metric(normalized, index=index)
        improvement_type = self._improvement_type(normalized)

        weak = next((verb for verb in WEAK_VERBS if re.search(rf"\b{verb}\b", normalized.lower())), None)
        if weak:
            normalized = re.sub(rf"\b{weak}\b", STRONG_VERBS[index % len(STRONG_VERBS)], normalized, flags=re.IGNORECASE, count=1)

        candidate = self._template(normalized, metric=metric, index=index, improvement_type=improvement_type)
        candidate = candidate[0].upper() + candidate[1:] if candidate else candidate
        return candidate, improvement_type

    def analyze_and_rewrite(self, resume_text: str) -> List[dict]:
        rewrites: List[dict] = []
        seen_after: set[str] = set()

        for index, line in enumerate(self._candidate_lines(resume_text)[:10]):
            after, improvement_type = self._rewrite(line, index=index)
            if after.strip().lower() == line.strip().lower():
                continue
            if after.strip().lower() in seen_after:
                continue
            seen_after.add(after.strip().lower())
            rewrites.append(
                {
                    "section": "Experience/Projects",
                    "before": line,
                    "after": after,
                    "improvement_type": improvement_type,
                }
            )
        return rewrites[:6]
