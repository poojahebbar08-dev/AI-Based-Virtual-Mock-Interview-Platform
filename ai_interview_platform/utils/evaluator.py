# Enhanced AI Interview Answer Evaluator
import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Setup Groq
GROQ_ENABLED = False
client = None
api_key = os.getenv("GROQ_API_KEY")
if api_key:
    try:
        client = Groq(api_key=api_key, timeout=60.0)
        GROQ_ENABLED = True
    except Exception:
        pass

# Setup Gemini
import google.generativeai as genai
GEMINI_ENABLED = False
try:
    gemini_key = os.getenv("GEMINI_API_KEY_1")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        GEMINI_ENABLED = True
except Exception:
    pass

# Use Llama 3 model for evaluation
MODEL_NAME = "llama-3.3-70b-versatile"

# Enhanced evaluation criteria with detailed descriptions
EVALUATION_CRITERIA = {
    "Relevance and Clarity": {
        "description": "How well the answer addresses the question and communicates ideas clearly",
        "1": "Answer is completely irrelevant or incomprehensible",
        "2": "Answer is mostly off-topic or very unclear",
        "3": "Answer is somewhat relevant but lacks clarity",
        "4": "Answer is relevant and mostly clear",
        "5": "Answer directly addresses the question with excellent clarity"
    },
    "Technical Knowledge": {
        "description": "Demonstration of role-specific technical skills and knowledge",
        "1": "No technical knowledge demonstrated",
        "2": "Very basic or incorrect technical understanding",
        "3": "Some technical knowledge but with gaps",
        "4": "Good technical knowledge with minor gaps",
        "5": "Excellent technical knowledge and understanding"
    },
    "Communication Skills": {
        "description": "Ability to articulate thoughts clearly and professionally",
        "1": "Poor communication, difficult to understand",
        "2": "Basic communication with many issues",
        "3": "Adequate communication with some issues",
        "4": "Good communication with minor issues",
        "5": "Excellent communication skills"
    },
    "Problem-Solving Approach": {
        "description": "Logical thinking and systematic approach to problems",
        "1": "No logical approach or problem-solving skills",
        "2": "Weak problem-solving approach",
        "3": "Some logical thinking but incomplete approach",
        "4": "Good problem-solving approach",
        "5": "Excellent systematic problem-solving approach"
    },
    "Experience and Examples": {
        "description": "Use of relevant examples and practical experience",
        "1": "No examples or relevant experience mentioned",
        "2": "Very few or irrelevant examples",
        "3": "Some examples but not very relevant",
        "4": "Good examples with relevant experience",
        "5": "Excellent examples with rich relevant experience"
    }
}

ENHANCED_EVALUATION_PROMPT = """
You are an expert HR evaluator conducting technical and behavioral interviews.

EVALUATE the candidate's answer based on the following criteria (1-5 stars each):

{criteria_text}

QUESTION: "{question}"
CANDIDATE ANSWER: "{answer}"
ANSWER MODE: {mode}
ROLE: {role}
DESIGNATION: {designation}

EVALUATION INSTRUCTIONS:
1. Rate each criterion from 1-5 based on the descriptions provided
2. Consider the role context: {role} - {designation}
3. For audio answers, evaluate based on transcribed content
4. Be fair but thorough in assessment
5. Provide specific, actionable feedback
6. CRITICAL: Check if the candidate's answer actually addresses the specific QUESTION. If the answer is a generic statement (e.g., a general paragraph about "stakeholders" or "communication") that ignores the specific question asked, or if it's completely irrelevant to the question context, you MUST give a score of 1 for all criteria and point this out in the feedback. Do not reward generic, copy-pasted paragraphs if they don't answer the actual prompt.

8. CRITICAL: Evaluate the answer in the context of the requested language: {language}. Make sure your feedback, strengths, improvements, and example answers are written in {language}.

IMPORTANT: Return ONLY valid JSON in this exact format:
{{
  "Relevance and Clarity": <number 1-5>,
  "Technical Knowledge": <number 1-5>,
  "Communication Skills": <number 1-5>,
  "Problem-Solving Approach": <number 1-5>,
  "Experience and Examples": <number 1-5>,
  "Overall Score": <number 1-5>,
  "Strengths": ["strength1", "strength2"],
  "Areas for Improvement": ["improvement1", "improvement2"],
  "Detailed Feedback": "comprehensive feedback explaining the evaluation",
  "Recommendation": "brief recommendation for this candidate",
  "Example Answer": "A model answer demonstrating an optimal way to answer this question in a real interview, showcasing strong structure, technical terminology, and specific examples."
}}

Do not include any other text, only the JSON response.
"""

def clean_answer_text(answer):
    """Clean and normalize answer text for evaluation."""
    if not answer or answer.strip() == "":
        return ""
    
    # Remove extra whitespace and normalize
    cleaned = re.sub(r'\s+', ' ', answer.strip())
    
    # Handle common audio transcription artifacts
    cleaned = re.sub(r'\[.*?\]', '', cleaned)  # Remove [inaudible] type markers
    cleaned = re.sub(r'\(.*?\)', '', cleaned)  # Remove (background noise) type markers
    
    return cleaned

