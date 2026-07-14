"""End-to-end test of the /analyze/v2 endpoint with a realistic resume."""
import json
import urllib.request

PAYLOAD = {
    "resumeText": """
John Doe | johndoe@email.com

SKILLS
Python, JavaScript, React, Node.js, SQL, Git, REST APIs, Docker (basic), TypeScript

EXPERIENCE
Software Engineer Intern — TechStartup Inc. (June 2023 – Dec 2023)
- Developed a React dashboard for tracking user analytics, improving page load time by 30%
- Built REST API endpoints using Node.js and Express, integrated with PostgreSQL database
- Collaborated with a 4-person team using Agile/Scrum methodology

Student Technical Head — CodeClub, ABC University (2022-2023)
- Led operations and event execution for a 200-member student technical club
- Organized 3 national-level hackathons with 500+ participants
- Coordinated cross-functional teams for project delivery and outreach

PROJECTS
Resume Classifier (Python, scikit-learn, Streamlit)
- Built an NLP-based resume classification model achieving 87% accuracy on 2400 resume samples
- Deployed on Streamlit Cloud with interactive filtering and prediction visualization

E-Commerce REST API (Node.js, Express, MongoDB)
- Implemented RESTful API with JWT authentication, rate limiting, and role-based access control
- Handled 500+ concurrent requests with average response time under 200ms

EDUCATION
B.Tech Computer Science — ABC University (2020-2024) | CGPA: 8.4/10
HSC Class XII — XYZ School (2020) | 91%
SSC Class X — XYZ School (2018) | 94%

CERTIFICATIONS & ACHIEVEMENTS
AWS Cloud Practitioner — Amazon Web Services (2023)
Google Data Analytics Certificate — Coursera (2022)
Winner — Smart India Hackathon 2023 (National Level)
Finalist — HackOut 5.0 (Top 10 out of 500 teams)
Codeforces Specialist — Rating 1450
""",
    "targetRole": "Software Engineer",
    "currentSkills": ["Python", "React", "Node.js", "SQL", "JavaScript"],
    "profession": "Software Engineer",
    "experienceLevel": "Junior",
    "rewriteInstructions": "",
}

print("Posting to /analyze/v2 ...")
body = json.dumps(PAYLOAD).encode("utf-8")
req = urllib.request.Request(
    "http://localhost:8000/analyze/v2",
    data=body,
    method="POST",
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(req, timeout=300) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print("\n✅ Response received!")
print(f"  matchScore           : {data.get('matchScore')}")
print(f"  overall_score        : {data.get('overall_score')}")
print(f"  confidence           : {data.get('confidence')}")
print(f"  strengths            : {data.get('strengths', [])[:4]}")
print(f"  skillGaps            : {data.get('skillGaps', [])[:4]}")
print(f"  certifications       : {data.get('certifications', [])}")
print(f"  skill_insights count : {len(data.get('skill_insights', []))}")
print(f"  roadmap entries      : {len(data.get('roadmap', []))}")
print(f"  rewrite_suggestions  : {len(data.get('rewrite_suggestions', []))}")
print(f"  ats_analysis         : {data.get('ats_analysis', {}).get('status')} (score={data.get('ats_analysis', {}).get('ats_score')})")

pr = data.get("parsedResume", {})
print(f"\n  parsedResume fields:")
print(f"    skillsExtracted      : {pr.get('skillsExtracted', [])[:5]}")
print(f"    softSkillsHighlights : {pr.get('softSkillsHighlights', [])}")
print(f"    certificationsDetected: {pr.get('certificationsDetected', [])}")
print(f"    awardsDetected       : {pr.get('awardsDetected', [])}")
print(f"    featuredExperiences  : {pr.get('featuredExperiences', [])[:2]}")
print(f"    educationHighlights  : {pr.get('educationHighlights', [])}")
print(f"    overviewSource       : {pr.get('overviewSource')}")
print(f"    overviewModel        : {pr.get('overviewModel')}")
print(f"    roadmapSource        : {pr.get('roadmapSource')}")
print(f"    roadmapModel         : {pr.get('roadmapModel')}")

roadmap_adv = data.get("roadmap_advanced", {})
print(f"\n  roadmap_advanced:")
for phase in ("30_day_plan", "60_day_plan", "90_day_plan"):
    tasks = roadmap_adv.get(phase, [])
    print(f"    {phase}: {len(tasks)} tasks")
    for t in tasks[:2]:
        print(f"      [{t.get('difficulty')}] {t.get('title')} ~{t.get('estimated_hours')}h")

print("\n  breakdown:", data.get("breakdown"))
