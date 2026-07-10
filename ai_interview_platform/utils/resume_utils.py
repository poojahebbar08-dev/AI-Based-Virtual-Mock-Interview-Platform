import os
import tempfile
import requests
from typing import Dict, Any, List
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


import re

def _check_is_resume(text: str, candidate_name: str = None) -> bool:
    """
    Determine if the text contains characteristics of a genuine resume.
    """
    text_lower = text.lower()
    
    # 1. Email check
    email_regex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    has_email = bool(email_regex.search(text))
    
    # 2. Phone check (matches standard formats like +1-234-567-8901, (123) 456-7890, 10 digits, etc.)
    phone_regex = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10}\b')
    has_phone = bool(phone_regex.search(text))
    
    # 3. Name check
    has_name = False
    if candidate_name:
        # Check for full name or major parts of it (excluding extremely common short words or initials)
        name_parts = [p.lower() for p in candidate_name.split() if len(p) > 2]
        if name_parts:
            has_name = candidate_name.lower() in text_lower or any(part in text_lower for part in name_parts)
    if not has_name:
        has_name = "name:" in text_lower or "full name:" in text_lower
        
    # 4. Contact Information
    contact_keywords = ["contact", "address", "phone", "email", "mobile", "linkedin.com", "github.com"]
    has_contact = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in contact_keywords)
    
    # Major Resume Sections
    # 5. Skills
    skills_keywords = ["skills", "core competencies", "expertise", "proficiencies", "skill set"]
    has_skills = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in skills_keywords)
    
    # 6. Education
    education_keywords = ["education", "academic", "university", "college", "degree", "bachelor", "master", "school", "gpa", "qualifications"]
    has_education = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in education_keywords)
    
    # 7. Experience
    experience_keywords = ["experience", "work history", "employment", "professional experience", "work experience", "career history", "job history"]
    has_experience = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in experience_keywords)
    
    # 8. Projects
    projects_keywords = ["projects", "personal projects", "academic projects", "selected projects", "project details"]
    has_projects = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in projects_keywords)
    
    # 9. Certifications
    certifications_keywords = ["certifications", "certification", "certified", "credentials", "courses"]
    has_certifications = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in certifications_keywords)
    
    # 10. Technical Skills
    tech_skills_keywords = ["technical skills", "technologies", "programming languages", "tools"]
    has_tech_skills = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in tech_skills_keywords)
    
    # 11. Objective / Summary
    summary_keywords = ["objective", "summary", "professional summary", "about me", "profile", "career objective"]
    has_summary = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in summary_keywords)
    
    # 12. Achievements
    achievements_keywords = ["achievements", "accomplishments", "awards", "honors"]
    has_achievements = any(re.search(rf'\b{re.escape(kw)}\b', text_lower) for kw in achievements_keywords)
    
    checklist = {
        "Email": has_email,
        "Phone Number": has_phone,
        "Name": has_name,
        "Contact Information": has_contact,
        "Skills": has_skills,
        "Education": has_education,
        "Experience": has_experience,
        "Projects": has_projects,
        "Certifications": has_certifications,
        "Technical Skills": has_tech_skills,
        "Objective/Summary": has_summary,
        "Achievements": has_achievements,
    }
    
    matched_characteristics = [k for k, v in checklist.items() if v]
    match_count = len(matched_characteristics)
    
    major_sections = [
        has_skills, has_education, has_experience, has_projects,
        has_certifications, has_tech_skills, has_summary, has_achievements
    ]
    major_count = sum(1 for v in major_sections if v)
    
    print(f"Resume validation characteristics matched: {matched_characteristics}")
    print(f"Total characteristics matched: {match_count}, Major sections matched: {major_count}")
    
    # A genuine resume must match at least 4 of these characteristics, and contain at least 2 major sections.
    return match_count >= 4 and major_count >= 2


