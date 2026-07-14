from __future__ import annotations

import os
import logging
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        BitsAndBytesConfig,
        GenerationConfig,
    )
    import torch
except Exception:
    AutoTokenizer = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None
    GenerationConfig = None
    torch = None


@lru_cache(maxsize=1)
def get_model_wrapper():
    """Lazily load a quantized HF model when requested.

    Controlled by env vars:
    - MODEL_NAME: HF model id
    - HF_LOAD_IN_4BIT: if set to '1' or 'true', use bitsandbytes 4-bit
    """
    model_name = os.getenv("MODEL_NAME", "").strip()
    use_4bit = os.getenv("HF_LOAD_IN_4BIT", "true").strip().lower() in {"1", "true", "yes"}
    if not model_name:
        logger.warning("No MODEL_NAME set; LLM disabled")
        return None

    if AutoTokenizer is None or AutoModelForCausalLM is None:
        logger.warning("transformers or torch not available; LLM disabled")
        return None

    try:
        if use_4bit and BitsAndBytesConfig is not None:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=False,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16 if torch is not None else None,
                trust_remote_code=False,
            )

        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)

        return {"model": model, "tokenizer": tokenizer}
    except Exception as e:
        logger.exception("Failed to load HF model: %s", e)
        return None


def generate_text(prompt: str, max_new_tokens: int = 128) -> str | None:
    wrapper = get_model_wrapper()
    if not wrapper:
        return None

    model = wrapper["model"]
    tokenizer = wrapper["tokenizer"]

    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        # Move inputs to model device
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            gen = model.generate(**inputs, max_new_tokens=max_new_tokens)
        text = tokenizer.decode(gen[0], skip_special_tokens=True)
        return text
    except Exception:
        logger.exception("LLM generation failed")
        return None


def _build_rewrite_prompt(
    bullets: List[str],
    resume_text: str,
    target_role: str,
    profession: str,
    experience_level: str,
    current_skills: List[str] | None,
    rewrite_instructions: str | None,
) -> str:
    skill_list = ", ".join(skill for skill in (current_skills or []) if skill) or "No skills supplied"
    instruction_block = rewrite_instructions.strip() if rewrite_instructions and rewrite_instructions.strip() else (
        "Rewrite the bullets so they are specific, measurable when evidence exists, ATS-friendly, and tailored to the target role. "
        "Do not invent employers, tools, metrics, or outcomes that are not supported by the resume text."
    )

    bullet_block = "\n".join(f"- {bullet}" for bullet in bullets)
    context_block = f"""
Project context:
- Application: Resume Analyzer
- Target role: {target_role or 'Unknown'}
- Profession: {profession or 'Unknown'}
- Experience level: {experience_level or 'Unknown'}
- Current skills: {skill_list}

Resume context:
{resume_text[:2500]}

Input bullets:
{bullet_block}
""".strip()

    return (
        "You are the resume rewrite engine for the Resume Analyzer project. "
        "Your job is to improve resume bullets while preserving truthfulness and relevance. "
        "Return ONLY a valid JSON array of objects with the keys section, before, after, and improvement_type. "
        "Do not include markdown, commentary, code fences, or extra keys. "
        f"User instructions: {instruction_block}\n\n"
        f"{context_block}"
    )


def generate_rewrites(
    bullets: List[str],
    *,
    resume_text: str,
    target_role: str,
    profession: str,
    experience_level: str,
    current_skills: List[str] | None = None,
    rewrite_instructions: str | None = None,
) -> List[dict]:
    """Ask the model to improve resume bullets. Returns list of {before, after}.

    Falls back to empty list on failure.
    """
    if not bullets:
        return []

    use_llm = os.getenv("USE_HF_LLM", "false").strip().lower() in {"1", "true", "yes"}
    if not use_llm:
        return []

    prompt = _build_rewrite_prompt(
        bullets=bullets,
        resume_text=resume_text,
        target_role=target_role,
        profession=profession,
        experience_level=experience_level,
        current_skills=current_skills,
        rewrite_instructions=rewrite_instructions,
    )

    raw = generate_text(prompt, max_new_tokens=512)
    if not raw:
        return []

    # Try to extract JSON-like list from the raw output
    import re, json

    m = re.search(r"(\[\s*\{.*\}\s*\])", raw, re.S)
    if not m:
        # As a fallback, pair lines sequentially
        results = []
        for b in bullets:
            results.append({"before": b, "after": b})
        return results

    try:
        arr = json.loads(m.group(1))
        out = []
        for item in arr:
            before = item.get("before") if isinstance(item.get("before"), str) else ""
            after = item.get("after") if isinstance(item.get("after"), str) else ""
            out.append({"before": before, "after": after})
        return out
    except Exception:
        logger.exception("Failed to parse model JSON output")
        return []
