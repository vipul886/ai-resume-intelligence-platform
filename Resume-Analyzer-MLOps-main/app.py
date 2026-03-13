# Author: Vipul Kaitke
"""
Gradio Frontend Application
Interactive web interface for Resume Analyzer.
"""

import gradio as gr
import os
import sys
from typing import Tuple
import logging

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.resume_parser import ResumeParser
from src.nlp_processor import NLPProcessor
from src.job_matcher import JobMatcher
from src.ats_scorer import ATSScorer
from src.utils import setup_logging, log_analysis, format_skills_list, load_json

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize components
logger.info("Initializing Resume Analyzer components...")
resume_parser = ResumeParser()
nlp_processor = NLPProcessor()
job_matcher = JobMatcher()
ats_scorer = ATSScorer()

# Load sample job database
try:
    job_database = load_json("data/job_database.json")
    logger.info(f"Loaded {len(job_database.get('jobs', []))} sample jobs")
except:
    job_database = {"jobs": []}
    logger.warning("No job database found")


def analyze_resume(
    resume_file,
    job_description: str = ""
) -> Tuple[str, str, str, str, str]:
    """
    Main analysis function for Gradio interface.
    
    Args:
        resume_file: Uploaded resume file
        job_description: Optional job description
        
    Returns:
        Tuple of (overview, ats_results, skills_results, job_match, recommendations)
    """
    try:
        if resume_file is None:
            return "⚠️ Please upload a resume file", "", "", "", ""
        
        # Parse resume
        logger.info(f"Processing: {resume_file.name}")
        parsed_data = resume_parser.parse_file(resume_file.name)
        resume_text = parsed_data['cleaned_text']
        
        # Extract information
        skills = nlp_processor.extract_skills(resume_text)
        experience_years = nlp_processor.calculate_experience_years(resume_text)
        experiences = nlp_processor.extract_experience(resume_text)
        education = nlp_processor.extract_education(resume_text)
        
        # Calculate ATS score
        ats_results = ats_scorer.calculate_score(resume_text, job_description)
        
        # Build overview with better formatting
        overview = f"""
<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; margin-bottom: 20px;">
    <h1 style="margin: 0; font-size: 28px;">📄 Resume Analysis Complete</h1>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0;">
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea;">
        <h3 style="margin: 0 0 10px 0; color: #667eea;">📋 File Info</h3>
        <p style="margin: 5px 0;"><strong>Name:</strong> {os.path.basename(resume_file.name)}</p>
        <p style="margin: 5px 0;"><strong>Words:</strong> {parsed_data['word_count']}</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #28a745;">
        <h3 style="margin: 0 0 10px 0; color: #28a745;">💼 Experience</h3>
        <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">{experience_years} years</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #ffc107;">
        <h3 style="margin: 0 0 10px 0; color: #ffc107;">🎯 Skills Found</h3>
        <p style="margin: 5px 0; font-size: 24px; font-weight: bold;">{sum(len(s) for s in skills.values())}</p>
    </div>
</div>

<div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 20px 0;">
    <h3 style="color: #333; margin-top: 0;">📧 Contact Information</h3>
"""
        if parsed_data['metadata'].get('emails'):
            overview += f"<p>✉️ <strong>Email:</strong> {parsed_data['metadata']['emails'][0]}</p>"
        if parsed_data['metadata'].get('phones'):
            overview += f"<p>📱 <strong>Phone:</strong> {parsed_data['metadata']['phones'][0]}</p>"
        if parsed_data['metadata'].get('linkedin'):
            overview += f"<p>💼 <strong>LinkedIn:</strong> {parsed_data['metadata']['linkedin']}</p>"
        
        overview += "</div>"
        
        # ATS Score Display with better visuals
        score_color = "#28a745" if ats_results['overall_score'] >= 80 else "#ffc107" if ats_results['overall_score'] >= 60 else "#dc3545"
        
        ats_display = f"""
<div style="padding: 20px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); border-radius: 12px; color: white; margin-bottom: 20px;">
    <h1 style="margin: 0; font-size: 28px;">🎯 ATS Compatibility Analysis</h1>
</div>

<div style="text-align: center; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin: 20px 0;">
    <div style="display: inline-block; position: relative; width: 180px; height: 180px;">
        <svg width="180" height="180" style="transform: rotate(-90deg);">
            <circle cx="90" cy="90" r="70" fill="none" stroke="#e0e0e0" stroke-width="20"/>
            <circle cx="90" cy="90" r="70" fill="none" stroke="{score_color}" stroke-width="20"
                    stroke-dasharray="440" stroke-dashoffset="{440 - (440 * ats_results['overall_score'] / 100)}"
                    stroke-linecap="round"/>
        </svg>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
            <div style="font-size: 42px; font-weight: bold; color: {score_color};">{ats_results['overall_score']}</div>
            <div style="font-size: 14px; color: #666;">out of 100</div>
        </div>
    </div>
    <h2 style="margin: 20px 0 10px 0; color: {score_color};">Grade: {ats_results['grade']}</h2>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 30px 0;">
"""
        
        colors = ['#667eea', '#28a745', '#ffc107', '#17a2b8', '#6c757d']
        for idx, (category, data) in enumerate(ats_results['category_scores'].items()):
            category_name = category.replace('_', ' ').title()
            color = colors[idx % len(colors)]
            ats_display += f"""
    <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-top: 4px solid {color};">
        <h3 style="margin: 0 0 10px 0; color: {color};">{category_name}</h3>
        <div style="font-size: 28px; font-weight: bold; color: #333; margin: 10px 0;">{data['score']:.0f}/100</div>
        <div style="background: #f0f0f0; height: 8px; border-radius: 4px; overflow: hidden; margin: 10px 0;">
            <div style="background: {color}; height: 100%; width: {data['score']}%; transition: width 0.3s;"></div>
        </div>
    </div>
"""
        
        ats_display += "</div>"
        
        ats_display += """
<div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 20px 0;">
    <h3 style="color: #333; margin-top: 0;">💡 Key Recommendations</h3>
    <ul style="list-style: none; padding: 0;">
"""
        for feedback in ats_results['feedback'][:5]:
            icon = "✅" if "Excellent" in feedback or "good" in feedback.lower() else "⚠️"
            ats_display += f"<li style='padding: 8px 0; border-bottom: 1px solid #dee2e6;'>{icon} {feedback}</li>"
        
        ats_display += "</ul></div>"
        
        # Skills Display with badges
        skills_display = f"""
<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 12px; color: white; margin-bottom: 20px;">
    <h1 style="margin: 0; font-size: 28px;">🎯 Skills Portfolio</h1>
    <p style="margin: 10px 0 0 0; opacity: 0.9;">Total: {sum(len(s) for s in skills.values())} skills identified</p>
</div>
"""
        
        if skills:
            skill_colors = {
                'programming': '#667eea',
                'web': '#28a745',
                'data_science': '#ff6b6b',
                'cloud': '#4ecdc4',
                'database': '#ffc107',
                'tools': '#95e1d3',
                'soft_skills': '#c44569'
            }
            
            for category, skill_list in skills.items():
                category_name = category.replace('_', ' ').title()
                color = skill_colors.get(category, '#6c757d')
                
                skills_display += f"""
<div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 15px 0;">
    <h3 style="color: {color}; margin: 0 0 15px 0; padding-bottom: 10px; border-bottom: 2px solid {color};">
        {category_name} ({len(skill_list)})
    </h3>
    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
"""
                for skill in skill_list:
                    skills_display += f"""
        <span style="background: {color}; color: white; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 500;">
            {skill}
        </span>
"""
                skills_display += "</div></div>"
        else:
            skills_display += "<p>No specific skills detected. Consider adding a dedicated skills section.</p>"
        
        # Job Matching with better design
        job_match_display = ""
        recommendations_display = ""
        
        if job_description and job_description.strip():
            similarity = job_matcher.calculate_similarity(resume_text, job_description)
            
            jd_skills = nlp_processor.extract_skills(job_description)
            all_resume_skills = [skill for skills_list in skills.values() for skill in skills_list]
            all_jd_skills = [skill for skills_list in jd_skills.values() for skill in skills_list]
            
            skill_gap = job_matcher.analyze_skill_match(all_resume_skills, all_jd_skills)
            
            match_color = "#28a745" if similarity >= 0.7 else "#ffc107" if similarity >= 0.5 else "#dc3545"
            
            job_match_display = f"""
<div style="padding: 20px; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); border-radius: 12px; color: white; margin-bottom: 20px;">
    <h1 style="margin: 0; font-size: 28px;">🎯 Job Match Analysis</h1>
</div>

<div style="text-align: center; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin: 20px 0;">
    <h2 style="color: #333; margin: 0 0 20px 0;">Match Score</h2>
    <div style="font-size: 52px; font-weight: bold; color: {match_color}; margin: 10px 0;">{similarity * 100:.1f}%</div>
    <p style="color: #666; margin: 10px 0;">Semantic Similarity</p>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
    <div style="background: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
        <h3 style="color: #28a745; margin: 0 0 15px 0;">✅ Matching Skills ({len(skill_gap['matching_skills'])})</h3>
        <div style="max-height: 200px; overflow-y: auto;">
"""
            if skill_gap['matching_skills']:
                for skill in skill_gap['matching_skills'][:15]:
                    job_match_display += f"<span style='display: inline-block; background: #28a745; color: white; padding: 4px 10px; border-radius: 15px; margin: 4px; font-size: 12px;'>{skill}</span>"
            else:
                job_match_display += "<p>None found</p>"
            
            job_match_display += f"""
        </div>
    </div>
    
    <div style="background: #f8d7da; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545;">
        <h3 style="color: #dc3545; margin: 0 0 15px 0;">❌ Missing Skills ({len(skill_gap['missing_skills'])})</h3>
        <div style="max-height: 200px; overflow-y: auto;">
"""
            if skill_gap['missing_skills']:
                for skill in skill_gap['missing_skills'][:15]:
                    job_match_display += f"<span style='display: inline-block; background: #dc3545; color: white; padding: 4px 10px; border-radius: 15px; margin: 4px; font-size: 12px;'>{skill}</span>"
            else:
                job_match_display += "<p>All required skills matched!</p>"
            
            job_match_display += f"""
        </div>
    </div>
</div>

<div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 20px 0;">
    <h3 style="color: #333; margin: 0 0 15px 0;">📊 Skill Coverage</h3>
    <div style="background: #e9ecef; height: 30px; border-radius: 15px; overflow: hidden; position: relative;">
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: {skill_gap['match_percentage']}%; transition: width 0.5s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
            {skill_gap['match_percentage']:.1f}%
        </div>
    </div>
    <p style="color: #666; margin: 10px 0 0 0; font-size: 14px;">
        {skill_gap['total_matched']} out of {skill_gap['total_required']} required skills found
    </p>
</div>
"""
            
            recommendations = job_matcher.generate_recommendations(
                resume_text, job_description, all_resume_skills
            )
            
            recommendations_display = """
<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 12px; color: white; margin-bottom: 20px;">
    <h1 style="margin: 0; font-size: 28px;">💡 Personalized Recommendations</h1>
</div>

<div style="background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
"""
            for i, rec in enumerate(recommendations, 1):
                recommendations_display += f"""
    <div style="padding: 15px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #4facfe; border-radius: 5px;">
        <strong style="color: #4facfe;">{i}.</strong> {rec}
    </div>
"""
            recommendations_display += "</div>"
            
            log_analysis(
                os.path.basename(resume_file.name),
                ats_results['overall_score'],
                similarity
            )
        else:
            job_match_display = """
<div style="text-align: center; padding: 60px 20px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <div style="font-size: 64px; margin-bottom: 20px;">📝</div>
    <h2 style="color: #333; margin: 10px 0;">No Job Description Provided</h2>
    <p style="color: #666; max-width: 500px; margin: 15px auto;">
        Paste a job description above to get personalized matching insights including:
    </p>
    <ul style="list-style: none; padding: 0; color: #666; margin: 20px 0;">
        <li>✅ Match percentage</li>
        <li>📊 Skill gap analysis</li>
        <li>❌ Missing skills</li>
        <li>💡 Tailored recommendations</li>
    </ul>
</div>
"""
            recommendations_display = """
<div style="padding: 25px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <h3 style="color: #333; margin: 0 0 20px 0;">💡 General Best Practices</h3>
    <div style="padding: 15px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #667eea; border-radius: 5px;">
        <strong>1.</strong> Add a job description above for personalized recommendations
    </div>
    <div style="padding: 15px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #28a745; border-radius: 5px;">
        <strong>2.</strong> Ensure your resume has clear sections (Experience, Education, Skills)
    </div>
    <div style="padding: 15px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #ffc107; border-radius: 5px;">
        <strong>3.</strong> Use action verbs and quantifiable achievements
    </div>
    <div style="padding: 15px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #17a2b8; border-radius: 5px;">
        <strong>4.</strong> Keep formatting simple and ATS-friendly
    </div>
</div>
"""
        
        return (
            overview,
            ats_display,
            skills_display,
            job_match_display,
            recommendations_display
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        error_msg = f"""
<div style="padding: 30px; background: #f8d7da; border-radius: 10px; border-left: 5px solid #dc3545; color: #721c24;">
    <h3 style="margin: 0 0 15px 0;">❌ Error</h3>
    <p>{str(e)}</p>
    <p style="margin-top: 15px; font-size: 14px;">Please try again with a different file or contact support.</p>
</div>
"""
        return error_msg, "", "", "", ""


def create_interface():
    """Create and configure Gradio interface."""
    
    # Commercial-Grade CSS
    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    .gradio-container {
        max-width: 1400px !important;
        margin: auto !important;
        padding: 20px !important;
    }
    
    .gr-button-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 16px 48px !important;
        font-size: 18px !important;
        border-radius: 50px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important;
        text-transform: none !important;
    }
    
    .gr-button-primary:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 30px rgba(102, 126, 234, 0.6) !important;
    }
    
    .gr-box {
        border-radius: 16px !important;
        border: none !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1) !important;
        background: white !important;
    }
    
    .gr-input, .gr-textarea {
        border-radius: 12px !important;
        border: 2px solid #e0e0e0 !important;
        transition: all 0.3s !important;
        font-size: 15px !important;
        padding: 12px !important;
    }
    
    .gr-input:focus, .gr-textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15) !important;
        outline: none !important;
    }
    
    .gr-panel {
        border: none !important;
        background: white !important;
        border-radius: 16px !important;
    }
    
    .gr-form {
        background: white !important;
        border-radius: 16px !important;
        padding: 25px !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1) !important;
    }
    
    h1, h2, h3 {
        font-weight: 700 !important;
    }
    
    .tabs {
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1) !important;
        background: white !important;
    }
    
    .tab-nav {
        background: #f8f9fa !important;
        padding: 10px !important;
        border-radius: 12px 12px 0 0 !important;
    }
    
    .tab-nav button {
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        transition: all 0.3s !important;
    }
    
    .tab-nav button:hover {
        background: rgba(102, 126, 234, 0.1) !important;
    }
    
    .tab-nav button[aria-selected="true"] {
        background: white !important;
        border-bottom: 3px solid #667eea !important;
        color: #667eea !important;
    }
    
    .gr-file {
        border: 3px dashed #667eea !important;
        border-radius: 16px !important;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        padding: 30px !important;
        transition: all 0.3s !important;
    }
    
    .gr-file:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3) !important;
    }
    
    label {
        font-weight: 600 !important;
        color: #333 !important;
        font-size: 16px !important;
        margin-bottom: 8px !important;
    }
    
    .gr-compact {
        gap: 20px !important;
    }
    """
    
    with gr.Blocks(css=custom_css, title="AI Resume Analyzer Pro", theme=gr.themes.Soft()) as demo:
        gr.HTML("""
        <div style="text-align: center; padding: 60px 20px; background: rgba(255, 255, 255, 0.95); border-radius: 24px; margin-bottom: 30px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);">
            <div style="font-size: 64px; margin-bottom: 20px;">🚀</div>
            <h1 style="margin: 0; font-size: 56px; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                AI Resume Analyzer Pro
            </h1>
            <p style="font-size: 20px; color: #666; margin: 20px 0 30px 0; font-weight: 500;">
                Transform Your Resume with Advanced AI & Machine Learning
            </p>
            <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; margin-top: 30px;">
                <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border-radius: 25px; font-weight: 600; font-size: 14px; box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);">
                    ✅ ATS Optimization
                </span>
                <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border-radius: 25px; font-weight: 600; font-size: 14px; box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);">
                    🎯 Skills Extraction
                </span>
                <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border-radius: 25px; font-weight: 600; font-size: 14px; box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);">
                    📊 Job Matching
                </span>
                <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 24px; border-radius: 25px; font-weight: 600; font-size: 14px; box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);">
                    💡 AI Recommendations
                </span>
            </div>
        </div>
        """)
        
        gr.HTML("""
        <div style="background: white; border-radius: 24px; padding: 40px; margin-bottom: 30px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);">
            <h2 style="text-align: center; margin-bottom: 30px; color: #333; font-size: 32px;">📤 Upload & Analyze</h2>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                resume_input = gr.File(
                    label="📄 Drop Your Resume Here",
                    file_types=[".pdf", ".docx", ".txt"],
                    type="filepath"
                )
                
                job_desc_input = gr.Textbox(
                    label="💼 Target Job Description (Optional)",
                    placeholder="Paste the job description here for personalized matching and recommendations...\n\nExample:\nWe are seeking a Senior Machine Learning Engineer with 5+ years of experience. Must have strong Python skills, experience with TensorFlow/PyTorch, and knowledge of MLOps practices...",
                    lines=12
                )
                
                analyze_btn = gr.Button(
                    "🔍 Analyze Resume",
                    variant="primary",
                    size="lg",
                    scale=1
                )
                
                gr.HTML("""
                <div style="margin-top: 25px; padding: 25px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 16px; border-left: 5px solid #667eea;">
                    <h4 style="margin: 0 0 15px 0; color: #667eea; font-size: 18px; font-weight: 700;">📝 Quick Tips</h4>
                    <ul style="margin: 0; padding-left: 20px; line-height: 2; color: #555; font-size: 15px;">
                        <li><strong>Supported formats:</strong> PDF, DOCX, TXT (Max 10MB)</li>
                        <li><strong>Job description:</strong> Add for personalized insights</li>
                        <li><strong>Processing time:</strong> Results in ~5 seconds</li>
                        <li><strong>Privacy:</strong> Your data is processed securely</li>
                    </ul>
                </div>
                """)
        
        gr.HTML("""
        <div style="margin: 40px 0;">
            <div style="background: white; border-radius: 24px; padding: 40px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);">
                <h2 style="text-align: center; color: #333; font-size: 32px; margin: 0;">📊 Analysis Results</h2>
            </div>
        </div>
        """)
        
        with gr.Tabs():
            with gr.Tab("📄 Overview"):
                overview_output = gr.HTML()
            
            with gr.Tab("🎯 ATS Score"):
                ats_output = gr.HTML()
            
            with gr.Tab("💼 Skills"):
                skills_output = gr.HTML()
            
            with gr.Tab("🎯 Job Match"):
                job_match_output = gr.HTML()
            
            with gr.Tab("💡 Recommendations"):
                recommendations_output = gr.HTML()
        
        # Set up event handler
        analyze_btn.click(
            fn=analyze_resume,
            inputs=[resume_input, job_desc_input],
            outputs=[
                overview_output,
                ats_output,
                skills_output,
                job_match_output,
                recommendations_output
            ]
        )
        
        gr.HTML("""
        <div style="margin-top: 50px; padding: 40px; background: rgba(255, 255, 255, 0.95); border-radius: 20px; text-align: center; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);">
            <h3 style="margin: 0 0 30px 0; color: #333; font-size: 24px;">🛠️ Built With Enterprise-Grade Technology</h3>
            <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-bottom: 30px;">
                <span style="background: #f8f9fa; padding: 15px 25px; border-radius: 12px; font-weight: 600; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    🤖 Transformers
                </span>
                <span style="background: #f8f9fa; padding: 15px 25px; border-radius: 12px; font-weight: 600; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    🧠 Sentence-BERT
                </span>
                <span style="background: #f8f9fa; padding: 15px 25px; border-radius: 12px; font-weight: 600; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    ⚡ FastAPI
                </span>
                <span style="background: #f8f9fa; padding: 15px 25px; border-radius: 12px; font-weight: 600; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    🎨 Gradio
                </span>
                <span style="background: #f8f9fa; padding: 15px 25px; border-radius: 12px; font-weight: 600; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    🐍 Python
                </span>
                <span style="background: #f8f9fa; padding: 15px 25px; border-radius: 12px; font-weight: 600; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    🐳 Docker
                </span>
            </div>
            <p style="color: #666; margin: 15px 0 5px 0; font-size: 15px;">
                Made with ❤️ using MLOps best practices • Deployed on HuggingFace Spaces
            </p>
            <p style="color: #999; margin: 5px 0 0 0; font-size: 13px;">
                © 2025 AI Resume Analyzer Pro. All rights reserved.
            </p>
        </div>
        """)
    
    return demo


if __name__ == "__main__":
    logger.info("Starting Gradio application...")
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
