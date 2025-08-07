import os
import json
import hashlib
import logging
import gradio as gr
from dotenv import load_dotenv

from agent import DirectoryStructureAgent
from utils import parse_preferences

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_agent():
    """Create DirectoryStructureAgent instance"""
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return DirectoryStructureAgent(openai_api_key)

def generate_directory_structure(project_desc: str, tech_stack: str, preferences: str):
    """Generate directory structure for Gradio interface"""
    try:
        # Create agent
        agent = create_agent()
        
        # Parse inputs
        tech_list = [tech.strip() for tech in tech_stack.split(',') if tech.strip()]
        prefs = parse_preferences(preferences)
        
        # Generate structure
        project_id = f"gradio_{hashlib.md5(project_desc.encode()).hexdigest()[:8]}"
        structure = agent.suggest_structure(project_id, project_desc, tech_list, prefs)
        
        if not structure:
            return "Failed to generate directory structure. Please try again.", "Error occurred."
        
        # Format outputs
        json_output = json.dumps(structure, indent=2)
        tree_output = agent.structure_to_tree(structure)
        
        return json_output, tree_output
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        return error_msg, error_msg

def create_gradio_app():
    """Create and return Gradio interface"""
    
    with gr.Blocks(title="Directory Structure Agent", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🗂️ Directory Structure Agent")
        gr.Markdown("Generate standardized project directory structures based on your project description and tech stack.")
        
        with gr.Row():
            with gr.Column(scale=1):
                project_desc = gr.Textbox(
                    label="Project Description",
                    placeholder="e.g., A web application for task management with user authentication",
                    lines=3
                )
                
                tech_stack = gr.Textbox(
                    label="Tech Stack (comma-separated)",
                    placeholder="e.g., React, Node.js, PostgreSQL, Docker",
                    lines=2
                )
                
                preferences = gr.Textbox(
                    label="Preferences (optional)",
                    placeholder="e.g., include docker, tests, docs\nfolder: custom-folder-name",
                    lines=4
                )
                
                generate_btn = gr.Button("Generate Structure", variant="primary")
            
            with gr.Column(scale=2):
                with gr.Tab("JSON Structure"):
                    json_output = gr.Code(
                        label="JSON Directory Structure",
                        language="json",
                        lines=20
                    )
                
                with gr.Tab("Tree View"):
                    tree_output = gr.Textbox(
                        label="Tree Directory Structure",
                        lines=20,
                        max_lines=30,
                        show_copy_button=True,
                        container=True,
                        interactive=False
                    )
        
        # Examples
        gr.Markdown("## Examples")
        examples = [
            [
                "A full-stack e-commerce web application with user authentication, payment processing, and admin dashboard",
                "React, TypeScript, Node.js, Express, PostgreSQL, Redis",
                "include docker\ninclude tests\nfolder: uploads\nfolder: logs"
            ],
            [
                "A REST API for a mobile app with real-time notifications",
                "Python, FastAPI, PostgreSQL, Redis, WebSocket",
                "include docs\ninclude docker\nfolder: migrations"
            ],
            [
                "A machine learning project for image classification",
                "Python, TensorFlow, Jupyter, scikit-learn",
                "folder: data\nfolder: models\nfolder: notebooks\ninclude tests"
            ]
        ]
        
        gr.Examples(
            examples=examples,
            inputs=[project_desc, tech_stack, preferences],
            label="Try these examples"
        )
        
        # Connect the generate button
        generate_btn.click(
            fn=generate_directory_structure,
            inputs=[project_desc, tech_stack, preferences],
            outputs=[json_output, tree_output]
        )
    
    return app

if __name__ == "__main__":
    # Ensure OpenAI API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the environment")
    else:
        app = create_gradio_app()
        app.launch(share=True, debug=True)