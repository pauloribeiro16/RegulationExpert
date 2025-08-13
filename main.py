# main.py
import sys
import beaupy
import requests
import subprocess
import config

def list_ollama_models(exclude_prefix="nomic"):
    """Lists available Ollama models, excluding specified prefixes."""
    try:
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()
        models = [m["name"] for m in response.json().get("models", [])]
        return sorted([m for m in models if not m.startswith(exclude_prefix)])
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Error contacting Ollama at {config.OLLAMA_BASE_URL}. Is it running? Details: {e}")
        return []

def main():
    """Interactively selects a model and launches the Streamlit UI."""
    print("--- ✍️ The Scribe: Compliance Co-Pilot ---")
    available_models = list_ollama_models(config.MODEL_EXCLUDE_PREFIX)
    
    if not available_models:
        print("❌ No compatible Ollama models found. Please ensure Ollama is running and has models installed.")
        sys.exit(1)
        
    print("\nPlease select the main LLM to use for the session:")
    selected_model = beaupy.select(available_models, cursor="👉", cursor_style="cyan")
    
    if not selected_model:
        print("No model selected. Exiting.")
        sys.exit(0)
        
    print(f"\n🚀 Launching The Scribe UI with model: {selected_model}")
    
    # Construct the command to run the Streamlit app
    # The '--' is crucial to separate arguments for streamlit from arguments for our script
    command = [
        sys.executable, "-m", "streamlit", "run", "app_ui.py",
        "--", "--model_name", selected_model
    ]
    
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("\n❌ ERROR: 'streamlit' command not found.")
        print("   Please install Streamlit by running: pip install streamlit")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR: The UI process exited unexpectedly. Code: {e.returncode}")

if __name__ == "__main__":
    main()