import os
import hashlib
import logging
from typing import Dict, List, Optional
from datetime import datetime

from models import ProjectPreferences, get_example_repos
from services import LLMService, CacheService, SimilarityService, ValidationService
from utils import parse_llm_output, apply_preferences, build_prompt, structure_to_tree

logger = logging.getLogger(__name__)

class DirectoryStructureAgent:
    """
    Agent that suggests standardized project directory structures based on
    project description, tech stack, team roles, and best practices.
    """
    
    def __init__(self, openai_api_key: str, cache_db_path: str = "cache.json"):
        """
        Initialize the DirectoryStructureAgent
        
        Args:
            openai_api_key: OpenAI API key for LLM inference
            cache_db_path: Path to cache database file
        """
        self.llm_service = LLMService(openai_api_key)
        self.cache_service = CacheService(cache_db_path)
        self.similarity_service = SimilarityService()
        self.validation_service = ValidationService()
        self.example_repos = get_example_repos()
    
    def suggest_structure(self, project_id: str, project_desc: str, 
                         tech_stack: List[str], prefs: Optional[ProjectPreferences] = None) -> Optional[Dict]:
        """
        Main method to suggest project directory structure
        
        Args:
            project_id: Unique identifier for the project
            project_desc: Description of the project
            tech_stack: List of technologies used in the project
            prefs: Optional preferences for the structure
            
        Returns:
            Dictionary containing the suggested directory structure
        """
        try:
            # Check cache first
            cache_key = self.cache_service.make_cache_key(
                project_desc, tech_stack, prefs.__dict__ if prefs else None
            )
            
            cached_result = self.cache_service.get_cached_structure(cache_key)
            if cached_result:
                logger.info("Returning cached result")
                return cached_result
            
            # Find similar repositories
            similar_repos = self.similarity_service.find_similar_repos(
                project_desc, tech_stack, self.example_repos
            )
            
            # Build prompt
            prompt = build_prompt(project_desc, tech_stack, prefs, similar_repos)
            
            # Generate structure using OpenAI
            llm_response = self.llm_service.generate_structure(prompt)
            if not llm_response:
                logger.error("Failed to get response from OpenAI")
                return None
            
            # Parse LLM output
            structure = parse_llm_output(llm_response)
            if not structure:
                logger.error("Failed to parse LLM output")
                return None
            
            # Validate structure
            if not self.validation_service.validate_structure(structure):
                logger.error("Generated structure is invalid")
                return None
            
            # Apply preferences
            structure = apply_preferences(structure, prefs)
            
            # Cache the result
            self.cache_service.cache_structure(cache_key, project_id, structure)
            
            return structure
            
        except Exception as e:
            logger.error(f"Error in suggest_structure: {e}")
            return None
    
    def structure_to_tree(self, structure: Dict) -> str:
        """Convert JSON structure to text tree representation"""
        return structure_to_tree(structure)