"""
Gemini LLM service for Resume Analyzer.

Drop-in replacement for ollama_service — same function signatures,
same return types, same graceful fallback on any error.

Calls the Gemini REST API directly (no SDK required) so the Docker
image stays lean.  Supports exponential-backoff retries on 429 errors.

Controlled by env vars:
  USE_GEMINI_ENHANCEMENTS=true   — enable this service
  USE_GEMINI_ROADMAP=true        — enable roadmap generation via Gemini
  GEMINI_API_KEY=<key>           — required
  GEMINI_MODEL=gemini-2.0-flash  — model to use
  GEMINI_TIMEOUT_MS=8000         — per-request timeout in ms
  GEMINI_MAX_RETRIES=2           — retries on 429 / transient errors
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from app.utils.pii_scrubber import scrub_pii_truncated

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
GEMINI_TIMEOUT: int = max(5, int(os.getenv("GEMINI_TIMEOUT_MS", "8000")) // 1000)
GEMINI_MAX_RETRIES: int = int(os.getenv("GEMINI_MAX_RETRIES", "2"))

USE_GEMINI: bool = (
    os.getenv("USE_GEMINI_ENHANCEMENTS", "false").strip().lower() in {"1", "true", "yes", "on"}
    and bool(GEMINI_API_KEY)
)
USE_GEMINI_ROADMAP: bool = (
    os.getenv("USE_GEMINI_ROADMAP", "false").strip().lower() in {"1", "true", "yes", "on"}
    and bool(GEMINI_API_KEY)
)

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# ---------------------------------------------------------------------------
# System prompt (same as ollama_service for consistency)
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = (
    "You are an expert resume analysis engine for the Resume Analyzer platform. "
    "Your output is consumed directly by a structured UI — return ONLY valid JSON with no prose, "
    "no markdown, no code fences, no explanations outside the JSON. "
    "Be specific, factual, and grounded entirely in the resume text provided. "
    "Never invent experience, employers, skills, metrics, or achievements not present in the resume. "
    "Use professional, concise language appropriate for a senior career advisor."
)


# ---------------------------------------------------------------------------
# Low-level HTTP helper
# ---------------------------------------------------------------------------

def _call_gemini(prompt: str, timeout: int | None = None) -> str | None:
    """
    Send a prompt to the Gemini generateContent endpoint.
    Returns the text response, or None on failure.
    Retries on 429 with exponential backoff.
    """
    if not GEMINI_API_KEY:
        logger.warning("[gemini] GEMINI_API_KEY not set — skipping")
        return None

    t = timeout or GEMINI_TIMEOUT
    url = f"{_GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "topP": 0.9,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        },
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    delay = 2.0
    for attempt in range(GEMINI_MAX_RETRIES + 1):
        try:
            t0 = time.monotonic()
            with urllib.request.urlopen(req, timeout=t) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            elapsed = round((time.monotonic() - t0) * 1000)
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                or ""
            )
            logger.info(
                "[gemini] model=%s elapsed_ms=%d chars=%d attempt=%d",
                GEMINI_MODEL, elapsed, len(text), attempt + 1,
            )
            return text.strip()

        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                logger.warning(
                    "[gemini] 429 rate-limited attempt=%d — retrying in %.1fs", attempt + 1, delay
                )
                if attempt < GEMINI_MAX_RETRIES:
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
                continue
            logger.warning("[gemini] HTTP %d on attempt %d: %s", exc.code, attempt + 1, exc)
            if attempt < GEMINI_MAX_RETRIES:
                time.sleep(delay)
                delay *= 2
        except Exception as exc:
            logger.warning("[gemini] attempt %d/%d failed: %s", attempt + 1, GEMINI_MAX_RETRIES + 1, exc)
            if attempt < GEMINI_MAX_RETRIES:
                time.sleep(delay)
                delay *= 2

    logger.error("[gemini] all %d attempts exhausted", GEMINI_MAX_RETRIES + 1)
    return None


# ---------------------------------------------------------------------------
# JSON extraction helper (same as ollama_service)
# ---------------------------------------------------------------------------

def _extract_json_from_text(text: str) -> Any | None:
    if not text:
        return None
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"(\[\s*\{.*\}\s*\])", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"(\{.*\})", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def _safe_str(value: Any, max_len: int = 300) -> str:
    if isinstance(value, str):
        return value.strip()[:max_len]
    return ""


def _safe_list(value: Any, item_max_len: int = 200) -> List[str]:
    if not isinstance(value, list):
        return []
    return [_safe_str(item, item_max_len) for item in value if isinstance(item, str) and item.strip()]


# ===========================================================================
# 1. RESUME OVERVIEW
# ===========================================================================

def analyze_resume_overview(
    resume_text: str,
    target_role: str,
    profession: str,
    level: str,
    current_skills: List[str],
) -> Dict[str, Any]:
    if not USE_GEMINI:
        return {}

    skill_hint = ", ".join(current_skills[:12]) if current_skills else "none provided"
    safe_resume = scrub_pii_truncated(resume_text, 4000)

    prompt = f"""Analyze this resume thoroughly and return a single JSON object.

