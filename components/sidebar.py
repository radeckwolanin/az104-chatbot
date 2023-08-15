import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

def sidebar():
    with st.sidebar:
        api_key_input = os.getenv("OPENAI_API_KEY") # Get API key from environment variable

        st.session_state["OPENAI_API_KEY"] = api_key_input

        st.markdown("---")
        st.markdown("# About")
        st.markdown(
            "📖AZ-104 Chatbot allows you to ask questions about "
            "Azure Admistrator subject and get accurate answers with instant citations. "
        )        
        st.markdown("Made by Radeck Wolanin")
        st.markdown("---")
