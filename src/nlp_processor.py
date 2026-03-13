"""
NLP Processor Module
Handles natural language processing tasks including skill extraction,
entity recognition, and text analysis.
"""

import re
import spacy
from typing import List, Dict, Set, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class NLPProcessor:
    """
    Advanced NLP processor for resume analysis using spaCy and transformers.
    """
    
    # Comprehensive skill database
    TECH_SKILLS = {
        'programming': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go',
            'rust', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'bash'
        ],
        'web': [
            'html', 'css', 'react', 'angular', 'vue.js', 'node.js', 'express',
            'django', 'flask', 'fastapi', 'spring', 'asp.net', 'jquery'
        ],
        'data_science': [
            'machine learning', 'deep learning', 'neural networks', 'nlp',
            'computer vision', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'data analysis',
            'statistical analysis', 'predictive modeling'
        ],
        'cloud': [
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
            'terraform', 'jenkins', 'ci/cd', 'devops', 'lambda', 's3', 'ec2'
        ],
        'database': [
            'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'dynamodb',
            'oracle', 'sql server', 'sqlite', 'elasticsearch'
        ],
        'tools': [
            'git', 'github', 'gitlab', 'jira', 'confluence', 'slack', 'linux',
            'windows', 'macos', 'vscode', 'jupyter', 'postman'
        ],
        'soft_skills': [
            'leadership', 'communication', 'teamwork', 'problem solving',
            'critical thinking', 'project management', 'agile', 'scrum',
            'collaboration', 'presentation', 'negotiation'
        ]
    }
    
    def __init__(self, use_gpu: bool = False):
        """Initialize NLP processor with models."""
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except Exception as e:
            logger.warning(f"spaCy model not available: {e}. Using fallback methods.")
            self.nlp = None
        
        self.all_skills = []
        for category, skills in self.TECH_SKILLS.items():
            self.all_skills.extend(skills)
        
        logger.info("NLPProcessor initialized")
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical and soft skills from text."""
        text_lower = text.lower()
        found_skills = {}
        
        for category, skills in self.TECH_SKILLS.items():
            found = []
            for skill in skills:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    found.append(skill)
            
            if found:
                found_skills[category] = found
        
        return found_skills
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy."""
        if not self.nlp:
            return {}
        
        doc = self.nlp(text)
        entities = {}
        
        for ent in doc.ents:
            entity_type = ent.label_
            if entity_type not in entities:
                entities[entity_type] = []
            entities[entity_type].append(ent.text)
        
        return {k: list(set(v)) for k, v in entities.items()}
    
    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience entries from text."""
        experiences = []
        date_pattern = r'(\d{4}|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})'
        
        exp_section = self._find_section(text, ['experience', 'employment', 'work history'])
        if not exp_section:
            return experiences
        
        lines = exp_section.split('\n')
        current_entry = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    experiences.append(current_entry)
                    current_entry = {}
                continue
            
            dates = re.findall(date_pattern, line, re.IGNORECASE)
            if dates and len(dates) >= 1:
                if current_entry:
                    experiences.append(current_entry)
                current_entry = {
                    'raw_text': line,
                    'dates': dates,
                    'description': []
                }
            elif current_entry:
                current_entry['description'].append(line)
        
        if current_entry:
            experiences.append(current_entry)
        
        return experiences
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information."""
        education = []
        degree_patterns = [
            r'\b(bachelor|b\.s\.|b\.a\.|bs|ba|undergraduate)\b',
            r'\b(master|m\.s\.|m\.a\.|ms|ma|mba|graduate)\b',
            r'\b(phd|ph\.d\.|doctorate|doctoral)\b',
            r'\b(associate|a\.s\.|a\.a\.)\b'
        ]
        
        edu_section = self._find_section(text, ['education', 'academic'])
        if not edu_section:
            return education
        
        lines = edu_section.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in degree_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    education.append({'raw_text': line, 'degree_mentioned': True})
                    break
        
        return education
    
    def _find_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """Find a section in text based on keywords."""
        text_lower = text.lower()
        
        for keyword in keywords:
            pattern = r'\b' + keyword + r'\b.*?(?=\n[A-Z]{2,}|\Z)'
            match = re.search(pattern, text_lower, re.DOTALL)
            if match:
                start = match.start()
                next_section = re.search(r'\n[A-Z\s]{10,}\n', text[start + 50:])
                end = start + 50 + next_section.start() if next_section else len(text)
                return text[start:end]
        
        return None
    
    def calculate_experience_years(self, text: str) -> float:
        """Estimate total years of experience from text."""
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        years = [int(y) for y in years]
        
        if len(years) < 2:
            return 0.0
        
        min_year = min(years)
        max_year = max(years)
        experience_years = max_year - min_year
        
        return min(experience_years, 50)
    
    def extract_keywords(self, text: str, top_n: int = 20) -> List[tuple]:
        """Extract top keywords from text."""
        if not self.nlp:
            words = re.findall(r'\b\w+\b', text.lower())
            common_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'])
            words = [w for w in words if w not in common_words and len(w) > 3]
            return Counter(words).most_common(top_n)
        
        doc = self.nlp(text)
        important_tokens = [
            token.lemma_.lower() 
            for token in doc 
            if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] 
            and not token.is_stop 
            and len(token.text) > 2
        ]
        
        return Counter(important_tokens).most_common(top_n)