def _simple_text_classification(text: str, candidate_name: str = None) -> Dict[str, Any]:
    """
    Very lightweight fallback classifier that:
    - extracts a rough list of "skills" as unique keywords
    - classifies the profile as IT / Non-IT based on keyword hits
    """
    text_lower = text.lower()

    it_keywords = [
        "python", "java", "javascript", "react", "django", "flask", "api",
        "sql", "database", "docker", "kubernetes", "aws", "azure",
        "git", "github", "devops", "linux", "cloud", "node.js",
        "html", "css", "c++", "c#", ".net", "spring", "microservices",
        "machine learning", "data science", "tensorflow", "pytorch",
    ]
    non_it_keywords = [
        "hr", "recruiter", "talent acquisition", "payroll", "onboarding",
        "sales", "business development", "marketing", "seo", "content",
        "customer support", "operations", "accountant", "finance",
        "teacher", "administration", "office assistant",
    ]

    it_hits = sum(1 for kw in it_keywords if kw in text_lower)
    non_it_hits = sum(1 for kw in non_it_keywords if kw in text_lower)

    if it_hits == 0 and non_it_hits == 0:
        field = ""
    elif it_hits >= non_it_hits:
        field = "IT"
    else:
        field = "Non-IT"

    # Very rough "skills" list: top unique keywords that matched
    skills: List[str] = []
    for kw in it_keywords + non_it_keywords:
        if kw in text_lower:
            skills.append(kw)

    is_resume = _check_is_resume(text, candidate_name)

    return {
        "field": field,
        "skills": skills,
        "is_resume": is_resume,
    }


def parse_resume_and_detect_field(resume_path_or_url: str, candidate_name: str = None) -> Dict[str, Any]:
    """
    Best-effort resume parsing that is safe for deployment:
    - Accepts either a local file path or a Cloudinary URL
    - Downloads from URL if needed, then uses pdfminer.six to extract plain text
    - Classifies IT / Non-IT based on keyword hits in the text
    - Avoids heavy spaCy/pyresparser dependencies that often fail on servers
    """
    if not resume_path_or_url:
        print("[WARNING] parse_resume_and_detect_field: resume_path_or_url is empty")
        return {"field": "", "skills": [], "raw_text": ""}

    temp_file_path = None
    resume_path = resume_path_or_url

    # Check if it's a URL (Cloudinary or HTTP/HTTPS)
    if resume_path_or_url.startswith(('http://', 'https://')):
        try:
            print(f"[INFO] Downloading resume from URL: {resume_path_or_url[:50]}...")
            response = requests.get(resume_path_or_url, timeout=30)
            response.raise_for_status()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file_path = temp_file.name
            temp_file.write(response.content)
            temp_file.close()
            
            resume_path = temp_file_path
            print(f"[SUCCESS] Resume downloaded to temp file: {temp_file_path}")
        except Exception as e:
            print(f"[WARNING] Failed to download resume from URL: {e}")
            return {"field": "", "skills": [], "raw_text": ""}
    elif not os.path.exists(resume_path):
        print(f"[WARNING] parse_resume_and_detect_field: resume_path does not exist: {resume_path}")
        return {"field": "", "skills": [], "raw_text": ""}

    raw_text = ""

    # Try pdfminer first
    try:
        from pdfminer.high_level import extract_text  # type: ignore
        raw_text = extract_text(resume_path) or ""
    except Exception as e:
        print(f"[WARNING] pdfminer extract_text failed: {e}")
        try:
            # As a very last resort, read as plain text
            with open(resume_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
        except Exception as e2:
            print(f"[WARNING] Fallback plain-text read failed: {e2}")
            raw_text = ""
    finally:
        # Clean up temporary file if we created one
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"[INFO] Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                print(f"[WARNING] Failed to delete temp file: {e}")

    classified = _simple_text_classification(raw_text, candidate_name)
    print("[INFO] Resume classification result:", classified)

    return {
        **classified,
        "raw_text": raw_text,
    }


