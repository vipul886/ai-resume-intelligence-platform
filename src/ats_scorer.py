"""
ATS Scorer Module
Calculates Applicant Tracking System compatibility scores.
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ATSScorer:
    """
    Calculates ATS compatibility score for resumes.
    """
    
    # Essential resume sections
    ESSENTIAL_SECTIONS = [
        'experience', 'education', 'skills', 'summary', 'contact'
    ]
    
    # ATS-friendly keywords
    COMMON_ATS_KEYWORDS = [
        'experience', 'education', 'skills', 'professional', 'summary',
        'objective', 'achievements', 'responsibilities', 'projects'
    ]
    
    def __init__(self):
        """Initialize ATS scorer."""
        logger.info("ATSScorer initialized")
    
    def calculate_score(
        self, 
        resume_text: str, 
        job_description: str = None,
        parsed_data: Dict = None
    ) -> Dict:
        """
        Calculate comprehensive ATS score.
        
        Args:
            resume_text: Resume content
            job_description: Optional job description for keyword matching
            parsed_data: Optional pre-parsed resume data
            
        Returns:
            Dictionary with scores and breakdown
        """
        scores = {}
        
        # 1. Format Score (30%)
        scores['format'] = self._calculate_format_score(resume_text)
        
        # 2. Section Completeness (25%)
        scores['sections'] = self._calculate_section_score(resume_text)
        
        # 3. Keyword Density (20%)
        scores['keywords'] = self._calculate_keyword_score(resume_text, job_description)
        
        # 4. Content Quality (15%)
        scores['content'] = self._calculate_content_score(resume_text)
        
        # 5. Contact Information (10%)
        scores['contact'] = self._calculate_contact_score(resume_text)
        
        # Calculate weighted overall score
        weights = {
            'format': 0.30,
            'sections': 0.25,
            'keywords': 0.20,
            'content': 0.15,
            'contact': 0.10
        }
        
        overall_score = sum(
            scores[category]['score'] * weights[category] 
            for category in weights
        )
        
        # Generate feedback
        feedback = self._generate_feedback(scores)
        
        return {
            'overall_score': round(overall_score, 1),
            'category_scores': scores,
            'feedback': feedback,
            'grade': self._get_grade(overall_score)
        }
    
    def _calculate_format_score(self, text: str) -> Dict:
        """Calculate formatting score."""
        score = 100
        issues = []
        
        # Check for special characters that confuse ATS
        special_chars = len(re.findall(r'[^\w\s\.,;:()\-@/]', text))
        if special_chars > 50:
            score -= 15
            issues.append("Too many special characters")
        
        # Check for tables/columns (hard for ATS)
        if '\t' in text:
            score -= 10
            issues.append("Contains tabs (may indicate columns)")
        
        # Check line length consistency
        lines = text.split('\n')
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        if avg_line_length < 20:
            score -= 10
            issues.append("Inconsistent line formatting")
        
        # Positive: Clean structure
        if score > 80:
            issues.append("Clean, ATS-friendly formatting")
        
        return {
            'score': max(score, 0),
            'issues': issues
        }
    
    def _calculate_section_score(self, text: str) -> Dict:
        """Calculate section completeness score."""
        found_sections = []
        missing_sections = []
        
        text_lower = text.lower()
        
        for section in self.ESSENTIAL_SECTIONS:
            # Look for section headers
            patterns = [
                f'\n{section}',
                f'\n{section.upper()}',
                f'{section}:',
                f'{section.upper()}:'
            ]
            
            found = any(pattern in text_lower for pattern in patterns)
            
            if found:
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        score = (len(found_sections) / len(self.ESSENTIAL_SECTIONS)) * 100
        
        issues = []
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
        if len(found_sections) == len(self.ESSENTIAL_SECTIONS):
            issues.append("All essential sections present")
        
        return {
            'score': score,
            'found_sections': found_sections,
            'missing_sections': missing_sections,
            'issues': issues
        }
    
    def _calculate_keyword_score(self, text: str, job_description: str = None) -> Dict:
        """Calculate keyword relevance score."""
        text_lower = text.lower()
        found_keywords = []
        
        # Check for common ATS keywords
        for keyword in self.COMMON_ATS_KEYWORDS:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        base_score = (len(found_keywords) / len(self.COMMON_ATS_KEYWORDS)) * 100
        
        issues = []
        
        # If job description provided, check for matching keywords
        if job_description:
            jd_words = set(re.findall(r'\b\w+\b', job_description.lower()))
            jd_words = {w for w in jd_words if len(w) > 4}  # Filter short words
            
            resume_words = set(re.findall(r'\b\w+\b', text_lower))
            
            matching_keywords = jd_words & resume_words
            match_ratio = len(matching_keywords) / max(len(jd_words), 1)
            
            # Adjust score based on JD match
            base_score = (base_score * 0.4) + (match_ratio * 100 * 0.6)
            
            if match_ratio < 0.3:
                issues.append("Low keyword match with job description")
            else:
                issues.append(f"Good keyword match: {len(matching_keywords)} relevant terms")
        else:
            issues.append("Using general ATS keywords (no job description provided)")
        
        return {
            'score': min(base_score, 100),
            'found_keywords': found_keywords,
            'issues': issues
        }
    
    def _calculate_content_score(self, text: str) -> Dict:
        """Calculate content quality score."""
        score = 100
        issues = []
        
        word_count = len(text.split())
        
        # Check word count
        if word_count < 200:
            score -= 30
            issues.append("Resume too short (< 200 words)")
        elif word_count > 1000:
            score -= 15
            issues.append("Resume too long (> 1000 words)")
        else:
            issues.append("Appropriate length")
        
        # Check for numbers (quantifiable achievements)
        numbers = re.findall(r'\d+', text)
        if len(numbers) < 5:
            score -= 20
            issues.append("Add more quantifiable achievements")
        else:
            issues.append("Good use of metrics")
        
        # Check for action verbs
        action_verbs = [
            'led', 'managed', 'developed', 'created', 'implemented',
            'designed', 'achieved', 'improved', 'increased', 'built'
        ]
        verb_count = sum(1 for verb in action_verbs if verb in text.lower())
        
        if verb_count < 3:
            score -= 15
            issues.append("Use more action verbs")
        else:
            issues.append("Strong action verbs present")
        
        return {
            'score': max(score, 0),
            'word_count': word_count,
            'issues': issues
        }
    
    def _calculate_contact_score(self, text: str) -> Dict:
        """Calculate contact information completeness."""
        score = 0
        found_contact = []
        missing_contact = []
        
        # Email
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            score += 40
            found_contact.append('email')
        else:
            missing_contact.append('email')
        
        # Phone
        if re.search(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text):
            score += 30
            found_contact.append('phone')
        else:
            missing_contact.append('phone')
        
        # LinkedIn
        if re.search(r'linkedin\.com/in/', text.lower()):
            score += 20
            found_contact.append('linkedin')
        
        # Location (City, State)
        if re.search(r',\s*[A-Z]{2}\b', text):
            score += 10
            found_contact.append('location')
        
        issues = []
        if missing_contact:
            issues.append(f"Missing: {', '.join(missing_contact)}")
        if score >= 70:
            issues.append("Complete contact information")
        
        return {
            'score': score,
            'found_contact': found_contact,
            'missing_contact': missing_contact,
            'issues': issues
        }
    
    def _generate_feedback(self, scores: Dict) -> List[str]:
        """Generate actionable feedback based on scores."""
        feedback = []
        
        for category, data in scores.items():
            if data['score'] < 60:
                feedback.append(f"⚠️ {category.upper()}: {data['issues'][0] if data['issues'] else 'Needs improvement'}")
            elif data['score'] >= 80:
                feedback.append(f"✅ {category.upper()}: Excellent")
        
        return feedback if feedback else ["Overall good ATS compatibility"]
    
    def _get_grade(self, score: float) -> str:
        """Get letter grade for score."""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

