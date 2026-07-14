from __future__ import annotations

import re
from typing import List
import os

try:
    from app.services.llm_service import generate_rewrites
except Exception:
    generate_rewrites = None


WEAK_VERBS = {
    "worked",
    "helped",
    "assisted",
    "involved",
    "responsible",
    "handled",
    "did",
}

WEAK_VERB_PREP_ENDINGS = ["on", "with", "in", "to", "for"]  # Common prep after weak verbs

STRONG_VERBS = ["Built", "Engineered", "Optimized", "Delivered", "Implemented", "Led", "Developed"]

NOISE_PATTERNS = [
    # Section headers
    r"^\s*(experience|projects|education|skills|certifications?|awards|achievements|summary|objective|contact)\s*$",
    # Contact information patterns
    r"^\s*(email|e-mail|phone|mobile|linkedin|github|portfolio|website|web link)\b",
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",  # Email
    r"\+?\d{1,3}[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",  # Phone
    # Skill lists (pipe or comma separated without actions)
    r"^(?:[a-zA-Z+#/.-]+(?:\s*[|,]\s*[a-zA-Z+#/.-]+){2,})$",
    # Role-only lines
    r"\|\s*(founding member|member|executive|operations?|president|secretary|coordinator|volunteer)\s*$",
    r"^\s*(intern|internship|student)\s*$",
    # Skills/tech stacks (comma or pipe separated single words)
    r"^(?:[a-zA-Z0-9+#/.\-]+(?:\s*[,|]\s*)?)+$",    # Job titles (Role - Company format with dates)
    r"^[\w\s]+\-\s*[\w\s]+\s*\(\d{4}",]

OUTCOME_TEMPLATES = [
    "resulting in {metric} faster delivery",
    "achieving {metric} improvement in system efficiency",
    "with {metric} increase in performance",
    "delivering {metric} improvement in reliability",
    "{metric} faster implementation timeline",
    "{metric} improvement in code quality",
    "reducing bugs by {metric}",
    "{metric} improvement in user experience",
    "accelerated to {metric} completion",
]

IMPACT_TEMPLATES = [
    "strengthened team capabilities",
    "enhanced system reliability",
    "improved code maintainability",
    "accelerated development velocity",
    "ensured production stability",
    "optimized system architecture",
    "elevated code quality standards",
    "streamlined project delivery",
]


