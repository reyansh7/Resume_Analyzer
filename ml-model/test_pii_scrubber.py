"""
Quick test for pii_scrubber — run with:
  python test_pii_scrubber.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.pii_scrubber import scrub_pii

SAMPLE_RESUME = """John Smith
john.smith@gmail.com | +1 (555) 867-5309 | linkedin.com/in/johnsmith | github.com/jsmith
123 Main Street, Austin, TX 78701

SUMMARY
Software Engineer with 4 years of experience building scalable web applications using Python, React, and AWS.

EXPERIENCE
Senior Software Engineer — Acme Corp, Austin TX  (2022 – Present)
- Built REST APIs using FastAPI and PostgreSQL serving 500k daily users
- Reduced deployment time by 40% using Docker and GitHub Actions CI/CD
- Led migration from monolith to microservices architecture on AWS ECS

Software Engineer — Startup Inc  (2020 – 2022)
- Developed React frontend with TypeScript and Redux
- Implemented OAuth2 authentication and JWT-based session management

EDUCATION
B.S. Computer Science — University of Texas at Austin, 2020

SKILLS
Python, TypeScript, React, Node.js, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, Redis

CERTIFICATIONS
AWS Certified Solutions Architect – Associate (2023)
"""

def run_tests():
    scrubbed = scrub_pii(SAMPLE_RESUME)
    print("=== SCRUBBED OUTPUT ===")
    print(scrubbed)
    print()

    passed = 0
    failed = 0

    checks = [
        # PII that MUST be removed
        ("john.smith@gmail.com",      "[EMAIL]",        True,  "email removed"),
        ("+1 (555) 867-5309",         "[PHONE]",        True,  "phone removed"),
        ("linkedin.com/in/johnsmith", "[PROFILE_URL]",  True,  "linkedin removed"),
        ("github.com/jsmith",         "[PROFILE_URL]",  True,  "github removed"),
        ("123 Main Street",           "[ADDRESS]",      True,  "street address removed"),
        ("Austin, TX 78701",          "[ADDRESS]",      True,  "city/state/zip removed"),
        ("John Smith",                "[CANDIDATE_NAME]",True, "name removed from header"),

        # Professional content that MUST be preserved
        ("FastAPI",                   None,             False, "FastAPI preserved"),
        ("PostgreSQL",                None,             False, "PostgreSQL preserved"),
        ("Docker",                    None,             False, "Docker preserved"),
        ("AWS Certified",             None,             False, "certification preserved"),
        ("React",                     None,             False, "React preserved"),
        ("University of Texas",       None,             False, "education preserved"),
        ("500k daily users",          None,             False, "metric preserved"),
        ("Acme Corp",                 None,             False, "employer preserved"),
        ("REST APIs",                 None,             False, "experience preserved"),
    ]

    for original, replacement, should_be_gone, label in checks:
        if should_be_gone:
            # PII should NOT appear in scrubbed output
            present_in_scrubbed = original.lower() in scrubbed.lower()
            replacement_present = replacement in scrubbed
            ok = not present_in_scrubbed and replacement_present
            status = "PASS" if ok else "FAIL"
            detail = f"'{original}' → '{replacement}'"
        else:
            # Content should still be present
            ok = original in scrubbed
            status = "PASS" if ok else "FAIL"
            detail = f"'{original}' still present"

        print(f"[{status}] {label}: {detail}")
        if ok:
            passed += 1
        else:
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
