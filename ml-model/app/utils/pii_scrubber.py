"""
PII scrubber for resume text sent to external LLM APIs (Gemini, etc.).

Strips personally identifiable information before the text leaves the server.
The scrubbed text is analysis-equivalent — skills, experience bullets, job
titles, companies, education, and certifications are fully preserved.

What gets removed:
  - Email addresses          → [EMAIL]
  - Phone numbers            → [PHONE]
  - Physical addresses       → [ADDRESS]
  - LinkedIn / GitHub URLs   → [PROFILE_URL]
  - Generic URLs             → [URL]
  - National ID / SSN        → [ID_NUMBER]
  - Passport / visa numbers  → [ID_NUMBER]
  - Date of birth patterns   → [DOB]
  - Full name (first line)   → [CANDIDATE_NAME]  (heuristic — only header line)
"""

from __future__ import annotations

import re
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_PATTERNS: List[Tuple[str, str]] = [
    # Email
    (
        r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        "[EMAIL]",
    ),
    # Phone — international and local formats
    (
        r"(?<!\d)"
        r"(\+?1[\s\-.]?)?"
        r"(\(?\d{3}\)?[\s\-.]?)"
        r"\d{3}[\s\-.]?\d{4}"
        r"(?!\d)",
        "[PHONE]",
    ),
    # LinkedIn profile URL (with or without https://)
    (
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s,;\"'<>\])\}]+",
        "[PROFILE_URL]",
    ),
    # GitHub profile URL (with or without https://)
    (
        r"(?:https?://)?(?:www\.)?github\.com/[^\s,;\"'<>\])\}]+",
        "[PROFILE_URL]",
    ),
    # Generic URL (after specific ones above)
    (
        r"https?://[^\s,;\"'<>\])\}]{4,}",
        "[URL]",
    ),
    # SSN  (xxx-xx-xxxx or xxxxxxxxx)
    (
        r"\b\d{3}[\s\-]\d{2}[\s\-]\d{4}\b",
        "[ID_NUMBER]",
    ),
    # Passport / national ID (6-9 digit standalone numbers)
    (
        r"\b[A-Z]{1,2}\d{6,9}\b",
        "[ID_NUMBER]",
    ),
    # Date of birth explicit markers
    (
        r"(?i)\b(?:dob|date\s+of\s+birth|born)\s*[:\-]?\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}",
        "[DOB]",
    ),
    # Street address — number + street name pattern
    (
        r"\b\d{1,5}\s+[A-Za-z0-9\s]{3,40}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
        r"Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Circle|Cir|Trail|Tr)\b[.,]?",
        "[ADDRESS]",
    ),
    # City, State ZIP  (US)
    (
        r"\b[A-Za-z\s]{3,25},\s*[A-Z]{2}\s+\d{5}(?:\-\d{4})?\b",
        "[ADDRESS]",
    ),
    # City, Country (common international pattern following address context)
    (
        r"\b[A-Za-z\s]{3,25},\s*[A-Za-z\s]{3,20}\s+\d{5,6}\b",
        "[ADDRESS]",
    ),
]

_COMPILED = [(re.compile(pattern, re.IGNORECASE), replacement)
             for pattern, replacement in _PATTERNS]


def _scrub_name_from_header(text: str) -> str:
    """
    Heuristic: the very first non-empty line of a resume is usually the
    candidate's full name.  Replace it only if it looks like a name
    (2-4 capitalized words, no digits, no special chars).
    """
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Name pattern: 2-4 words, each starting with a capital, no digits
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$", stripped):
            lines[i] = line.replace(stripped, "[CANDIDATE_NAME]")
        # Whether or not we matched, stop after the first non-empty line
        break
    return "\n".join(lines)


def scrub_pii(text: str) -> str:
    """
    Remove PII from resume text before sending to an external LLM.

    Returns the scrubbed text with placeholders in place of personal data.
    Skills, experience, education, certifications, and project descriptions
    are fully preserved.
    """
    if not text:
        return text

    result = _scrub_name_from_header(text)

    for pattern, replacement in _COMPILED:
        result = pattern.sub(replacement, result)

    return result


def scrub_pii_truncated(text: str, max_chars: int) -> str:
    """Scrub PII then truncate to max_chars. Convenience wrapper."""
    return scrub_pii(text)[:max_chars]