class ResumeRewriteEngine:
    def _candidate_lines(self, text: str) -> List[str]:
        lines = [line.strip(" -•\t") for line in text.splitlines()]
        lines = [re.sub(r"\s+", " ", line).strip() for line in lines if line.strip()]
        filtered: List[str] = []
        for line in lines:
            lower = line.lower()
            # Skip if matches noise patterns
            if any(re.search(pattern, lower) for pattern in NOISE_PATTERNS):
                continue
            # Skip lines that are too short or too long
            word_count = len(line.split())
            if word_count < 6 or word_count > 36:
                continue
            # Skip section headers
            if line.endswith(":"):
                continue
            # Skip pure skill lists or tech stacks (mostly single words separated by commas/pipes)
            parts = [x.strip() for x in re.split(r"[,|]", line) if x.strip()]
            word_per_part = [len(p.split()) for p in parts]
            
            # If 3+ parts and most are single/dual words (tech names), it's a skill list
            if len(parts) >= 3 and sum(1 for w in word_per_part if w <= 2) >= len(parts) - 1:
                continue
            
            # If too many commas/pipes relative to words (skill list indicator)
            comma_pipe_count = len(re.findall(r"[,|]", line))
            if comma_pipe_count >= word_count / 3:
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
        # Remove contact/email patterns after pipe
        line = re.sub(r"\s*[|,]\s*(?:email|phone|linkedin|github|portfolio|website).*$", "", line, flags=re.IGNORECASE)
        # Remove email addresses
        line = re.sub(r"\S+@\S+", "", line)
        # Remove phone numbers (more careful pattern)
        line = re.sub(r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "", line)
        # Replace pipes and dashes with spaces
        line = re.sub(r"\s*\|\s*", " ", line)
        line = re.sub(r"\s+\-\s+", " ", line)
        # Normalize whitespace
        line = re.sub(r"\s+", " ", line).strip().rstrip(".")
        return line

    def _improvement_type(self, line: str) -> str:
        weak = any(re.search(rf"\b{verb}\b", line.lower()) for verb in WEAK_VERBS)
        has_metric = self._contains_metric(line)
        has_action = self._contains_action_verb(line)
        has_skill_keywords = bool(re.search(r"\b(python|java|javascript|react|node|sql|api|database|cloud|aws)\b", line.lower()))
        
        # Detect if this is primarily a skill/tech list that slipped through
        comma_pipe_count = len(re.findall(r"[,|]", line))
        if comma_pipe_count >= 2:
            return "skip"  # Mark for skipping
        
        # Only offer verb_strengthening if line is substantial and doesn't already have good action verbs
        if not has_action and len(line) >= 20 and not has_skill_keywords:
            return "verb_strengthening"
        
        if weak and not has_metric:
            return "impact_quantification"
        
        if not has_metric and has_action:
            return "metric_enrichment"
        
        if has_skill_keywords:
            return "skip"  # Don't rewrite skill-heavy lines
        
        return "clarity_refinement"

    def _rewrite(self, line: str, index: int) -> tuple[str, str]:
        normalized = self._cleanup(line)
        
        # Don't rewrite very short lines or pure lists
        if len(normalized.split()) < 4:
            return normalized, "skip"
        
        improvement_type = self._improvement_type(normalized)
        
        # Skip if it's a skill list or tech stack
        if improvement_type == "skip":
            return normalized, "skip"
        
        metric = self._extract_or_default_metric(normalized, index=index)

        # Check for weak verb and replace it
        weak = next((verb for verb in WEAK_VERBS if re.search(rf"\b{verb}\b", normalized.lower())), None)
        has_weak_verb = weak is not None
        
        if weak:
            # Replace the weak verb with a strong verb
            strong_verb = STRONG_VERBS[index % len(STRONG_VERBS)]
            
            # Handle multiple patterns:
            # 1. "verb + preposition + gerund/noun" e.g., "Worked on designing X" 
            # 2. "verb + base_verb + noun" e.g., "Helped develop X"
            
            # Pattern 1: verb + prep + gerund
            gerund_pattern = rf"\b{weak}\s+(?:on|with|in|to|for)\s+(?:the\s+)?(\w+ing)\s+"
            match = re.search(gerund_pattern, normalized, re.IGNORECASE)
            if match:
                # Replace entire "verb prep gerund " with just the strong verb
                normalized = re.sub(gerund_pattern, f"{strong_verb} ", normalized, flags=re.IGNORECASE, count=1)
            else:
                # Pattern 2: "verb + weak_action_verb + noun" e.g., "Helped develop X"
                weak_action_verbs = r"(?:develop|build|create|design|write|test|review|deploy|maintain|optimize)"
                action_pattern = rf"\b{weak}\s+{weak_action_verbs}\s+"
                match2 = re.search(action_pattern, normalized, re.IGNORECASE)
                if match2:
                    # Skip the second weak action verb
                    normalized = re.sub(action_pattern, f"{strong_verb} ", normalized, flags=re.IGNORECASE, count=1)
                else:
                    # Simple replacement
                    normalized = re.sub(rf"\b{weak}\b", strong_verb, normalized, flags=re.IGNORECASE, count=1)
                    # Clean up common prepositions that follow weak verbs
                    for prep in WEAK_VERB_PREP_ENDINGS:
                        normalized = re.sub(rf"({strong_verb})\s+{prep}\s+", r"\1 ", normalized, flags=re.IGNORECASE, count=1)

        candidate = self._template(normalized, metric=metric, index=index, improvement_type=improvement_type, has_weak_verb=has_weak_verb)
        candidate = candidate[0].upper() + candidate[1:] if candidate else candidate
        return candidate, improvement_type

    def _template(self, normalized: str, metric: str, index: int, improvement_type: str, has_weak_verb: bool = False) -> str:
        outcome = OUTCOME_TEMPLATES[index % len(OUTCOME_TEMPLATES)].format(metric=metric)
        impact = IMPACT_TEMPLATES[index % len(IMPACT_TEMPLATES)]

        # If we only replaced a weak verb, the strong verb is already in normalized
        if has_weak_verb:
            return f"{normalized.capitalize()}, {outcome}."
        
        # If line already has good action verb, just enhance with outcome/impact
        if improvement_type == "metric_enrichment":
            return f"{normalized.capitalize()}, {outcome}."

        if improvement_type == "clarity_refinement":
            return f"{normalized.capitalize()}, {impact}."

        # Fallback
        return f"{normalized.capitalize()}, {outcome}."

    def analyze_and_rewrite(
        self,
        resume_text: str,
        target_role: str,
        profession: str,
        experience_level: str,
        current_skills: List[str],
        rewrite_instructions: str | None = None,
    ) -> List[dict]:
        rewrites: List[dict] = []
        seen_after: set[str] = set()
        seen_improvement_types: dict[str, int] = {}
        candidates = self._candidate_lines(resume_text)[:10]

        # If HF LLM rewrites are enabled, try to use model-generated rewrites first
        use_llm = os.getenv("USE_HF_LLM", "false").strip().lower() in {"1", "true", "yes"}
        model_results = []
        if use_llm and generate_rewrites is not None:
            try:
                model_results = generate_rewrites(
                    candidates,
                    resume_text=resume_text,
                    target_role=target_role,
                    profession=profession,
                    experience_level=experience_level,
                    current_skills=current_skills,
                    rewrite_instructions=rewrite_instructions,
                )
            except Exception:
                model_results = []

        # Integrate model results if present
        added = 0
        if model_results:
            for item in model_results:
                before = item.get("before", "")
                after = item.get("after", "")
                if not before or not after:
                    continue
                if after.strip().lower() in seen_after:
                    continue
                if len(after.strip()) < 20:
                    continue
                seen_after.add(after.strip().lower())
                rewrites.append(
                    {
                        "section": "Experience/Projects",
                        "before": before,
                        "after": after,
                        "improvement_type": "llm_generated",
                    }
                )
                added += 1
                if added >= 6:
                    break

        # If not enough model rewrites, fall back to rule-based rewrites
        if added < 6:
            for index, line in enumerate(candidates):
                if added >= 6:
                    break
                after, improvement_type = self._rewrite(line, index=index)

                # Skip if marked for skipping
                if improvement_type == "skip":
                    continue

                # Skip if rewrite is same as original
                if after.strip().lower() == line.strip().lower():
                    continue

                # Skip if we've already seen this exact rewrite
                if after.strip().lower() in seen_after:
                    continue

                # Limit repetitive improvement types (max 2 of same type)
                if improvement_type in seen_improvement_types:
                    if seen_improvement_types[improvement_type] >= 2:
                        continue
                    seen_improvement_types[improvement_type] += 1
                else:
                    seen_improvement_types[improvement_type] = 1

                # Skip if rewrite is too short (likely just noise)
                if len(after.strip()) < 30:
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
                added += 1

        return rewrites[:6]
