"""
Job Matcher Module
Uses sentence embeddings to match resumes with job descriptions.
"""

import numpy as np
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class JobMatcher:
    """
    Semantic job matching using sentence embeddings.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize job matcher with embedding model.
        
        Args:
            model_name: HuggingFace model name for embeddings
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
        
        self.model_name = model_name
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        return self.model.encode(text, convert_to_tensor=False)
    
    def calculate_similarity(self, resume_text: str, job_description: str) -> float:
        """
        Calculate semantic similarity between resume and job description.
        
        Args:
            resume_text: Resume content
            job_description: Job description content
            
        Returns:
            Similarity score (0-1)
        """
        resume_embedding = self.encode_text(resume_text)
        job_embedding = self.encode_text(job_description)
        
        similarity = util.cos_sim(resume_embedding, job_embedding)
        return float(similarity[0][0])
    
    def match_jobs(
        self, 
        resume_text: str, 
        job_descriptions: List[Dict[str, str]], 
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find top matching jobs for a resume.
        
        Args:
            resume_text: Resume content
            job_descriptions: List of job dicts with 'title' and 'description'
            top_k: Number of top matches to return
            
        Returns:
            List of top matching jobs with similarity scores
        """
        if not job_descriptions:
            return []
        
        # Generate resume embedding
        resume_embedding = self.encode_text(resume_text)
        
        # Generate job embeddings
        job_texts = [
            f"{job.get('title', '')} {job.get('description', '')}" 
            for job in job_descriptions
        ]
        job_embeddings = self.model.encode(job_texts, convert_to_tensor=False)
        
        # Calculate similarities
        similarities = util.cos_sim(resume_embedding, job_embeddings)[0]
        
        # Get top k matches
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            idx = int(idx)
            results.append({
                'job': job_descriptions[idx],
                'similarity_score': float(similarities[idx]),
                'match_percentage': float(similarities[idx] * 100),
                'rank': len(results) + 1
            })
        
        return results
    
    def analyze_skill_match(
        self, 
        resume_skills: List[str], 
        required_skills: List[str]
    ) -> Dict:
        """
        Analyze skill matching between resume and requirements.
        
        Args:
            resume_skills: Skills extracted from resume
            required_skills: Required skills from job description
            
        Returns:
            Dictionary with matching analysis
        """
        resume_skills_lower = [s.lower() for s in resume_skills]
        required_skills_lower = [s.lower() for s in required_skills]
        
        # Direct matches
        matching_skills = list(set(resume_skills_lower) & set(required_skills_lower))
        
        # Missing skills
        missing_skills = list(set(required_skills_lower) - set(resume_skills_lower))
        
        # Calculate match percentage
        if required_skills:
            match_percentage = (len(matching_skills) / len(required_skills)) * 100
        else:
            match_percentage = 0.0
        
        # Semantic similarity for non-exact matches
        similar_skills = []
        if missing_skills and resume_skills:
            for req_skill in missing_skills:
                req_embedding = self.encode_text(req_skill)
                for resume_skill in resume_skills_lower:
                    if resume_skill not in matching_skills:
                        skill_embedding = self.encode_text(resume_skill)
                        similarity = util.cos_sim(req_embedding, skill_embedding)[0][0]
                        if similarity > 0.7:  # Threshold for similar skills
                            similar_skills.append({
                                'required': req_skill,
                                'resume_has': resume_skill,
                                'similarity': float(similarity)
                            })
        
        return {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'similar_skills': similar_skills,
            'match_percentage': match_percentage,
            'total_required': len(required_skills),
            'total_matched': len(matching_skills)
        }
    
    def generate_recommendations(
        self, 
        resume_text: str, 
        job_description: str,
        resume_skills: List[str]
    ) -> List[str]:
        """
        Generate recommendations for improving resume for specific job.
        
        Args:
            resume_text: Resume content
            job_description: Target job description
            resume_skills: Extracted skills from resume
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Calculate similarity
        similarity = self.calculate_similarity(resume_text, job_description)
        
        if similarity < 0.3:
            recommendations.append(
                "Consider tailoring your resume more closely to this job description"
            )
        
        # Check resume length
        word_count = len(resume_text.split())
        if word_count < 200:
            recommendations.append(
                "Your resume seems brief. Consider adding more details about your experience and achievements"
            )
        elif word_count > 800:
            recommendations.append(
                "Your resume is quite long. Consider condensing it to focus on most relevant experience"
            )
        
        # Check for quantifiable achievements
        has_numbers = any(char.isdigit() for char in resume_text)
        if not has_numbers:
            recommendations.append(
                "Add quantifiable achievements (e.g., 'Increased sales by 25%', 'Managed team of 10')"
            )
        
        # Check for action verbs
        action_verbs = [
            'led', 'managed', 'developed', 'created', 'implemented', 
            'designed', 'achieved', 'improved', 'increased', 'decreased'
        ]
        has_action_verbs = any(verb in resume_text.lower() for verb in action_verbs)
        if not has_action_verbs:
            recommendations.append(
                "Use strong action verbs to describe your accomplishments (e.g., 'Led', 'Developed', 'Achieved')"
            )
        
        return recommendations if recommendations else [
            "Your resume looks well-structured! Continue to keep it updated with latest achievements."
        ]