RESUME TEXT:
\"\"\"
{safe_resume}
\"\"\"

CANDIDATE CONTEXT:
- Target role: {target_role}
- Profession: {profession}
- Experience level: {level}
- Self-reported skills: {skill_hint}

Return this exact JSON structure (all fields required, use empty arrays/null where absent):
{{
  "skillsExtracted": ["array of all technical skills found in resume, max 20"],
  "softSkillsHighlights": ["array of soft skills / interpersonal strengths found, max 6"],
  "certificationsDetected": ["array of certifications, licenses, courses found verbatim, max 10"],
  "awardsDetected": ["array of awards, honors, achievements, rankings found verbatim, max 8"],
  "featuredExperiences": ["array of 2-4 strongest work/internship/club experience bullets from resume"],
  "featuredProjects": ["array of 2-3 strongest project summaries from resume"],
  "educationHighlights": ["array of education entries found: degree, institution, year if present, max 5"],
  "wordCount": <integer word count of resume>,
  "resumePreview": "<first 200 chars of resume text, verbatim>",
  "predictedCategory": "<best-fit industry category: INFORMATION-TECHNOLOGY | FINANCE | ENGINEERING | BUSINESS-DEVELOPMENT | HEALTHCARE | OTHER>",
  "targetCategoryMatch": <true if resume category matches target role category, else false>
}}

Rules:
- skillsExtracted must be actual skills from the resume (languages, frameworks, tools, platforms)
- featuredExperiences must be real bullets from the resume, cleaned and readable
- featuredProjects must be real project entries, not job roles
- Do NOT invent anything not in the resume text
- Return only the JSON object, nothing else"""

    raw = _call_gemini(prompt)
    parsed = _extract_json_from_text(raw) if raw else None

    if not isinstance(parsed, dict):
        logger.warning("[gemini] overview parse failed, raw=%s", (raw or "")[:200])
        return {}

    return {
        "skillsExtracted": _safe_list(parsed.get("skillsExtracted"), 60),
        "softSkillsHighlights": _safe_list(parsed.get("softSkillsHighlights"), 60),
        "certificationsDetected": _safe_list(parsed.get("certificationsDetected"), 120),
        "awardsDetected": _safe_list(parsed.get("awardsDetected"), 150),
        "featuredExperiences": _safe_list(parsed.get("featuredExperiences"), 220),
        "featuredProjects": _safe_list(parsed.get("featuredProjects"), 220),
        "educationHighlights": _safe_list(parsed.get("educationHighlights"), 150),
        "wordCount": int(parsed.get("wordCount", 0)) or None,
        "resumePreview": _safe_str(parsed.get("resumePreview"), 300),
        "predictedCategory": _safe_str(parsed.get("predictedCategory"), 60) or None,
        "overviewSource": "gemini",
        "overviewModel": GEMINI_MODEL,
    }


# ===========================================================================
# 2. SKILL GAP INSIGHTS
# ===========================================================================

def generate_skill_insights(
    resume_text: str,
    target_role: str,
    strengths: List[str],
    skill_gaps: List[str],
    level: str,
) -> List[Dict[str, Any]]:
    if not USE_GEMINI or not (strengths or skill_gaps):
        return []

    strengths_str = ", ".join(strengths[:8]) if strengths else "none"
    gaps_str = ", ".join(skill_gaps[:8]) if skill_gaps else "none"
    safe_resume = scrub_pii_truncated(resume_text, 3000)

    prompt = f"""Analyze the resume and produce detailed skill insight cards for a candidate targeting: {target_role} ({level} level).

RESUME EXCERPT:
\"\"\"
{safe_resume}
\"\"\"

DETECTED STRENGTHS: {strengths_str}
SKILL GAPS TO CLOSE: {gaps_str}

Return a JSON array of skill insight objects. Include ALL strengths first, then ALL gaps.
Each object must have exactly these fields:
{{
  "skill": "<skill name>",
  "detected_from": "<1-2 sentences: where exactly this skill was found in the resume OR why it is missing>",
  "confidence": <0.0-1.0 float: how confident the detection is, strengths near 0.8-0.95, gaps near 0.1-0.3>,
  "related_missing_skills": ["up to 3 related skills also worth developing"],
  "improvement_suggestions": "<1-2 actionable sentences: exactly how to demonstrate or deepen this skill>",
  "resources": [
    {{"title": "<resource name>", "type": "course|documentation|practice|video", "link": "<real working URL>"}}
  ]
}}

