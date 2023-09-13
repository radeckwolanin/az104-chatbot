import streamlit as st
import numpy as np
from components.sidebar import sidebar

st.set_page_config(page_title="AZ-104 Chatbot", page_icon="📖", layout="wide")
st.header("📖 AZ-104 Chatbot")

sidebar()

with st.chat_message("user"):
    st.write("Hello 👋")
    st.line_chart(np.random.randn(30, 3))
    
prompt = st.chat_input("Say something")
if prompt:
    st.write(f"User has sent the following prompt: {prompt}")