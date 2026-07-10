# Enhanced AI Interview Question Generator
import os
import time
import random
import re
import hashlib
from datetime import datetime
from django.db.models import Count
from candidate.models import InterviewRecord

# Optional Groq import
try:
    from groq import Groq
except Exception:
    Groq = None

# ================== LOAD & CONFIGURE GROQ/GEMINI ==================

GROQ_ENABLED = False
client = None
try:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and Groq is not None:
        try:
            client = Groq(api_key=api_key)
            GROQ_ENABLED = True
        except Exception:
            GROQ_ENABLED = False
    else:
        GROQ_ENABLED = False
except Exception:
    GROQ_ENABLED = False 

import google.generativeai as genai
GEMINI_ENABLED = False
try:
    gemini_key = os.getenv("GEMINI_API_KEY_1")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        GEMINI_ENABLED = True
except Exception:
    GEMINI_ENABLED = False

# ================== DIFFICULTY PROGRESSION ==================
def get_difficulty_by_interview_count(count: int) -> str:
    """
    Progressive difficulty based on interview count:
    1st interview → very_easy (basic role understanding)
    2-3 interviews → easy (experience and tools)
    4+ interviews → medium (scenarios and problem-solving)
    """
    if count <= 1:
        return "very_easy"
    elif count <= 3:
        return "easy"
    return "medium"

# ================== ENHANCED PROMPT BUILDER ==================
def build_enhanced_prompt(role, designation, difficulty, num_questions, previous_questions, candidate_experience="", language="English"):
    """
    Build a comprehensive prompt for accurate, role-specific questions.
    """
    role_context = {
        "IT": "technology and software development",
        "Non-IT": "business operations and management"
    }.get(role, "professional")
    
    difficulty_context = {
        "very_easy": "basic understanding and fundamental concepts",
        "easy": "simple beginner-friendly questions that are straightforward", 
        "medium": "intermediate questions requiring practical understanding and real-world scenarios",
        "hard": "complex system design and advanced problem-solving situations",
        "advanced": "challenging questions that test deeper knowledge, expert-level skills, and real-world interview standards"
    }
    
    exclude_text = ""
    if previous_questions:
        exclude_text = f"\n\nIMPORTANT: Avoid these previously asked questions:\n{chr(10).join(f'- {q}' for q in previous_questions[:5])}"
    
    coding_instructions = ""
    if role == "IT":
        if difficulty in ["advanced", "hard"]:
            coding_instructions = "6. You MUST provide a mix of advanced theoretical questions and coding test questions. Ensure at least some questions require the candidate to write code. VERY IMPORTANT: You MUST prefix every coding question exactly with the tag [CODING] at the very beginning of the question text."
        else:
            coding_instructions = "6. Focus on theoretical knowledge and practical experience. Do NOT ask them to write code scripts. VERY IMPORTANT: Keep the questions very simple and short, strictly a maximum of 2-3 sentences."
    elif role == "Non-IT":
        if difficulty in ["advanced", "hard"]:
            coding_instructions = "6. You MUST provide a mix of advanced theoretical questions and complex problem-solving scenarios."
        else:
            coding_instructions = "6. Focus on industry-relevant theory, professional skills, and basic operations. Do NOT ask complex problem-solving scenarios. VERY IMPORTANT: Keep the questions very simple and short, strictly a maximum of 2-3 sentences."

    # Add randomness seed to ensure different questions every time
    random_seed = random.randint(1, 1000000)

    prompt = f"""You are an expert HR interviewer specializing in {role_context} roles.

Generate {num_questions} completely unique and different interview questions for a {designation} position. (Seed: {random_seed})

CONTEXT:
- Role: {designation}
- Domain: {role_context}
- Difficulty Level: {difficulty} ({difficulty_context[difficulty]})
- Focus: Real interview scenarios, practical knowledge, and role-specific skills

REQUIREMENTS:
1. Questions must be specific to {designation} responsibilities and skills
2. Difficulty: {difficulty} level only
3. Questions should be clear, professional, and interview-appropriate
4. Focus on practical experience and problem-solving abilities
5. Provide UNIQUE questions not commonly found in generic lists.
{coding_instructions}
7. IMPORTANT: You MUST generate all the questions in the following language: {language}.

FORMAT: Return only numbered questions (1. Question text?)
{exclude_text}

Generate {num_questions} questions:"""

    return prompt