def detect_answer_quality(answer):
    """Detect if answer is too short, meaningless, or contains issues."""
    cleaned = clean_answer_text(answer)
    
    # Check for very short answers
    if len(cleaned) < 10:
        return False, "Answer is too short to evaluate properly"
    
    # Check for meaningless responses
    meaningless_patterns = [
        r'^\s*(i don\'t know|idk|no idea|not sure|maybe|perhaps)\s*$',
        r'^\s*(yes|no)\s*$',
        r'^\s*(ok|okay)\s*$',
        r'^\s*(skip|pass|next)\s*$'
    ]
    
    for pattern in meaningless_patterns:
        if re.match(pattern, cleaned.lower()):
            return False, "Answer is too brief or non-substantive"
    
    # Check for repetitive text
    words = cleaned.split()
    if len(words) > 3:
        unique_words = len(set(words))
        if unique_words / len(words) < 0.3:  # Less than 30% unique words
            return False, "Answer appears to be repetitive or nonsensical"
    
    return True, "Answer appears valid for evaluation"

def build_criteria_text():
    """Build detailed criteria text for the prompt."""
    criteria_text = ""
    for criterion, details in EVALUATION_CRITERIA.items():
        criteria_text += f"\n{criterion}:\n"
        criteria_text += f"Description: {details['description']}\n"
        for score, description in details.items():
            if score.isdigit():
                criteria_text += f"{score} star: {description}\n"
        criteria_text += "\n"
    return criteria_text

def extract_json_from_response(response_text):
    """Extract JSON from AI response, handling various formats."""
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
    except:
        pass
    
    # If no JSON found, try to parse the entire response
    try:
        return json.loads(response_text.strip())
    except:
        return None

def evaluate_answer(question, answer, role="", designation="", mode="text", language="English"):
    """
    Enhanced evaluation of candidate answers using AI.
    
    Args:
        question (str): The interview question
        answer (str): Candidate's answer (text or transcribed audio)
        role (str): Role context (IT/Non-IT)
        designation (str): Specific designation
        mode (str): Answer mode ("text" or "voice")
        language (str): Language for feedback
    
    Returns:
        dict: Comprehensive evaluation results
    """
    
    # Clean and validate answer
    cleaned_answer = clean_answer_text(answer)
    is_valid, validation_message = detect_answer_quality(cleaned_answer)
    
    if not is_valid:
        return {
            "Relevance and Clarity": 1,
            "Technical Knowledge": 1,
            "Communication Skills": 1,
            "Problem-Solving Approach": 1,
            "Experience and Examples": 1,
            "Overall Score": 1,
            "Strengths": [],
            "Areas for Improvement": [validation_message],
            "Detailed Feedback": f"Unable to evaluate: {validation_message}",
            "Recommendation": "Candidate should provide more detailed answers"
        }
    
    try:
        # Build enhanced prompt
        criteria_text = build_criteria_text()
        prompt = ENHANCED_EVALUATION_PROMPT.format(
            criteria_text=criteria_text,
            question=question.strip(),
            answer=cleaned_answer,
            mode=mode,
            role=role or "Professional",
            designation=designation or "Role",
            language=language
        )
        
        # Generate evaluation with retry logic
        success = False
        evaluation = None
        max_retries = 3
        
        if GROQ_ENABLED and client:
            for attempt in range(max_retries):
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        model=MODEL_NAME,
                        temperature=0.3,
                    )
                    response_text = chat_completion.choices[0].message.content.strip()
                    evaluation = extract_json_from_response(response_text)
                    if evaluation and isinstance(evaluation, dict):
                        success = True
                        break
                except Exception as e:
                    print(f"Groq Attempt {attempt + 1} failed: {e}")
                    
        if not success and GEMINI_ENABLED:
            for attempt in range(max_retries):
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    response = model.generate_content(
                        prompt, 
                        generation_config=genai.GenerationConfig(temperature=0.3)
                    )
                    response_text = response.text.strip()
                    evaluation = extract_json_from_response(response_text)
                    if evaluation and isinstance(evaluation, dict):
                        success = True
                        break
                except Exception as e:
                    print(f"Gemini Attempt {attempt + 1} failed: {e}")
        
        if success and evaluation:
            # Validate and normalize scores
            validated_evaluation = {}
            for criterion in EVALUATION_CRITERIA.keys():
                score = evaluation.get(criterion, 1)
                if isinstance(score, (int, float)) and 1 <= score <= 5:
                    validated_evaluation[criterion] = int(score)
                else:
                    validated_evaluation[criterion] = 1
            
            # Calculate overall score
            scores = [validated_evaluation[criterion] for criterion in EVALUATION_CRITERIA.keys()]
            overall_score = sum(scores) / len(scores)
            validated_evaluation["Overall Score"] = round(overall_score, 1)
            
            # Ensure other fields exist
            validated_evaluation["Strengths"] = evaluation.get("Strengths", [])
            validated_evaluation["Areas for Improvement"] = evaluation.get("Areas for Improvement", [])
            validated_evaluation["Detailed Feedback"] = evaluation.get("Detailed Feedback", "Evaluation completed")
            validated_evaluation["Recommendation"] = evaluation.get("Recommendation", "Standard evaluation")
            validated_evaluation["Example Answer"] = evaluation.get("Example Answer", "No example answer provided.")
            
            return validated_evaluation
        else:
            # If all retries failed, return manual evaluation
            return manual_evaluate_answer(question, cleaned_answer, role, designation)
            
    except Exception as e:
        print(f"Evaluation error: {e}")
        # Return manual evaluation for failed cases
        return manual_evaluate_answer(question, cleaned_answer, role, designation)

