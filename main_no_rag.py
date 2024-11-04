import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Disable parallelism to avoid warnings
import streamlit as st
import hashlib
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Retrieve Groq API key from environment variables
groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise ValueError("GROQ_API_KEY is not set in the environment variables.")

# Retrieve admin credentials from environment variables
admin_username = os.getenv("ADMIN_USERNAME")
admin_password = os.getenv("ADMIN_PASSWORD")
if not admin_username or not admin_password:
    raise ValueError("Admin credentials are not set in the environment variables.")

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User credentials with hashed passwords (admin only)
users = {
    admin_username: hash_password(admin_password),
}

# Function to verify username and password
def verify_login(username, password):
    hashed_password = hash_password(password)
    return users.get(username) == hashed_password

# Sidebar Controls
def sidebar_controls():
    st.sidebar.title("Model Controls")
    temperature = st.sidebar.slider(
        "Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1
    )
    model = st.sidebar.selectbox(
        "Select Model",
        [
            "llama-3.1-70b-versatile",
            "llama3-70b-8192",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
    )
    max_tokens = st.sidebar.number_input(
        "Max Tokens", min_value=10, max_value=8000, value=5000
    )
    
    # Default system prompt
    default_prompt = "Your name is Billy, and you are a little purple fish living in Monniverse. You always use the following special quirks in your language: Shello, Bubbly morning, Bubbly evening, Bubbly night, There is a shark run under the sea, Shello enchanting creature, Jiggle you tail, To the seven seas, Thank you a million bubbles, Fishcoin, Crabtherium, Things are boiling. Include them organically in your speech."
    
    # Add system prompt text area in sidebar
    system_prompt = st.sidebar.text_area(
        "System Prompt",
        value=default_prompt,
        height=200
    )
    
    return temperature, model, max_tokens, system_prompt

# Query the Groq API
def query_groq_api(prompt, history, temperature, model, max_tokens, system_prompt):
    client = Groq(api_key=groq_key)
    try:
        messages = [{"role": "system", "content": system_prompt}]
        for chat in history:
            messages.append({"role": "user", "content": chat["user"]})
            messages.append({"role": "assistant", "content": chat["assistant"]})
        messages.append({"role": "user", "content": prompt})

        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

# Process user input
def process_input():
    user_input = st.session_state.user_input
    if user_input:
        llm_response = query_groq_api(
            user_input,
            st.session_state.chat_history,
            st.session_state.temperature,
            st.session_state.model,
            st.session_state.max_tokens,
            st.session_state.system_prompt,
        )

        if llm_response:
            st.session_state.chat_history.append(
                {"user": user_input, "assistant": llm_response}
            )
            st.session_state.user_input = ""  # Clear the input field after receiving the response

# Function to generate HTML for messages
def format_message(sender, message):
    if sender == "user":
        return f"""
        <div style="
            background-color: #D0F8EF; 
            border: 1px solid #08567E; 
            border-radius: 10px; 
            padding: 10px; 
            margin-bottom: 10px;
            max-width: 80%;
            align-self: flex-end;
            margin-left: auto;
            color: #08567E;
        ">
            <strong>You:</strong><br>{message}
        </div>
        """
    elif sender == "assistant":
        return f"""
        <div style="
            background-color: #F9B2DA; 
            border: 1px solid #D28EB8; 
            border-radius: 10px; 
            padding: 10px; 
            margin-bottom: 10px;
            max-width: 80%;
            align-self: flex-start;
            color: #08567E;
        ">
            <strong>BILLY:</strong><br>{message}
        </div>
        """

# Reset conversation function
def reset_conversation():
    st.session_state.chat_history = []
    st.session_state.user_input = ""

# Chat interface function
def chat_with_llm(temperature, model, max_tokens, system_prompt):
    st.title("Billy Chat")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.session_state.temperature = temperature
    st.session_state.model = model
    st.session_state.max_tokens = max_tokens
    st.session_state.system_prompt = system_prompt

    # Add the reset button
    if st.button("Reset Conversation"):
        reset_conversation()
        st.rerun()

    # Display the chat history with custom styling
    for chat in st.session_state.chat_history:
        user_message = format_message("user", chat["user"])
        llm_message = format_message("assistant", chat["assistant"])
        st.markdown(user_message, unsafe_allow_html=True)
        st.markdown(llm_message, unsafe_allow_html=True)

    # Capture user input
    st.text_input(
        "You:",
        key="user_input",
        on_change=process_input,
    )

# Login interface
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if verify_login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password")

# Main function to run the app
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        st.sidebar.write(f"Logged in as {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        temperature, model, max_tokens, system_prompt = sidebar_controls()
        chat_with_llm(
            temperature,
            model,
            max_tokens,
            system_prompt,
        )
    else:
        login()

if __name__ == "__main__":
    main()