# ================== ENHANCED QUESTION EXTRACTION ==================
def extract_questions(text, num_questions):
    """Extract and clean questions from AI response."""
    questions = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Match numbered questions (1. Question text?)
        if re.match(r'^\d+\.', line):
            # Extract question text after number
            question_text = re.sub(r'^\d+\.\s*', '', line).strip()
            if question_text and question_text.endswith('?'):
                questions.append(question_text)
        # Also match questions without numbers but ending with ?
        elif line.endswith('?') and len(line) > 10:
            questions.append(line)
    
    return questions[:num_questions]

# ================== PERSISTENT QUESTION HISTORY ==================
def get_previous_questions_for_candidate(candidate_id, designation):
    """Get questions previously asked to this candidate for this designation."""
    try:
        previous_interviews = InterviewRecord.objects.filter(
            candidate_id=candidate_id,
            designation=designation
        ).order_by('-created_at')
        
        previous_questions = set()
        for interview in previous_interviews:
            for eval_item in interview.evaluations:
                if 'question' in eval_item:
                    previous_questions.add(eval_item['question'])
        
        return list(previous_questions)
    except Exception:
        return []

def get_interview_count_for_designation(candidate_id, designation):
    """Get how many times this candidate has been interviewed for this designation."""
    try:
        return InterviewRecord.objects.filter(
            candidate_id=candidate_id,
            designation=designation
        ).count()
    except Exception:
        return 0

# ================== ENHANCED FALLBACK QUESTIONS ==================
def get_fallback_questions(role, designation, difficulty, num_questions):
    """Comprehensive fallback questions organized by role and difficulty."""
    
    # IT Role Questions
    it_questions = {
        "very_easy": [
            f"What programming languages are you most comfortable with for {designation} work?",
            f"Can you explain the basic responsibilities of a {designation}?",
            f"What development tools or IDEs do you use regularly?",
            f"How do you stay updated with the latest technologies in your field?",
            f"What is your understanding of version control systems like Git?"
        ],
        "easy": [
            f"Describe a project where you used {designation} skills to solve a problem.",
            f"What frameworks or libraries are you most experienced with?",
            f"How do you approach debugging and troubleshooting in your work?",
            f"Can you explain your experience with database design and management?",
            f"What is your experience with testing and quality assurance processes?"
        ],
        "medium": [
            f"Walk us through how you would design a scalable system for a {designation} project.",
            f"Describe a challenging technical problem you solved and your approach.",
            f"How do you handle conflicting requirements from different stakeholders?",
            f"Explain your experience with cloud platforms and deployment strategies.",
            f"What is your approach to code review and maintaining code quality?"
        ],
        "hard": [
            f"Write a Python script to perform load balancing for a distributed {designation} service.",
            f"Implement a function that optimizes a complex database query used by a {designation}.",
            f"Design an architecture for a high-availability system and explain the trade-offs.",
            f"Write a Python script to detect and resolve race conditions in multi-threaded code.",
            f"Explain deep internals of memory management in your primary programming language."
        ],
        "advanced": [
            f"Write a Python script that implements a custom caching mechanism with an LRU eviction policy.",
            f"Implement a function that handles leader election in a distributed system.",
            f"Design a highly scalable microservices architecture for a global application.",
            f"Write a script to analyze and mitigate a sophisticated security vulnerability.",
            f"What are the hardest algorithmic optimization problems you've solved?"
        ]
    }
    
    # Non-IT Role Questions
    non_it_questions = {
        "very_easy": [
            f"What are the key responsibilities of a {designation} in your understanding?",
            f"How do you prioritize tasks in a busy work environment?",
            f"What software tools do you use for {designation} work?",
            f"How do you handle customer or client interactions?",
            f"What is your approach to meeting deadlines and targets?"
        ],
        "easy": [
            f"Describe a successful project you managed as a {designation}.",
            f"How do you handle difficult team members or stakeholders?",
            f"What metrics do you use to measure success in your role?",
            f"Can you explain your experience with budget management?",
            f"How do you stay organized when handling multiple projects?"
        ],
        "medium": [
            f"Walk us through how you would handle a crisis situation in your role.",
            f"Describe a time when you had to implement a major change in your organization.",
            f"How do you balance competing priorities from different departments?",
            f"Explain your approach to strategic planning and goal setting.",
            f"What is your experience with cross-functional team leadership?"
        ],
        "hard": [
            f"Describe how you would design a comprehensive 5-year strategy for a {designation} department.",
            f"How do you handle a situation where executive leadership disagrees with your critical decisions?",
            f"What is your approach to turning around an underperforming team or division?",
            f"Describe a complex negotiation you've led and the strategies you employed.",
            f"How do you manage severe budget cuts while maintaining operational efficiency?"
        ],
        "advanced": [
            f"How do you identify and capitalize on disruptive market trends in your industry?",
            f"Describe your experience with mergers, acquisitions, or major organizational restructuring.",
            f"How do you foster a culture of continuous innovation at an enterprise level?",
            f"Explain your framework for assessing and mitigating enterprise-wide risks.",
            f"What is your philosophy on building and scaling global operations?"
        ]
    }
    
    questions = it_questions if role == "IT" else non_it_questions
    available = questions.get(difficulty, questions["medium"])
    random.shuffle(available)
    return available[:num_questions]