Rules:
- detected_from must reference specific evidence from the resume or explain absence
- improvement_suggestions must be concrete (e.g. "Build a REST API project using X and add a metrics dashboard")
- resources links must be real (YouTube search, official docs, LeetCode, Coursera — never invented URLs)
- Confidence for strengths found in resume: 0.75-0.95. For gaps: 0.10-0.30
- Return ONLY the JSON array, nothing else"""

    raw = _call_gemini(prompt, timeout=15)
    parsed = _extract_json_from_text(raw) if raw else None

    if not isinstance(parsed, list):
        logger.warning("[gemini] skill insights parse failed, raw=%s", (raw or "")[:200])
        return []

    insights: List[Dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        skill = _safe_str(item.get("skill"), 80)
        if not skill:
            continue
        resources: List[Dict[str, str]] = []
        for r in (item.get("resources") or []):
            if isinstance(r, dict) and r.get("title") and r.get("link"):
                resources.append({
                    "title": _safe_str(r.get("title"), 100),
                    "type": _safe_str(r.get("type"), 30) or "course",
                    "link": _safe_str(r.get("link"), 200),
                })
        insights.append({
            "skill": skill,
            "detected_from": _safe_str(item.get("detected_from"), 300),
            "confidence": float(item.get("confidence") or 0.5),
            "related_missing_skills": _safe_list(item.get("related_missing_skills"), 60)[:3],
            "improvement_suggestions": _safe_str(item.get("improvement_suggestions"), 300),
            "resources": resources[:3],
        })

    return insights[:20]


# ===========================================================================
# 3. ADVANCED ROADMAP  (30/60/90-day plan)
# ===========================================================================

def generate_advanced_roadmap(
    missing_skills: List[str],
    target_role: str,
    level: str,
    resume_text: str,
) -> Dict[str, List[Dict[str, Any]]]:
    if not USE_GEMINI_ROADMAP or not missing_skills:
        return {"30_day_plan": [], "60_day_plan": [], "90_day_plan": []}

    skills_str = ", ".join(missing_skills[:10])
    is_tech = any(t in target_role.lower() for t in ["engineer", "developer", "data", "devops", "software"])
    leet_note = (
        "Include 1-2 relevant LeetCode problem set URLs for technical skills."
        if is_tech
        else "Omit leetcode_problems (use empty array)."
    )
    safe_resume = scrub_pii_truncated(resume_text, 1500)

    prompt = f"""Create a structured 30/60/90-day skill development roadmap for a {level} {target_role}.

SKILLS TO DEVELOP (in priority order): {skills_str}

CANDIDATE RESUME EXCERPT (for context):
\"\"\"
{safe_resume}
\"\"\"

Assign skills to phases:
- 30_day_plan: first 3-4 highest-priority skills (Beginner difficulty)
- 60_day_plan: next 3-4 skills (Intermediate difficulty)
- 90_day_plan: remaining skills (Advanced difficulty)

Return a JSON object with exactly these three keys. Each plan is an array of task objects:
{{
  "30_day_plan": [
    {{
      "skill": "<skill name>",
      "title": "<action-oriented task title, e.g. 'Master Docker Containerization'>",
      "difficulty": "Beginner",
      "estimated_hours": <integer 4-10>,
      "priority_score": <float 0.8-1.0 for first skills, decreasing>,
      "suggested_courses": ["<real course name on Coursera/Udemy/official docs>", "<second option>"],
      "youtube_links": ["https://www.youtube.com/results?search_query=<skill>+tutorial+beginner"],
      "leetcode_problems": ["https://leetcode.com/problemset/"],
      "details": "<2-3 sentences: what to build, what to measure, how to add to resume>"
    }}
  ],
  "60_day_plan": [...],
  "90_day_plan": [...]
}}

