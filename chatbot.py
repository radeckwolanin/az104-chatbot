import streamlit as st
from components.sidebar import sidebar

st.set_page_config(page_title="AZ-104 Chatbot", page_icon="📖", layout="wide")
st.header("📖 AZ-104 Chatbot")

sidebar()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    
# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.chat_message("assistant"):
    st.write("Hello👋 Ask me anything related to Azure cloud administration.")
    
# React to user input
if prompt := st.chat_input("For example: What are main types of Azure storage solutions?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    response = f"Echo: {prompt}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
