# Training Placeholder Dataset Structure

Use this directory for curated, privacy-safe training/evaluation data:

- `train.jsonl`
- `val.jsonl`
- `test.jsonl`

Recommended schema per row:

```json
{
  "resume_text": "...",
  "target_role": "software engineer",
  "gold_skills": ["react", "typescript", "docker"],
  "soft_skills": ["communication", "ownership"],
  "education_level": "bachelor",
  "experience_label": "mid",
  "match_label": 0.78
}
```

Keep PII removed before model training.
