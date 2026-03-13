"""
Utility Functions
Helper functions for the Resume Analyzer system.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging(log_file: str = "logs/app.log", level: str = "INFO"):
    """
    Setup logging configuration.
    
    Args:
        log_file: Path to log file
        level: Logging level
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger.info("Logging initialized")


def save_json(data: Dict, filepath: str):
    """
    Save data to JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Output file path
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved data to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        raise


def load_json(filepath: str) -> Dict:
    """
    Load data from JSON file.
    
    Args:
        filepath: Input file path
        
    Returns:
        Loaded dictionary
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded data from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Failed to load JSON: {e}")
        raise


def generate_file_hash(filepath: str) -> str:
    """
    Generate MD5 hash of file.
    
    Args:
        filepath: Path to file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def log_analysis(
    resume_name: str, 
    ats_score: float, 
    match_score: float = None,
    log_file: str = "logs/analysis_log.jsonl"
):
    """
    Log analysis results for monitoring.
    
    Args:
        resume_name: Name of resume file
        ats_score: ATS compatibility score
        match_score: Job match score (optional)
        log_file: Path to log file
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'resume_name': resume_name,
        'ats_score': ats_score,
        'match_score': match_score,
    }
    
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"Failed to log analysis: {e}")


def format_skills_list(skills_dict: Dict[str, List[str]]) -> str:
    """
    Format skills dictionary into readable string.
    
    Args:
        skills_dict: Dictionary of categorized skills
        
    Returns:
        Formatted string
    """
    formatted = []
    for category, skills in skills_dict.items():
        category_name = category.replace('_', ' ').title()
        skills_str = ', '.join(skills)
        formatted.append(f"**{category_name}**: {skills_str}")
    
    return '\n'.join(formatted)


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'


def validate_file_upload(file_path: str, max_size_mb: int = 10) -> bool:
    """
    Validate uploaded file.
    
    Args:
        file_path: Path to file
        max_size_mb: Maximum file size in MB
        
    Returns:
        True if valid, raises exception otherwise
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Check file size
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"File too large: {file_size_mb:.1f}MB (max: {max_size_mb}MB)")
    
    # Check file extension
    valid_extensions = ['.pdf', '.docx', '.txt']
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in valid_extensions:
        raise ValueError(f"Invalid file type: {file_ext}")
    
    return True


def create_result_summary(analysis_results: Dict) -> str:
    """
    Create a summary of analysis results.
    
    Args:
        analysis_results: Complete analysis dictionary
        
    Returns:
        Formatted summary string
    """
    summary_parts = []
    
    # ATS Score
    if 'ats_score' in analysis_results:
        ats = analysis_results['ats_score']
        summary_parts.append(
            f"📊 **ATS Score**: {ats.get('overall_score', 0)}/100 "
            f"(Grade: {ats.get('grade', 'N/A')})"
        )
    
    # Skills
    if 'skills' in analysis_results:
        total_skills = sum(
            len(skills) for skills in analysis_results['skills'].values()
        )
        summary_parts.append(f"🎯 **Skills Found**: {total_skills}")
    
    # Experience
    if 'experience_years' in analysis_results:
        summary_parts.append(
            f"💼 **Experience**: ~{analysis_results['experience_years']} years"
        )
    
    # Job Matches
    if 'job_matches' in analysis_results and analysis_results['job_matches']:
        top_match = analysis_results['job_matches'][0]
        summary_parts.append(
            f"🎯 **Top Match**: {top_match['job']['title']} "
            f"({top_match['match_percentage']:.0f}% match)"
        )
    
    return '\n'.join(summary_parts)


def get_timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def ensure_dir(directory: str):
    """Ensure directory exists."""
    Path(directory).mkdir(parents=True, exist_ok=True)

