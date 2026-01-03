import logging
import requests
import time
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from models.schemas import SkillsRequest
from utils.helpers import (
    extract_text_from_pdf, 
    clean_gemini_response, 
    get_fallback_courses
)
from config.settings import (
    GEMINI_API_KEY, 
    GOOGLE_API_KEY, 
    YOUTUBE_API_KEY, 
    SEARCH_ENGINE_ID
)
from prompts.prompts import (
    RESUME_ANALYSIS_PROMPT, 
    JOB_MATCHING_PROMPT, 
    PROJECT_GENERATOR_PROMPT
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Health check endpoint
@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "gemini_api": "configured" if GEMINI_API_KEY else "not_configured",
            "google_api": "configured" if GOOGLE_API_KEY else "not_configured",
            "youtube_api": "configured" if YOUTUBE_API_KEY else "not_configured"
        }
    }

@router.get("/")
def home():
    return {
        "message": "Skill Gap Analyzer API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "analyze_resume": "/analyze_resume/",
            "fetch_courses": "/fetch_courses/{job_title}",
            "youtube_courses": "/youtube-courses/{job_title}",
            "job_matching": "/job_matching/",
            "project_generator": "/project_generator/"
        }
    }

@router.post("/analyze_resume/")
async def analyze_resume(file: UploadFile = File(...), job_title: str = Form(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Validate file size (10MB limit)
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
        
        # Validate job title
        if not job_title or len(job_title.strip()) < 2:
            raise HTTPException(status_code=400, detail="Valid job title is required")
        
        extracted_text = extract_text_from_pdf(file_content)
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        # Enhanced prompt for better skill gap analysis
        prompt_text = RESUME_ANALYSIS_PROMPT.format(
            job_title=job_title, 
            extracted_text=extracted_text
        )
        
        prompt = {
            "contents": [{"parts": [{"text": prompt_text}]}]
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, headers=headers, json=prompt, timeout=30)

        if response.status_code == 200:
            response_json = response.json()
            
            if "candidates" in response_json and response_json["candidates"]:
                skill_gap = response_json["candidates"][0]["content"]["parts"][0]["text"]
                skill_gap = clean_gemini_response(skill_gap)
            else:
                skill_gap = "- No specific missing skills identified\n- Consider reviewing job requirements for additional skills"

        else:
            logger.error(f"Gemini API error: {response.text}")
            skill_gap = "- Unable to analyze resume at this time\n- Please try again later"

        # IMPORTANT: Return both missing skills AND extracted text
        return {
            "missing_skills": skill_gap,
            "extracted_text": extracted_text,  # This is crucial for job matching
            "job_title": job_title,
            "analysis_timestamp": datetime.now().isoformat(),
            "resume_length": len(extracted_text)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze resume")

@router.get("/fetch_courses/{job_title}")
def fetch_courses(job_title: str):
    try:
        if not job_title or len(job_title.strip()) < 2:
            raise HTTPException(status_code=400, detail="Valid job title is required")
        
        # Enhanced search queries for better results
        search_queries = [
            f"{job_title} course certification",
            f"{job_title} training program",
            f"learn {job_title} skills online"
        ]
        
        all_courses = []
        
        for query in search_queries:
            try:
                # Search for courses
                search_url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": GOOGLE_API_KEY,
                    "cx": SEARCH_ENGINE_ID,
                    "q": query,
                    "num": 3,
                    "safe": "active"
                }

                response = requests.get(search_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "items" in data:
                        for item in data["items"]:
                            link = item.get("link", "")
                            title = item.get("title", "")
                            
                            # Filter for educational platforms
                            if any(platform in link.lower() for platform in [
                                "coursera.org", "udemy.com", "edx.org", "pluralsight.com",
                                "linkedin.com/learning", "skillshare.com", "udacity.com",
                                "codecademy.com", "freecodecamp.org"
                            ]):
                                platform = "Unknown"
                                if "coursera.org" in link:
                                    platform = "Coursera"
                                elif "udemy.com" in link:
                                    platform = "Udemy"
                                elif "edx.org" in link:
                                    platform = "edX"
                                elif "pluralsight.com" in link:
                                    platform = "Pluralsight"
                                elif "linkedin.com/learning" in link:
                                    platform = "LinkedIn Learning"
                                elif "skillshare.com" in link:
                                    platform = "Skillshare"
                                elif "udacity.com" in link:
                                    platform = "Udacity"
                                elif "codecademy.com" in link:
                                    platform = "Codecademy"
                                elif "freecodecamp.org" in link:
                                    platform = "FreeCodeCamp"
                                
                                course = {
                                    "title": title,
                                    "link": link,
                                    "snippet": item.get("snippet", f"Learn {job_title} skills with this comprehensive course"),
                                    "platform": platform,
                                    "isFree": platform in ["FreeCodeCamp", "edX"] or "free" in title.lower()
                                }
                                
                                # Avoid duplicates
                                if not any(existing["link"] == course["link"] for existing in all_courses):
                                    all_courses.append(course)
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Search query failed for '{query}': {str(e)}")
                continue
        
        # If no results found, provide curated fallback courses
        if not all_courses:
            all_courses = get_fallback_courses(job_title)
        
        # Limit to 8 courses and prioritize free ones
        all_courses = sorted(all_courses, key=lambda x: (not x.get("isFree", False), x["title"]))[:8]
        
        return {
            "courses": all_courses,
            "job_title": job_title,
            "total_found": len(all_courses),
            "search_timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course fetch error: {str(e)}")
        return {
            "courses": get_fallback_courses(job_title),
            "job_title": job_title,
            "total_found": 0,
            "error": "Using fallback courses due to API limitations"
        }

@router.get("/youtube-courses/{job_title}")
def get_youtube_courses(job_title: str):
    try:
        if not job_title or len(job_title.strip()) < 2:
            raise HTTPException(status_code=400, detail="Valid job title is required")
        
        # Enhanced search query for better YouTube results
        search_query = f"{job_title} tutorial course 2024"
        youtube_url = f"https://www.googleapis.com/youtube/v3/search"
        
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "key": YOUTUBE_API_KEY,
            "maxResults": 12,
            "order": "relevance",
            "videoDuration": "medium",  # Filter for substantial content
            "safeSearch": "strict"
        }

        response = requests.get(youtube_url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"YouTube API error: {response.text}")
            return {
                "videos": [],
                "job_title": job_title,
                "error": "YouTube API temporarily unavailable"
            }
        
        data = response.json()

        if "items" not in data or not data["items"]:
            return {
                "videos": [],
                "job_title": job_title,
                "message": f"No YouTube videos found for {job_title}"
            }

        videos = []
        for item in data.get("items", []):
            if "videoId" in item["id"]:
                video = {
                    "title": item["snippet"]["title"],
                    "video_id": item["id"]["videoId"],
                    "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                    "channel": item["snippet"]["channelTitle"],
                    "description": item["snippet"]["description"][:200] + "..." if len(item["snippet"]["description"]) > 200 else item["snippet"]["description"],
                    "published_at": item["snippet"]["publishedAt"],
                    "link": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                videos.append(video)

        return {
            "videos": videos,
            "job_title": job_title,
            "total_found": len(videos),
            "search_timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube fetch error: {str(e)}")
        return {
            "videos": [],
            "job_title": job_title,
            "error": f"Failed to fetch YouTube videos: {str(e)}"
        }

# FIXED: Job Matching Endpoint - Only the job matching part
@router.post("/job_matching/")
async def job_matching(request: dict):
    try:
        # Extract data from request
        skills = request.get("skills", [])
        job_title = request.get("job_title", "")
        extracted_text = request.get("extracted_text", "")
        
        # Validate inputs
        if not skills or len(skills) == 0:
            raise HTTPException(status_code=400, detail="Skills list cannot be empty")
        if not job_title or len(job_title.strip()) < 2:
            raise HTTPException(status_code=400, detail="Valid job title is required")
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Extracted text is required")
        
        # FIXED: Remove hardcoded examples and let AI generate unique recommendations
        prompt_text = JOB_MATCHING_PROMPT.format(
            extracted_text=extracted_text,
            skills_str=", ".join(skills),
            job_title=job_title
        )
        
        prompt = {
            "contents": [{"parts": [{"text": prompt_text}]}]
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}

        # Log the request for debugging
        logger.info(f"Sending job matching request for job title: {job_title}")

        response = requests.post(url, headers=headers, json=prompt, timeout=30)

        if response.status_code == 200:
            response_json = response.json()
            
            if "candidates" in response_json and response_json["candidates"]:
                job_recommendations = response_json["candidates"][0]["content"]["parts"][0]["text"]
                job_recommendations = clean_gemini_response(job_recommendations)
                
                # Log the response for debugging
                logger.info(f"Job recommendations generated successfully. Length: {len(job_recommendations)}")
                
            else:
                logger.warning("No candidates in Gemini response")
                job_recommendations = "Unable to generate job recommendations at this time. Please try again."

        else:
            logger.error(f"Gemini API error: Status {response.status_code}, Response: {response.text}")
            job_recommendations = "Unable to generate job recommendations due to API error. Please try again."

        return {
            "job_recommendations": job_recommendations,
            "skills_analyzed": skills,
            "job_title": job_title,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_skills": len(skills)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job matching error: {str(e)}")
        return {
            "job_recommendations": "Unable to generate job recommendations due to system error. Please try again.",
            "error": str(e)
        }

@router.post("/project_generator/")
async def project_generator(request: SkillsRequest):
    try:
        skills = request.skills
        
        # Enhanced prompt for API to generate creative project ideas
        prompt_text = PROJECT_GENERATOR_PROMPT.format(
            skills_str=", ".join(skills)
        )
        
        prompt = {
            "contents": [{"parts": [{"text": prompt_text}]}]
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, headers=headers, json=prompt, timeout=30)

        if response.status_code == 200:
            response_json = response.json()
            
            if "candidates" in response_json and response_json["candidates"]:
                project_ideas = response_json["candidates"][0]["content"]["parts"][0]["text"]
                project_ideas = clean_gemini_response(project_ideas)
            else:
                # Only use fallback if API response is empty
                project_ideas = "Unable to generate project ideas at this time. Please try again."

        else:
            logger.error(f"Gemini API error: {response.text}")
            project_ideas = "Unable to generate project ideas due to API error. Please try again."

        return {
            "project_ideas": project_ideas,
            "skills_analyzed": skills,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_skills": len(skills)
        }

    except Exception as e:
        logger.error(f"Project generation error: {str(e)}")
        return {
            "project_ideas": "Unable to generate project ideas due to system error. Please try again.",
            "error": str(e)
        }
