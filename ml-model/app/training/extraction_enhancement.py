"""
Enhanced extraction module to improve certifications, awards, and experience detection.
This module provides improved patterns and filtering logic for better resume section extraction.
"""

import re
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ExtractionPatterns:
    """Enhanced patterns for better resume section detection."""
    
    # Certifications keywords
    CERT_KEYWORDS = {
        "certification", "certified", "certificate", "credential", 
        "license", "licensed", "aws", "azure", "google cloud",
        "coursera", "udemy", "nptel", "scrum", "kubernetes",
        "terraform", "docker", "foundation", "associate",
        "professional", "specialist", "expert", "oracle",
        "salesforce", "comptia", "microsoft", "vendor",
        "accredited", "accreditation"
    }
    
    # Award keywords
    AWARD_KEYWORDS = {
        "award", "awardee", "awarded", "achievement", "achieved",
        "honor", "honours", "honorable", "accomplishment",
        "winner", "won", "finalist", "finalist", "recognition",
        "recognized", "placed", "rank", "ranked", "ranking",
        "scholarship", "scholastic", "medal", "medalist",
        "dean's list", "distinction", "prize", "first place",
        "second place", "third place", "top performer",
        "best", "outstanding", "excellence", "exceptional"
    }
    
    # Experience keywords (less restrictive)
    EXPERIENCE_KEYWORDS = {
        "led", "managed", "coordinated", "delivered", "built",
        "improved", "organized", "achieved", "supported",
        "assessed", "guided", "mentored", "worked", "worked on",
        "responsible for", "oversaw", "supervised", "conducted",
        "executed", "established", "created", "developed",
        "implemented", "spearheaded", "pioneered", "initiated"
    }
    
    # Experience role indicators
    ROLE_INDICATORS = {
        "intern", "internship", "job", "position", "role",
        "employment", "company", "organization", "team",
        "club", "committee", "officer", "member", "associate",
        "coordinator", "lead", "head", "president", "secretary",
        "volunteer", "executive", "chairman"
    }


