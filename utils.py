import json
import re
import logging
from typing import Dict, List, Optional
from models import ProjectPreferences

logger = logging.getLogger(__name__)

def parse_llm_output(llm_response: str) -> Optional[Dict]:
    """Parse the LLM output to extract JSON structure"""
    try:
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            return json.loads(llm_response.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM output as JSON: {e}")
        return None

def apply_preferences(structure: Dict, prefs: Optional[ProjectPreferences]) -> Dict:
    """Apply user preferences to the structure"""
    if not prefs:
        return structure
    
    structure_list = structure["structure"]
    
    # Add custom folders
    for custom_folder in prefs.custom_folders:
        if not any(item.get("name") == custom_folder for item in structure_list):
            structure_list.append({
                "type": "folder",
                "name": custom_folder,
                "children": []
            })
    
    # Add Docker support
    if prefs.include_docker:
        docker_files = ["Dockerfile", "docker-compose.yml", ".dockerignore"]
        for docker_file in docker_files:
            if not any(item.get("name") == docker_file for item in structure_list):
                structure_list.append({
                    "type": "file",
                    "name": docker_file
                })
    
    # Add CI/CD support
    if prefs.include_ci_cd:
        if not any(item.get("name") == ".github" for item in structure_list):
            structure_list.append({
                "type": "folder",
                "name": ".github",
                "children": [
                    {
                        "type": "folder",
                        "name": "workflows",
                        "children": [
                            {"type": "file", "name": "ci.yml"}
                        ]
                    }
                ]
            })
    
    return structure

def build_prompt(project_desc: str, tech_stack: List[str], 
                prefs: Optional[ProjectPreferences] = None,
                similar_repos: List[Dict] = None) -> str:
    """Build the prompt for the LLM"""
    
    similar_examples = ""
    if similar_repos:
        similar_examples = "\n\nHere are some similar project examples for reference:\n"
        for i, repo in enumerate(similar_repos, 1):
            similar_examples += f"\nExample {i}:\n"
            similar_examples += f"Description: {repo['description']}\n"
            similar_examples += f"Tech Stack: {', '.join(repo['tech_stack'])}\n"
    
    preferences_text = ""
    if prefs:
        preferences_text = f"""
Additional Requirements:
- Include documentation folder: {prefs.include_docs}
- Include tests folder: {prefs.include_tests}
- Include Docker support: {prefs.include_docker}
- Include CI/CD: {prefs.include_ci_cd}
- Custom folders: {', '.join(prefs.custom_folders) if prefs.custom_folders else 'None'}
- Framework-specific structure: {prefs.framework_specific}
"""
    
    prompt = f"""You are an expert software architect. Create a standardized project directory structure based on the following requirements:

Project Description: {project_desc}
Tech Stack: {', '.join(tech_stack)}
{preferences_text}
{similar_examples}

Generate a comprehensive directory structure that follows best practices for the given tech stack. The output must be a valid JSON object with the following exact schema:

{{
  "name": "project-name",
  "structure": [
    {{"type": "file", "name": "README.md"}},
    {{"type": "file", "name": ".gitignore"}},
    {{"type": "folder", "name": "src", "children": [
      {{"type": "file", "name": "main.py"}},
      {{"type": "folder", "name": "utils", "children": []}}
    ]}}
  ]
}}

Rules:
1. Always include README.md and .gitignore
2. Use appropriate file extensions for the tech stack
3. Follow language/framework conventions
4. Include common configuration files
5. Structure should be logical and scalable
6. Use lowercase names with hyphens or underscores
7. Include only the JSON, no additional text or explanations

Generate the directory structure now:"""
    
    return prompt

def structure_to_tree(structure: Dict) -> str:
    """Convert JSON structure to text tree representation"""
    if not structure:
        return "Invalid structure"
    
    tree_lines = [f"{structure['name']}/"]
    
    def _build_tree(items: List[Dict], current_indent: str) -> List[str]:
        lines = []
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            prefix = "└── " if is_last else "├── "
            name = item.get('name', 'unnamed')
            
            if item.get('type') == 'folder':
                lines.append(f"{current_indent}{prefix}{name}/")
                if 'children' in item and item['children']:
                    next_indent = current_indent + ("    " if is_last else "│   ")
                    lines.extend(_build_tree(item['children'], next_indent))
            else:
                lines.append(f"{current_indent}{prefix}{name}")
        return lines
    
    if 'structure' in structure:
        tree_lines.extend(_build_tree(structure['structure'], ""))
    
    return "\n".join(tree_lines)

def parse_preferences(prefs_text: str) -> ProjectPreferences:
    """Parse preferences from text input"""
    prefs = ProjectPreferences()
    
    if not prefs_text.strip():
        return prefs
    
    prefs_lower = prefs_text.lower()
    
    # Parse boolean preferences
    prefs.include_docs = "docs" in prefs_lower or "documentation" in prefs_lower
    prefs.include_tests = "test" in prefs_lower
    prefs.include_docker = "docker" in prefs_lower
    prefs.include_ci_cd = "ci" in prefs_lower or "github actions" in prefs_lower
    
    # Parse custom folders
    custom_folders = []
    lines = prefs_text.split('\n')
    for line in lines:
        if line.strip().startswith('folder:') or line.strip().startswith('custom:'):
            folder_name = line.split(':', 1)[1].strip()
            if folder_name:
                custom_folders.append(folder_name)
    
    prefs.custom_folders = custom_folders
    return prefs