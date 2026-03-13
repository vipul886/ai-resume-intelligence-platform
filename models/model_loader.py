"""
Model Loader Module
Handles loading and caching of AI models.
"""

import os
import logging
from typing import Optional
from sentence_transformers import SentenceTransformer
import spacy

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton class for loading and caching models.
    """
    
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize model loader."""
        self.cache_dir = os.getenv('MODEL_CACHE_DIR', './model_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def load_sentence_transformer(
        self, 
        model_name: str = "all-MiniLM-L6-v2"
    ) -> SentenceTransformer:
        """
        Load sentence transformer model with caching.
        
        Args:
            model_name: HuggingFace model name
            
        Returns:
            Loaded model
        """
        if model_name in self._models:
            logger.info(f"Using cached model: {model_name}")
            return self._models[model_name]
        
        try:
            logger.info(f"Loading sentence transformer: {model_name}")
            model = SentenceTransformer(model_name, cache_folder=self.cache_dir)
            self._models[model_name] = model
            logger.info(f"Successfully loaded: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def load_spacy_model(self, model_name: str = "en_core_web_sm"):
        """
        Load spaCy model with caching.
        
        Args:
            model_name: spaCy model name
            
        Returns:
            Loaded spaCy model
        """
        if model_name in self._models:
            logger.info(f"Using cached spaCy model: {model_name}")
            return self._models[model_name]
        
        try:
            logger.info(f"Loading spaCy model: {model_name}")
            nlp = spacy.load(model_name)
            self._models[model_name] = nlp
            logger.info(f"Successfully loaded: {model_name}")
            return nlp
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            return None
    
    def clear_cache(self):
        """Clear model cache."""
        self._models.clear()
        logger.info("Model cache cleared")
    
    def get_loaded_models(self):
        """Get list of currently loaded models."""
        return list(self._models.keys())

