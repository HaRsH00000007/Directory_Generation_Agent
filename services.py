import json
import hashlib
import logging
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
from tinydb import TinyDB, Query
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate_structure(self, prompt: str) -> Optional[str]:
        """Generate response using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software architect that generates project directory structures in JSON format. Always respond with valid JSON only, no additional text or explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None

class CacheService:
    """Service for caching results"""
    
    def __init__(self, cache_db_path: str = "cache.json"):
        self.cache_db = TinyDB(cache_db_path)
    
    def make_cache_key(self, project_desc: str, tech_stack: List[str], prefs: Optional[dict] = None) -> str:
        """Generate a cache key for the given parameters"""
        cache_data = {
            "project_desc": project_desc.lower().strip(),
            "tech_stack": sorted([tech.lower().strip() for tech in tech_stack]),
            "prefs": prefs or {}
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get_cached_structure(self, cache_key: str) -> Optional[Dict]:
        """Get cached structure if exists"""
        QueryObj = Query()
        cached_result = self.cache_db.table('structures').search(QueryObj.cache_key == cache_key)
        return cached_result[0]['structure'] if cached_result else None
    
    def cache_structure(self, cache_key: str, project_id: str, structure: Dict):
        """Cache the structure"""
        self.cache_db.table('structures').insert({
            'cache_key': cache_key,
            'project_id': project_id,
            'structure': structure,
            'timestamp': datetime.now().isoformat()
        })

class SimilarityService:
    """Service for finding similar repositories"""
    
    def __init__(self):
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
            self.sentence_model = None
    
    def find_similar_repos(self, project_desc: str, tech_stack: List[str], example_repos: List[Dict], top_k: int = 2) -> List[Dict]:
        """Find similar repository examples using sentence similarity"""
        if not self.sentence_model:
            return []
        
        try:
            query_text = f"{project_desc} {' '.join(tech_stack)}"
            query_embedding = self.sentence_model.encode([query_text])
            
            similarities = []
            for repo in example_repos:
                repo_text = f"{repo['description']} {' '.join(repo['tech_stack'])}"
                repo_embedding = self.sentence_model.encode([repo_text])
                similarity = np.dot(query_embedding[0], repo_embedding[0]) / (
                    np.linalg.norm(query_embedding[0]) * np.linalg.norm(repo_embedding[0])
                )
                similarities.append((similarity, repo))
            
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [repo for _, repo in similarities[:top_k]]
        
        except Exception as e:
            logger.warning(f"Similarity search failed: {e}")
            return []

class ValidationService:
    """Service for validating directory structures"""
    
    @staticmethod
    def validate_structure(structure: Dict) -> bool:
        """Validate the generated directory structure"""
        if not isinstance(structure, dict):
            return False
        
        if "name" not in structure or "structure" not in structure:
            return False
        
        if not isinstance(structure["structure"], list):
            return False
        
        # Check for required files
        file_names = []
        for item in structure["structure"]:
            if item.get("type") == "file":
                file_names.append(item.get("name", ""))
        
        required_files = ["README.md", ".gitignore"]
        for req_file in required_files:
            if req_file not in file_names:
                logger.warning(f"Missing required file: {req_file}")
                return False
        
        return True