class EnhancedExtractionFilter:
    """Enhanced filter for resume section extraction."""
    
    def __init__(self):
        self.patterns = ExtractionPatterns()
        self.min_experience_score = 1  # Lowered from implicit 2-3
        self.min_cert_score = 1
        self.min_award_score = 1
    
    def score_certification(self, text: str) -> int:
        """Score likelihood that text is a certification."""
        score = 0
        lower_text = text.lower()
        
        # Check for certification keywords
        cert_count = sum(1 for keyword in self.patterns.CERT_KEYWORDS 
                        if keyword in lower_text)
        score += cert_count * 2
        
        # Check for certification patterns
        if re.search(r"\b(?:aws|gcp|azure|oracle)\s+(?:certified|associate|professional|specialist)\b", lower_text):
            score += 5
        
        if re.search(r"\b(?:certified|certified?)\s+(?:kubernetes|docker|scrum|terraform|salesforce)\b", lower_text):
            score += 4
        
        if re.search(r"(?:course|completed|earned|obtained).*(?:certificate|certification)", lower_text):
            score += 3
        
        # Penalty for non-cert content
        if re.search(r"\b(?:project|experience|award|internship|worked|led|managed)\b", lower_text):
            if "certificate" not in lower_text and "certified" not in lower_text:
                score -= 2
        
        return max(0, score)
    
    def score_award(self, text: str) -> int:
        """Score likelihood that text is an award."""
        score = 0
        lower_text = text.lower()
        
        # Check for award keywords
        award_count = sum(1 for keyword in self.patterns.AWARD_KEYWORDS 
                         if keyword in lower_text)
        score += award_count * 2
        
        # Check for award patterns
        if re.search(r"\b(?:winner|finalist|ranked?|rank\s+\d+|top\s+\d+)\b", lower_text):
            score += 4
        
        if re.search(r"\b(?:gold|silver|bronze)\s+(?:medal|award)\b", lower_text):
            score += 5
        
        if re.search(r"(?:smart india|hackathon|competition|contest|challenge).*(?:winner|finalist|qualified)", lower_text):
            score += 5
        
        if re.search(r"\b(?:dean's list|distinction|excellence|recognition)\b", lower_text):
            score += 3
        
        # Penalty for non-award content
        if re.search(r"\b(?:certification|certified|project|role|responsibilities|worked)\b", lower_text):
            if not re.search(r"\b(?:won|winner|award|achievement|recognition|honor)\b", lower_text):
                score -= 3
        
        return max(0, score)
    
    def score_experience(self, text: str, is_from_experience_section: bool = True) -> int:
        """Score likelihood that text is work/project experience."""
        score = 0
        lower_text = text.lower()
        
        # Bonus if from experience section
        if is_from_experience_section:
            score += 2
        
        # Check for experience action keywords
        action_count = sum(1 for keyword in self.patterns.EXPERIENCE_KEYWORDS 
                          if keyword in lower_text)
        score += min(action_count, 3) * 2
        
        # Check for role indicators
        role_count = sum(1 for keyword in self.patterns.ROLE_INDICATORS 
                        if keyword in lower_text)
        score += min(role_count, 2) * 1
        
        # Check for quantifiable achievements
        if re.search(r"\b\d+(?:,\d{3})*\s*(?:%|million|thousand|people|team|members?)\b", lower_text):
            score += 2
        
        # Check for impact/outcome indicators
        if re.search(r"\b(?:resulting in|led to|achieved|improved|increased|decreased|accelerated)\b", lower_text):
            score += 1
        
        # Reward length (substantial descriptions are typically experiences)
        if len(text) >= 60:
            score += 1
        
        # Penalty for non-experience content
        penalty = 0
        if re.search(r"\b(?:certification|certified|award|degree|education|bachelor|master|gpa|cgpa)\b", lower_text):
            if not re.search(r"\b(?:led|managed|worked|coordinated|team|organization|company|club)\b", lower_text):
                penalty += 3
        
        return max(0, score - penalty)
    
    def is_valid_entry(self, text: str, min_length: int = 8) -> bool:
        """Check if text is a valid resume entry."""
        if len(text.strip()) < min_length:
            return False
        
        # Remove URLs and emails
        text = re.sub(r"https?://\S+", "", text)
        text = re.sub(r"\S+@\S+", "", text)
        
        # Check for readable content (not noise)
        if re.match(r"^\s*[\d\-/.,()]*\s*$", text):
            return False
        
        # Check for minimum word count
        words = text.split()
        if len(words) < 2:
            return False
        
        return True
    
    def extract_certifications(self, text: str, section_lines: List[str]) -> List[str]:
        """Enhanced certification extraction."""
        certifications = []
        seen = set()
        
        for line in section_lines:
            if not self.is_valid_entry(line, min_length=5):
                continue
            
            # Skip noise
            if re.search(r"^\s*(?:certification|certifications|certificates?)\s*$", line.lower()):
                continue
            
            score = self.score_certification(line)
            if score >= self.min_cert_score:
                line_lower = line.lower()
                if line_lower not in seen:
                    certifications.append(line)
                    seen.add(line_lower)
        
        # Deduplicate similar entries
        deduped = []
        for cert in certifications:
            cert_lower = cert.lower()
            is_duplicate = any(
                cert_lower in other.lower() or other.lower() in cert_lower
                for other in deduped
            )
            if not is_duplicate:
                deduped.append(cert)
        
        return deduped[:10]
    
    def extract_awards(self, text: str, section_lines: List[str]) -> List[str]:
        """Enhanced award extraction."""
        awards = []
        seen = set()
        
        for line in section_lines:
            if not self.is_valid_entry(line, min_length=6):
                continue
            
            # Skip noise
            if re.search(r"^\s*(?:awards?|honors?|achievements?)\s*$", line.lower()):
                continue
            
            score = self.score_award(line)
            if score >= self.min_award_score:
                line_lower = line.lower()
                if line_lower not in seen:
                    awards.append(line)
                    seen.add(line_lower)
        
        # Deduplicate similar entries
        deduped = []
        for award in awards:
            award_lower = award.lower()
            is_duplicate = any(
                award_lower in other.lower() or other.lower() in award_lower
                for other in deduped
            )
            if not is_duplicate:
                deduped.append(award)
        
        return deduped[:8]
    
    def extract_experiences(self, text: str, section_lines: List[str], 
                           is_from_experience_section: bool = True) -> List[str]:
        """Enhanced experience extraction with less aggressive filtering."""
        experiences = []
        seen = set()
        
        scored_lines: List[Tuple[int, str]] = []
        
        for line in section_lines:
            if not self.is_valid_entry(line):
                continue
            
            score = self.score_experience(line, is_from_experience_section)
            if score >= self.min_experience_score:
                scored_lines.append((score, line))
        
        # Sort by score
        scored_lines.sort(key=lambda x: x[0], reverse=True)
        
        # Extract top experiences
        for score, line in scored_lines:
            line_lower = line.lower()
            if line_lower not in seen:
                experiences.append(line)
                seen.add(line_lower)
                if len(experiences) >= 3:
                    break
        
        # If we still need more, be less strict
        if len(experiences) < 3:
            for score, line in scored_lines:
                if line not in experiences:
                    experiences.append(line)
                    if len(experiences) >= 3:
                        break
        
        return experiences[:3]


def create_training_examples() -> Dict[str, List[List[str]]]:
    """Create training examples for extraction improvement."""
    return {
        "certifications": [
            ["AWS Certified Developer Associate"],
            ["Google Cloud Professional Data Engineer"],
            ["Certified Kubernetes Administrator (CKA)"],
            ["Microsoft Azure Developer Associate"],
            ["HashiCorp Certified: Terraform Associate"],
            ["Scrum Master Certification"],
            ["Oracle Database Administrator Certified Associate"],
            ["AWS Solutions Architect Professional"],
        ],
        "awards": [
            ["Winner - Smart India Hackathon 2024"],
            ["Finalist - National Coding Championship"],
            ["Dean's List - GPA > 3.8"],
            ["Best Project Award - College Technical Festival"],
            ["Gold Medal - State-level Science Competition"],
            ["Rank 1 on Codeforces - Maximum Rating 2100"],
            ["Achieved Pupil Rank on Codeforces"],
            ["Qualified for Google Code Jam Final Round"],
        ],
        "experiences": [
            ["Led cross-functional team of 5 engineers to deliver project 2 weeks early"],
            ["Coordinated outreach strategy with 3 partner organizations"],
            ["Marketing Intern: Managed social media campaigns reaching 50K users"],
            ["President of Technical Club: Organized 10+ events with 500+ participants"],
            ["Implemented CI/CD pipeline reducing deployment time by 60%"],
            ["Developed React dashboard used by 1000+ internal employees"],
            ["Mentor: Guided 3 junior developers on best practices and coding standards"],
        ],
    }
