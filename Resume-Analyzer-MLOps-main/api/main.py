"""
FastAPI Backend
Main API endpoints for Resume Analyzer.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import tempfile
import logging

from src.resume_parser import ResumeParser
from src.nlp_processor import NLPProcessor
from src.job_matcher import JobMatcher
from src.ats_scorer import ATSScorer
from src.utils import setup_logging, log_analysis, validate_file_upload

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Analyzer API",
    description="AI-powered resume analysis and job matching API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
resume_parser = ResumeParser()
nlp_processor = NLPProcessor()
job_matcher = JobMatcher()
ats_scorer = ATSScorer()

logger.info("FastAPI application initialized")


# Pydantic models
class AnalysisResponse(BaseModel):
    success: bool
    data: dict
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    """
    Analyze uploaded resume.
    
    Args:
        file: Resume file (PDF, DOCX, or TXT)
        job_description: Optional job description for matching
        
    Returns:
        Analysis results including ATS score, skills, and matches
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Validate file
        validate_file_upload(tmp_file_path)
        
        # Parse resume
        logger.info(f"Parsing resume: {file.filename}")
        parsed_data = resume_parser.parse_file(tmp_file_path)
        resume_text = parsed_data['cleaned_text']
        
        # Extract skills
        logger.info("Extracting skills")
        skills = nlp_processor.extract_skills(resume_text)
        
        # Extract experience
        experiences = nlp_processor.extract_experience(resume_text)
        experience_years = nlp_processor.calculate_experience_years(resume_text)
        
        # Extract education
        education = nlp_processor.extract_education(resume_text)
        
        # Calculate ATS score
        logger.info("Calculating ATS score")
        ats_score = ats_scorer.calculate_score(resume_text, job_description)
        
        # Job matching (if job description provided)
        job_matches = None
        skill_gap = None
        
        if job_description:
            logger.info("Performing job matching")
            similarity = job_matcher.calculate_similarity(resume_text, job_description)
            
            # Extract skills from job description
            jd_skills = nlp_processor.extract_skills(job_description)
            all_resume_skills = [skill for skills_list in skills.values() for skill in skills_list]
            all_jd_skills = [skill for skills_list in jd_skills.values() for skill in skills_list]
            
            # Skill gap analysis
            skill_gap = job_matcher.analyze_skill_match(all_resume_skills, all_jd_skills)
            
            # Generate recommendations
            recommendations = job_matcher.generate_recommendations(
                resume_text, job_description, all_resume_skills
            )
            
            job_matches = {
                'similarity_score': similarity,
                'match_percentage': similarity * 100,
                'recommendations': recommendations
            }
        
        # Log analysis
        log_analysis(
            file.filename,
            ats_score['overall_score'],
            job_matches['similarity_score'] if job_matches else None
        )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        # Prepare response
        response_data = {
            'file_name': file.filename,
            'metadata': parsed_data['metadata'],
            'word_count': parsed_data['word_count'],
            'skills': skills,
            'experience_years': experience_years,
            'experiences': experiences[:3],  # Limit to top 3
            'education': education,
            'ats_score': ats_score,
            'job_match': job_matches,
            'skill_gap': skill_gap
        }
        
        return {
            'success': True,
            'data': response_data,
            'message': 'Analysis completed successfully'
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/match-jobs")
async def match_jobs(
    file: UploadFile = File(...),
    job_titles: List[str] = Form(...)
):
    """
    Match resume against multiple job titles.
    
    Args:
        file: Resume file
        job_titles: List of job titles to match against
        
    Returns:
        Ranked list of job matches
    """
    try:
        # Save and parse resume
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        parsed_data = resume_parser.parse_file(tmp_file_path)
        resume_text = parsed_data['cleaned_text']
        
        # Create job descriptions from titles
        jobs = [{'title': title, 'description': title} for title in job_titles]
        
        # Match jobs
        matches = job_matcher.match_jobs(resume_text, jobs, top_k=len(jobs))
        
        # Clean up
        os.unlink(tmp_file_path)
        
        return {
            'success': True,
            'data': {
                'matches': matches
            },
            'message': 'Job matching completed'
        }
        
    except Exception as e:
        logger.error(f"Job matching failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get API usage statistics."""
    try:
        # Read analysis logs
        log_file = "logs/analysis_log.jsonl"
        if not os.path.exists(log_file):
            return {
                'success': True,
                'data': {
                    'total_analyses': 0,
                    'average_ats_score': 0
                },
                'message': 'No analyses yet'
            }
        
        import json
        analyses = []
        with open(log_file, 'r') as f:
            for line in f:
                analyses.append(json.loads(line))
        
        total = len(analyses)
        avg_ats = sum(a['ats_score'] for a in analyses) / total if total > 0 else 0
        
        return {
            'success': True,
            'data': {
                'total_analyses': total,
                'average_ats_score': round(avg_ats, 2)
            },
            'message': 'Statistics retrieved'
        }
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

