"""
Ollama LLM service for Resume Analyzer.

Uses llama3.1:8b (already on disk) via Ollama's HTTP API to power:
  1. Deep resume overview  — skills, certs, awards, education, soft skills, experience
  2. Skill gap explanations  — per-skill analysis with resources
  3. Advanced roadmap  — 30/60/90-day structured plan
  4. Resume bullet rewrites  — ATS-optimised rewrites with improvement type

All functions are synchronous, return typed dicts, and degrade gracefully to
empty/None on any error so the rest of the pipeline always returns a result.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import urllib.request
import urllib.error

from app.utils.pii_scrubber import scrub_pii_truncated

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config (read from env, with safe defaults)
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT_MS", "60000")) // 1000  # convert ms → s
OLLAMA_MAX_RETRIES: int = int(os.getenv("OLLAMA_MAX_RETRIES", "1"))

USE_OLLAMA: bool = os.getenv("USE_OLLAMA_ENHANCEMENTS", "false").strip().lower() in {
    "1", "true", "yes", "on"
}


# ---------------------------------------------------------------------------
# Low-level HTTP helper (no extra deps beyond stdlib)
# ---------------------------------------------------------------------------

def _post_json(endpoint: str, payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    """POST JSON to Ollama and return parsed response dict."""
    url = f"{OLLAMA_BASE_URL}{endpoint}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _call_ollama(prompt: str, system: str, timeout: int | None = None) -> str | None:
    """Send a prompt to Ollama and return the text response, or None on failure."""
    if not USE_OLLAMA:
        return None

    t = timeout or OLLAMA_TIMEOUT
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 2048,
            "stop": ["<|eot_id|>", "<|end_of_text|>"],
        },
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }

    for attempt in range(OLLAMA_MAX_RETRIES + 1):
        try:
            t0 = time.monotonic()
            data = _post_json("/api/chat", payload, timeout=t)
            elapsed = round((time.monotonic() - t0) * 1000)
            text = data.get("message", {}).get("content", "") or ""
            logger.info(
                "[ollama] model=%s elapsed_ms=%d chars=%d attempt=%d",
                OLLAMA_MODEL, elapsed, len(text), attempt + 1,
            )
            return text.strip()
        except Exception as exc:
            logger.warning("[ollama] attempt %d/%d failed: %s", attempt + 1, OLLAMA_MAX_RETRIES + 1, exc)
            if attempt < OLLAMA_MAX_RETRIES:
                time.sleep(1)

    return None


def is_ollama_available() -> bool:
    """Quick health check — returns True if Ollama is reachable."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=4) as resp:
            return resp.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json_from_text(text: str) -> Any | None:
    """Extract first JSON object or array from a text blob (handles markdown fences)."""
    if not text:
        return None

    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()

    # Try the whole text first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON array
    m = re.search(r"(\[\s*\{.*\}\s*\])", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find a JSON object
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


# ---------------------------------------------------------------------------
# SYSTEM PROMPT  (shared across all calls for consistency)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert resume analysis engine for the Resume Analyzer platform.
Your output is consumed directly by a structured UI — return ONLY valid JSON with no prose,
no markdown, no code fences, no explanations outside the JSON.
Be specific, factual, and grounded entirely in the resume text provided.
Never invent experience, employers, skills, metrics, or achievements not present in the resume.
Use professional, concise language appropriate for a senior career advisor."""


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
    """
    Returns a rich parsed_resume dict with all the fields the frontend expects:
      skillsExtracted, certificationsDetected, awardsDetected,
      featuredExperiences, featuredProjects, educationHighlights,
      softSkillsHighlights, overviewSource, overviewModel
    """
    if not USE_OLLAMA:
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

    raw = _call_ollama(prompt, _SYSTEM_PROMPT, timeout=45)
    parsed = _extract_json_from_text(raw) if raw else None

    if not isinstance(parsed, dict):
        logger.warning("[ollama] overview parse failed, raw=%s", (raw or "")[:200])
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
        "overviewSource": "ollama",
        "overviewModel": OLLAMA_MODEL,
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
    """
    Returns a list of skill insight objects (for both strengths and gaps).
    Each matches the SkillInsightItem schema the UI renders.
    """
    if not USE_OLLAMA or not (strengths or skill_gaps):
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

    raw = _call_ollama(prompt, _SYSTEM_PROMPT, timeout=60)
    parsed = _extract_json_from_text(raw) if raw else None

    if not isinstance(parsed, list):
        logger.warning("[ollama] skill insights parse failed, raw=%s", (raw or "")[:200])
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
    """
    Returns a roadmap_advanced dict with 30_day_plan, 60_day_plan, 90_day_plan.
    Each entry matches the RoadmapTask schema.
    """
    if not USE_OLLAMA or not missing_skills:
        return {"30_day_plan": [], "60_day_plan": [], "90_day_plan": []}

    skills_str = ", ".join(missing_skills[:10])
    is_tech = any(t in target_role.lower() for t in ["engineer", "developer", "data", "devops", "software"])
    leet_note = "Include 1-2 relevant LeetCode problem set URLs for technical skills." if is_tech else "Omit leetcode_problems (use empty array)."
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

    raw = _call_ollama(prompt, _SYSTEM_PROMPT, timeout=60)
    parsed = _extract_json_from_text(raw) if raw else None

    empty = {"30_day_plan": [], "60_day_plan": [], "90_day_plan": []}
    if not isinstance(parsed, dict):
        logger.warning("[ollama] roadmap parse failed, raw=%s", (raw or "")[:200])
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

def generate_ollama_rewrites(
    resume_text: str,
    target_role: str,
    profession: str,
    level: str,
    current_skills: List[str],
    rewrite_instructions: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Returns rewrite_suggestions list: [{section, before, after, improvement_type}].
    """
    if not USE_OLLAMA:
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

    raw = _call_ollama(prompt, _SYSTEM_PROMPT, timeout=60)
    parsed = _extract_json_from_text(raw) if raw else None

    if not isinstance(parsed, list):
        logger.warning("[ollama] rewrites parse failed, raw=%s", (raw or "")[:200])
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
