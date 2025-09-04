# main.py
import sys
import os
import json
import beaupy
import requests
import subprocess
import config

def list_ollama_models(exclude_prefix="nomic"):
    # ... (this function remains unchanged) ...
    try:
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags")
        response.raise_for_status()
        models = [m["name"] for m in response.json().get("models", [])]
        return sorted([m for m in models if not m.startswith(exclude_prefix)])
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Error contacting Ollama at {config.OLLAMA_BASE_URL}. Is it running? Details: {e}")
        return []

def list_session_logs():
    """
    Finds and validates saved session logs.
    Only logs conforming to the new format (dict with 'metadata' and 'history')
    are returned.
    """
    valid_logs = []
    log_dir = config.LOG_DIRECTORY
    if not os.path.isdir(log_dir):
        return []
    
    files = sorted([f for f in os.listdir(log_dir) if f.startswith("session_") and f.endswith(".json")], reverse=True)
    
    for filename in files:
        filepath = os.path.join(log_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Validate the structure
            if isinstance(data, dict) and "metadata" in data and "history" in data:
                valid_logs.append(filename)
            else:
                print(f"⚠️  Skipping incompatible log file (old format): {filename}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Skipping corrupted log file: {filename} ({e})")
            
    return valid_logs

def main():
    """Interactively selects a model and launches the Streamlit UI."""
    print("--- ✍️ The Scribe: Compliance Co-Pilot ---")
    
    session_mode = beaupy.select(["Start New Session", "Resume Existing Session"], cursor="👉", cursor_style="cyan")
    
    selected_model = None
    resume_file_path = None
    
    if session_mode == "Resume Existing Session":
        logs = list_session_logs() # This now returns only valid logs
        if not logs:
            print("\n❌ No compatible saved session logs found. Starting a new session instead.")
        else:
            print("\nPlease select a session to resume:")
            selected_log = beaupy.select(logs, cursor="👉", cursor_style="cyan")
            if selected_log:
                resume_file_path = os.path.join(config.LOG_DIRECTORY, selected_log)
                # VETTING: Simplified logic, as validation is already done.
                with open(resume_file_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                selected_model = log_data["metadata"]["model_name"]
                print(f"✅ Resuming session with original model: {selected_model}")

    # If starting a new session or resuming failed, run model selection
    if not selected_model:
        available_models = list_ollama_models(config.MODEL_EXCLUDE_PREFIX)
        if not available_models:
            print("❌ No compatible Ollama models found. Please ensure Ollama is running.")
            sys.exit(1)
        print("\nPlease select the main LLM to use for the session:")
        selected_model = beaupy.select(available_models, cursor="👉", cursor_style="cyan")

    if not selected_model:
        print("No model or session selected. Exiting.")
        sys.exit(0)
        
    print(f"\n🚀 Launching The Scribe UI with model: {selected_model}")
    
    # VETTING: Build a robust, absolute path to the UI script.
    # This prevents errors if the script is run from a different directory.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_ui_path = os.path.join(script_dir, "app_ui.py")

    command = [
        sys.executable, "-m", "streamlit", "run", app_ui_path, # VETTING: Use the absolute path
        "--", "--model_name", selected_model
    ]
    if resume_file_path:
        command.extend(["--resume_from", resume_file_path])
    
    try:
        try:
            subprocess.run(command, check=True)
        except FileNotFoundError:
            # VETTING: Added a check for the UI script itself.
            if not os.path.exists(app_ui_path):
                print(f"\n❌ ERROR: The UI script 'app_ui.py' was not found in the same directory as the launcher.")
            else:
                print("\n❌ ERROR: 'streamlit' command not found.")
                print("   Please install Streamlit by running: pip install streamlit")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ ERROR: The UI process exited unexpectedly. Code: {e.returncode}")
    except KeyboardInterrupt:
        print("\n👋  Shutdown signal received. Exiting gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    main()