Rules:
- Each phase must have at least 1 task if skills remain
- details must be specific and actionable (name a specific project idea)
- suggested_courses should be real, well-known courses (not invented titles)
- {leet_note}
- Return ONLY the JSON object, nothing else"""

    raw = _call_gemini(prompt, timeout=15)
    parsed = _extract_json_from_text(raw) if raw else None

    empty: Dict[str, List[Dict[str, Any]]] = {"30_day_plan": [], "60_day_plan": [], "90_day_plan": []}
    if not isinstance(parsed, dict):
        logger.warning("[gemini] roadmap parse failed, raw=%s", (raw or "")[:200])
        return empty

    def _parse_tasks(tasks_raw: Any) -> List[Dict[str, Any]]:
        if not isinstance(tasks_raw, list):
            return []
        out = []
        for t in tasks_raw:
            if not isinstance(t, dict):
                continue
            skill = _safe_str(t.get("skill"), 80)
            title = _safe_str(t.get("title"), 120)
            if not skill or not title:
                continue
            diff = _safe_str(t.get("difficulty"), 20)
            if diff not in {"Beginner", "Intermediate", "Advanced"}:
                diff = "Beginner"
            out.append({
                "skill": skill,
                "title": title,
                "difficulty": diff,
                "estimated_hours": int(t.get("estimated_hours") or 6),
                "priority_score": float(t.get("priority_score") or 0.7),
                "suggested_courses": _safe_list(t.get("suggested_courses"), 120)[:3],
                "youtube_links": _safe_list(t.get("youtube_links"), 200)[:2],
                "leetcode_problems": _safe_list(t.get("leetcode_problems"), 200)[:2],
                "details": _safe_str(t.get("details"), 400),
            })
        return out

    return {
        "30_day_plan": _parse_tasks(parsed.get("30_day_plan")),
        "60_day_plan": _parse_tasks(parsed.get("60_day_plan")),
        "90_day_plan": _parse_tasks(parsed.get("90_day_plan")),
    }


# ===========================================================================
# 4. RESUME BULLET REWRITES
# ===========================================================================

def generate_gemini_rewrites(
    resume_text: str,
    target_role: str,
    profession: str,
    level: str,
    current_skills: List[str],
    rewrite_instructions: Optional[str] = None,
) -> List[Dict[str, str]]:
    if not USE_GEMINI:
        return []

    skill_list = ", ".join(current_skills[:10]) if current_skills else "see resume"
    safe_resume = scrub_pii_truncated(resume_text, 3500)
    instruction_block = (
        rewrite_instructions.strip()
        if rewrite_instructions and rewrite_instructions.strip()
        else (
            "Rewrite bullets to be ATS-friendly, action-first, specific, and quantified where evidence exists. "
            "Do not invent any numbers, employers, tools, or outcomes not in the resume."
        )
    )

    prompt = f"""You are rewriting resume bullets for a {level} {profession} targeting: {target_role}.

RESUME TEXT:
\"\"\"
{safe_resume}
\"\"\"

CURRENT SKILLS: {skill_list}

REWRITE INSTRUCTIONS:
{instruction_block}

Identify the 4-6 weakest or most improvable bullets from the Experience and Projects sections.
Return a JSON array where each object has:
{{
  "section": "<Experience | Projects | Skills | Summary>",
  "before": "<exact original bullet text from resume>",
  "after": "<improved version: action verb, specific outcome, ATS keywords for {target_role}>",
  "improvement_type": "<one of: verb_strengthening | impact_quantification | metric_enrichment | clarity_refinement | ats_optimization | keyword_injection>"
}}

Rules:
- before must be an exact quote from the resume text above
- after must be grounded in the resume — do not invent employers, projects, or metrics not present
- Use strong action verbs (Built, Engineered, Optimized, Delivered, Implemented, Led, Automated)
- Add ATS keywords relevant to {target_role} naturally
- Each rewrite must be meaningfully different from the original
- Return ONLY the JSON array, nothing else"""

    raw = _call_gemini(prompt, timeout=15)
    parsed = _extract_json_from_text(raw) if raw else None

    if not isinstance(parsed, list):
        logger.warning("[gemini] rewrites parse failed, raw=%s", (raw or "")[:200])
        return []

    valid_types = {
        "verb_strengthening", "impact_quantification", "metric_enrichment",
        "clarity_refinement", "ats_optimization", "keyword_injection",
    }

    rewrites: List[Dict[str, str]] = []
    seen_before: set[str] = set()
    for item in parsed:
        if not isinstance(item, dict):
            continue
        before = _safe_str(item.get("before"), 400)
        after = _safe_str(item.get("after"), 500)
        if not before or not after or before.lower() == after.lower():
            continue
        if before.lower() in seen_before:
            continue
        if len(after) < 20:
            continue
        seen_before.add(before.lower())
        improvement = _safe_str(item.get("improvement_type"), 40)
        if improvement not in valid_types:
            improvement = "clarity_refinement"
        rewrites.append({
            "section": _safe_str(item.get("section"), 40) or "Experience/Projects",
            "before": before,
            "after": after,
            "improvement_type": improvement,
        })

    return rewrites[:6]
