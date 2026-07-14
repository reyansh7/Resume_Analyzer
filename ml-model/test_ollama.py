"""Quick smoke test for Ollama service integration."""
import os
import sys
from pathlib import Path

# Load .env
env_file = Path(__file__).parent / ".env"
for line in env_file.read_text(encoding="utf-8").splitlines():
    raw = line.strip()
    if not raw or raw.startswith("#") or "=" not in raw:
        continue
    key, value = raw.split("=", 1)
    env_key = key.strip()
    env_value = value.strip().strip('"').strip("'")
    if env_key and env_key not in os.environ:
        os.environ[env_key] = env_value

from app.services.ollama_service import (
    USE_OLLAMA,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    is_ollama_available,
    analyze_resume_overview,
    generate_skill_insights,
    generate_advanced_roadmap,
    generate_ollama_rewrites,
)

print(f"USE_OLLAMA           : {USE_OLLAMA}")
print(f"OLLAMA_MODEL         : {OLLAMA_MODEL}")
print(f"OLLAMA_BASE_URL      : {OLLAMA_BASE_URL}")
print(f"Ollama reachable     : {is_ollama_available()}")

SAMPLE_RESUME = """
John Doe | johndoe@email.com | LinkedIn: linkedin.com/in/johndoe

SKILLS
Python, JavaScript, React, Node.js, SQL, Git, REST APIs, Docker (basic)

EXPERIENCE
Software Engineer Intern — TechStartup Inc. (2023)
- Developed a React dashboard for tracking user analytics, improving load time by 30%
- Built REST API endpoints using Node.js and Express, integrated with PostgreSQL database
- Collaborated with a 4-person team using Agile/Scrum methodology

Student Technical Head — CodeClub, ABC University (2022-2023)
- Led operations and event execution for a 200-member student technical club
- Organized 3 national-level hackathons with 500+ participants

PROJECTS
Resume Classifier (Python, scikit-learn, Streamlit)
- Built an NLP-based resume classification model achieving 87% accuracy on 2400 samples
- Deployed on Streamlit Cloud with interactive filtering and prediction visualization

E-Commerce API (Node.js, Express, MongoDB)
- Implemented RESTful API with JWT authentication, rate limiting, and role-based access control
- Handled 500+ concurrent requests with <200ms response time

EDUCATION
B.Tech Computer Science — ABC University (2020-2024) | CGPA: 8.4/10
HSC (Class XII) — XYZ School (2020) | 91%

CERTIFICATIONS
AWS Cloud Practitioner (2023)
Google Data Analytics Certificate (Coursera, 2022)

AWARDS & ACHIEVEMENTS
- Winner — Smart India Hackathon 2023 (National Level)
- Finalist — HackOut 5.0 (Top 10 out of 500 teams)
- Codeforces Rating: 1450 (Specialist)
"""

if not USE_OLLAMA:
    print("\nUSE_OLLAMA_ENHANCEMENTS is false — set it to true in .env to run LLM tests")
    sys.exit(0)

if not is_ollama_available():
    print("\nOllama not reachable — make sure `ollama serve` is running")
    sys.exit(1)

print("\n" + "="*60)
print("TEST 1: Resume Overview")
print("="*60)
overview = analyze_resume_overview(
    resume_text=SAMPLE_RESUME,
    target_role="Software Engineer",
    profession="Engineer",
    level="Junior",
    current_skills=["Python", "React", "Node.js", "SQL"],
)
print(f"  skillsExtracted      : {overview.get('skillsExtracted', [])[:5]}")
print(f"  softSkillsHighlights : {overview.get('softSkillsHighlights', [])}")
print(f"  certificationsDetected: {overview.get('certificationsDetected', [])}")
print(f"  awardsDetected       : {overview.get('awardsDetected', [])}")
print(f"  featuredExperiences  : {overview.get('featuredExperiences', [])[:2]}")
print(f"  educationHighlights  : {overview.get('educationHighlights', [])}")
print(f"  overviewSource       : {overview.get('overviewSource')}")
print(f"  overviewModel        : {overview.get('overviewModel')}")

print("\n" + "="*60)
print("TEST 2: Skill Insights")
print("="*60)
insights = generate_skill_insights(
    resume_text=SAMPLE_RESUME,
    target_role="Software Engineer",
    strengths=["Python", "React", "Node.js", "SQL"],
    skill_gaps=["Docker", "Kubernetes", "System Design", "TypeScript"],
    level="Junior",
)
print(f"  Total insight cards  : {len(insights)}")
for ins in insights[:3]:
    print(f"  - {ins['skill']}: confidence={ins['confidence']:.2f}, resources={len(ins['resources'])}")

print("\n" + "="*60)
print("TEST 3: Advanced Roadmap")
print("="*60)
roadmap = generate_advanced_roadmap(
    missing_skills=["Docker", "Kubernetes", "System Design", "TypeScript"],
    target_role="Software Engineer",
    level="Junior",
    resume_text=SAMPLE_RESUME,
)
for phase in ("30_day_plan", "60_day_plan", "90_day_plan"):
    tasks = roadmap.get(phase, [])
    print(f"  {phase}: {len(tasks)} tasks")
    for t in tasks:
        print(f"    - [{t['difficulty']}] {t['title']} (~{t['estimated_hours']}h)")

print("\n" + "="*60)
print("TEST 4: Resume Rewrites")
print("="*60)
rewrites = generate_ollama_rewrites(
    resume_text=SAMPLE_RESUME,
    target_role="Software Engineer",
    profession="Engineer",
    level="Junior",
    current_skills=["Python", "React", "Node.js", "SQL"],
)
print(f"  Total rewrites       : {len(rewrites)}")
for rw in rewrites[:3]:
    print(f"  [{rw['improvement_type']}]")
    print(f"    BEFORE: {rw['before'][:80]}")
    print(f"    AFTER : {rw['after'][:80]}")

print("\n✅ All Ollama tests passed!")