# ================== MAIN ENHANCED GENERATOR ==================
def generate_questions(role, designation, num_questions=5, candidate_id=None, requested_difficulty=None, language="English"):
    """
    Enhanced question generator with persistent history and role-specific accuracy.
    """
    if not role or not designation:
        return ["Error: Role and designation required."]
    
    # Get candidate's interview history for this designation
    interview_count = get_interview_count_for_designation(candidate_id, designation) if candidate_id else 0
    previous_questions = get_previous_questions_for_candidate(candidate_id, designation) if candidate_id else []
    
    # Determine difficulty based on interview count or requested difficulty
    if requested_difficulty:
        difficulty = requested_difficulty
    else:
        difficulty = get_difficulty_by_interview_count(interview_count)
    
    # Try AI generation first
    ai_questions = []
    success = False
    
    prompt = build_enhanced_prompt(role, designation, difficulty, num_questions, previous_questions, language=language)
    
    if GROQ_ENABLED and client:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.9,
                top_p=0.9,
                max_tokens=800,
            )
            
            response_text = chat_completion.choices[0].message.content
            ai_questions = extract_questions(response_text, num_questions)
            if len(ai_questions) > 0:
                success = True
        except Exception as e:
            print(f"Groq generation failed: {e}")
            
    if not success and GEMINI_ENABLED:
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt, generation_config=genai.GenerationConfig(
                temperature=0.9,
                top_p=0.9
            ))
            response_text = response.text
            ai_questions = extract_questions(response_text, num_questions)
            if len(ai_questions) > 0:
                success = True
        except Exception as e:
            print(f"Gemini generation failed: {e}")

    if success:
        # Filter out previously asked questions
        new_questions = [q for q in ai_questions if q not in previous_questions]
        
        if len(new_questions) >= num_questions:
            return new_questions[:num_questions]
        elif new_questions:
            # Supplement with fallback questions
            remaining = num_questions - len(new_questions)
            fallback = get_fallback_questions(role, designation, difficulty, remaining)
            fallback = [q for q in fallback if q not in previous_questions and q not in new_questions]
            combined = new_questions + fallback[:remaining]
            # If still short, pad with generic templates
            if len(combined) < num_questions:
                templates = [
                    f"What are your core responsibilities as a {designation}?",
                    f"Describe a challenging situation you handled as a {designation}.",
                    f"Which tools or methods do you rely on most as a {designation}?",
                    f"How do you measure success in your {designation} role?",
                    f"Tell us about a project that best showcases your {designation} skills."
                ]
                for t in templates:
                    if t not in combined:
                        combined.append(t)
                    if len(combined) >= num_questions:
                        break
            return combined[:num_questions]
    
    # Fallback to predefined questions
    fallback_questions = get_fallback_questions(role, designation, difficulty, num_questions)
    filtered_questions = [q for q in fallback_questions if q not in previous_questions]
    
    # Ensure we always return at least num_questions; pad with generic templates if needed
    if len(filtered_questions) < num_questions:
        templates = [
            f"What interests you most about the {designation} role?",
            f"How do you stay current in {designation}-related practices?",
            f"Can you walk through your typical day as a {designation}?",
            f"Describe a time you improved a process in your {designation} work.",
            f"How do you collaborate with stakeholders in your {designation} responsibilities?"
        ]
        for t in templates:
            if t not in filtered_questions:
                filtered_questions.append(t)
            if len(filtered_questions) >= num_questions:
                break
    
    return filtered_questions[:num_questions]
