# Directory_Generation_Agent
A smart agent powered by OpenAI GPT-3.5 Turbo that generates project directory structures from natural language input. It interprets user prompts to create organized folders and files for various use cases like software development, data science, and more.
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
File Organization:

> models.py - Data classes and example repositories

> services.py - LLM, cache, similarity, and validation services

> utils.py - Helper functions for parsing, formatting, and preferences

> agent.py - Main DirectoryStructureAgent orchestrator class

> main.py - Gradio interface and entry point
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Key Benefits of This Structure:

✅ Clean Separation: Each file has a single, clear responsibility

✅ Easy Maintenance: Changes to one feature don't affect others

✅ Simple Imports: Clear dependency flow between files

✅ Testable: Each component can be tested independently

✅ Scalable: Easy to add new features or modify existing ones
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
How It Works:

main.py → Creates Gradio interface, calls agent.py

agent.py → Orchestrates all services, main business logic

services.py → Handles LLM calls, caching, similarity matching

utils.py → Helper functions for text processing and formatting

models.py → Data structures and example templates
