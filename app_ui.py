# app_ui.py
import streamlit as st
import json
import argparse
import os
from datetime import datetime
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage, MessageRole
import config

# --- Argument Parsing for Model Name ---
parser = argparse.ArgumentParser()
parser.add_argument("--model_name", type=str, required=True)
args = parser.parse_args()

# --- Core Functions (Cached for performance) ---
@st.cache_resource
def load_llm(model_name):
    """Loads the Ollama LLM, cached for the duration of the session."""
    return Ollama(
        model=model_name,
        base_url=config.OLLAMA_BASE_URL,
        request_timeout=config.SYNTHESIS_MODEL_TIMEOUT,
        context_window=config.SYNTHESIS_MODEL_CONTEXT_WINDOW
    )

@st.cache_data
def load_prompts_and_context():
    """Loads prompts and the project context from disk."""
    with open(config.PROMPTS_FILE, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    with open(config.CONTEXT_FILE, 'r', encoding='utf-8') as f:
        context = json.load(f)
    return prompts, context

# --- Application Initialization ---
llm = load_llm(args.model_name)
prompts, project_context = load_prompts_and_context()

st.set_page_config(page_title="The Scribe", page_icon="✍️", layout="centered")

# --- Session State Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_persona = "conductor" # Start with the conductor
    
    # Format the initial system prompt with project context
    conductor_prompt = prompts["conductor"]["system_prompt"]
    initial_system_message = ChatMessage(
        role=MessageRole.SYSTEM, 
        content=f"PROJECT CONTEXT:\n```json\n{json.dumps(project_context, indent=2)}\n```\n\nINSTRUCTIONS:\n{conductor_prompt}"
    )
    st.session_state.messages.append(initial_system_message)
    
    # Add the first visible message from the assistant
    st.session_state.messages.append(ChatMessage(role=MessageRole.ASSISTANT, content="Greetings! I am The Scribe. I have loaded your project context. Does this look correct, or would you like to add more detail?"))

# --- Sidebar for Controls ---
with st.sidebar:
    st.header("Controls")
    if st.button("Save & End Session", use_container_width=True):
        log_dir = config.LOG_DIRECTORY
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"session_{timestamp}.json")
        
        # Save only user and assistant messages for a clean log
        save_data = [
            {"role": msg.role.name, "content": msg.content} 
            for msg in st.session_state.messages 
            if msg.role != MessageRole.SYSTEM
        ]
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)
        
        st.success(f"Session saved to:\n{log_file}")
        st.info("You can now close this window.")
        st.stop() # Halts the script

# --- Main Chat Interface ---
st.title("✍️ The Scribe")
st.caption(f"Compliance Co-Pilot | Powered by: `{args.model_name}` | Persona: `{st.session_state.current_persona}`")

# Display chat history, ignoring system messages
for message in st.session_state.messages:
    if message.role != MessageRole.SYSTEM:
        with st.chat_message(message.role.name):
            st.markdown(message.content)

# --- User Input and Persona Handoff Logic ---
if prompt := st.chat_input("Your message..."):
    # Append and display user message
    st.session_state.messages.append(ChatMessage(role=MessageRole.USER, content=prompt))
    with st.chat_message("USER"):
        st.markdown(prompt)

    # Persona Handoff Logic
    if st.session_state.current_persona == "conductor" and "gdpr" in prompt.lower():
        st.session_state.current_persona = "gdpr_expert"
        
        # Announce the handoff to the user
        handoff_message = "Excellent. Connecting you to our GDPR specialist now..."
        st.session_state.messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=handoff_message))
        with st.chat_message("ASSISTANT"):
            st.markdown(handoff_message)
            
        # Silently insert the new system prompt for the expert
        expert_system_prompt = prompts["gdpr_expert"]["system_prompt"]
        st.session_state.messages.append(ChatMessage(role=MessageRole.SYSTEM, content=expert_system_prompt))

    # --- LLM Call ---
    with st.chat_message("ASSISTANT"):
        with st.spinner("The Scribe is thinking..."):
            # Filter for only the messages relevant to the current LLM call
            response = llm.chat(st.session_state.messages)
            response_content = response.message.content
            st.markdown(response_content)
    
    # Add AI's response to state
    st.session_state.messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=response_content))