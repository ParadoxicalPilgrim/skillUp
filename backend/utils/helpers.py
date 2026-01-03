import re
import fitz
import logging
from fastapi import HTTPException
from typing import List

logger = logging.getLogger(__name__)

# Enhanced PDF text extraction
def extract_text_from_pdf(file_content):
    try:
        with fitz.open(stream=file_content, filetype="pdf") as pdf:
            text_parts = []
            for page_num, page in enumerate(pdf):
                if page_num >= 3:  # Limit to first 3 pages
                    break
                page_text = page.get_text("text")
                if page_text.strip():
                    text_parts.append(page_text)
            
            full_text = "\n".join(text_parts)
            # Clean up the text
            full_text = re.sub(r'\n+', '\n', full_text)
            full_text = re.sub(r'\s+', ' ', full_text)
            
            return full_text[:4000]  # Increased limit for better analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

def clean_gemini_response(text):
    """Clean and format Gemini API response"""
    # Remove markdown formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def get_fallback_courses(job_title: str) -> List[dict]:
    """Provide curated fallback courses based on job title"""
    job_lower = job_title.lower()
    
    # Job-specific course mappings
    course_mappings = {
        "software engineer": [
            {"title": "Full Stack Web Development", "link": "https://www.freecodecamp.org/learn/", "platform": "FreeCodeCamp", "isFree": True},
            {"title": "Software Engineering Fundamentals", "link": "https://www.coursera.org/specializations/software-engineering", "platform": "Coursera", "isFree": False},
        ],
        "data scientist": [
            {"title": "Data Science Fundamentals", "link": "https://www.kaggle.com/learn", "platform": "Kaggle Learn", "isFree": True},
            {"title": "Python for Data Science", "link": "https://www.coursera.org/specializations/python", "platform": "Coursera", "isFree": False},
        ],
        "web developer": [
            {"title": "Responsive Web Design", "link": "https://www.freecodecamp.org/learn/responsive-web-design/", "platform": "FreeCodeCamp", "isFree": True},
            {"title": "JavaScript Algorithms and Data Structures", "link": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "platform": "FreeCodeCamp", "isFree": True},
        ]
    }
    
    # Find matching courses
    for key, courses in course_mappings.items():
        if key in job_lower:
            return [
                {
                    **course,
                    "snippet": f"Learn essential skills for {job_title} with this comprehensive course"
                }
                for course in courses
            ]
    
    # Generic fallback
    return [
        {
            "title": f"{job_title} Fundamentals",
            "link": "https://www.coursera.org/",
            "snippet": f"Learn the fundamentals of {job_title} with expert instruction",
            "platform": "Coursera",
            "isFree": False
        },
        {
            "title": f"Introduction to {job_title}",
            "link": "https://www.edx.org/",
            "snippet": f"Get started with {job_title} through this introductory course",
            "platform": "edX",
            "isFree": True
        }
    ]
