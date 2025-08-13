# config.py

# --- Ollama Configuration ---
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
SYNTHESIS_MODEL_TIMEOUT = 360.0
SYNTHESIS_MODEL_CONTEXT_WINDOW = 4096 # 4k context window is a reasonable default
MODEL_EXCLUDE_PREFIX = "nomic" # Exclude embedding models from selection

# --- File Paths ---
PROMPTS_FILE = "prompts.json"
CONTEXT_FILE = "project_context.json"
LOG_DIRECTORY = "compliance_logs"