def manual_evaluate_answer(question, answer, role, designation):
    """Fallback when AI evaluation completely fails (e.g. invalid API key, network error)."""
    return {
        "Relevance and Clarity": 1,
        "Technical Knowledge": 1,
        "Communication Skills": 1,
        "Problem-Solving Approach": 1,
        "Experience and Examples": 1,
        "Overall Score": 1.0,
        "Strengths": [],
        "Areas for Improvement": ["AI Evaluation Service Unavailable"],
        "Detailed Feedback": "The AI evaluation completely failed. This is typically caused by an invalid or missing Groq API key in the .env file. As a result, the answer could not be scored.",
        "Recommendation": "System Administrator: Please verify the GROQ_API_KEY.",
        "Example Answer": "AI Evaluation Service is currently unavailable."
    }

def evaluate_audio_answer(question, transcribed_audio, role="", designation="", language="English"):
    """
    Specialized evaluation for audio answers.
    
    Args:
        question (str): The interview question
        transcribed_audio (str): Transcribed audio content
        role (str): Role context
        designation (str): Specific designation
        language (str): Preferred language
    
    Returns:
        dict: Evaluation results with audio-specific considerations
    """
    
    # Use the main evaluation function with audio mode
    evaluation = evaluate_answer(question, transcribed_audio, role, designation, "voice", language)
    
    # Add audio-specific feedback if needed
    if "Communication Skills" in evaluation:
        comm_score = evaluation["Communication Skills"]
        if comm_score <= 2:
            evaluation["Areas for Improvement"].append("Consider improving voice clarity and confidence in verbal communication")
        elif comm_score >= 4:
            evaluation["Strengths"].append("Good verbal communication skills demonstrated")
    
    return evaluation

# Legacy compatibility function
def evaluate_answer_legacy(question, answer):
    """Legacy function for backward compatibility."""
    return evaluate_answer(question, answer)

def generate_career_advice(evaluations, role, designation, language="English"):
    """
    Generate personalized AI career advice based on the candidate's interview performance.
    """
    if not evaluations:
        return "No evaluations available to generate career advice."
        
    # Summarize the candidate's performance
    strengths = []
    improvements = []
    for ev in evaluations:
        if isinstance(ev, dict):
            strengths.extend(ev.get("strengths", [])[:2])
            improvements.extend(ev.get("improvements", [])[:2])
            
    # Make lists unique
    strengths = list(set(strengths))[:5]
    improvements = list(set(improvements))[:5]
    
    prompt = f"""You are an expert Career Coach and IT/Non-IT Recruiter.
A candidate recently completed an AI interview for the role of {designation} in the {role} field.

Based on their performance, provide a personalized, constructive career advice summary.

Candidate's Demonstrated Strengths:
- {chr(10).join(strengths) if strengths else 'None clearly identified'}

Areas for Improvement (Missed Questions/Concepts):
- {chr(10).join(improvements) if improvements else 'None clearly identified'}

Please provide a 2-3 paragraph career advice summary that includes:
1. An encouraging opening acknowledging their effort.
2. Specific topics, skills, or certifications they should focus on improving based on their weak areas.
3. Actionable next steps for their career progression as a {designation}.

CRITICAL: Your response MUST be in the following language: {language}. Return ONLY the text of the career advice, no JSON, no markdown formatting blocks.
"""

    success = False
    advice = ""
    max_retries = 2
    
    if GROQ_ENABLED and client:
        for attempt in range(max_retries):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=MODEL_NAME,
                    temperature=0.5,
                )
                advice = chat_completion.choices[0].message.content.strip()
                success = True
                break
            except Exception as e:
                print(f"Groq Career advice generation failed on attempt {attempt+1}: {e}")
                
    if not success and GEMINI_ENABLED:
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel('gemini-1.5-pro')
                response = model.generate_content(
                    prompt, 
                    generation_config=genai.GenerationConfig(temperature=0.5)
                )
                advice = response.text.strip()
                success = True
                break
            except Exception as e:
                print(f"Gemini Career advice generation failed on attempt {attempt+1}: {e}")

    if success and advice:
        return advice
        
    return "Unable to generate personalized career advice at this time due to AI service unavailability. However, reviewing standard study materials for your role is always recommended."