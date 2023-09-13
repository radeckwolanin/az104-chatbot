import os
import streamlit as st

from components.sidebar import sidebar
from core.embedding import get_vectorstore
from core.qa import query_folder

EMBEDDING = "openai"
VECTOR_STORE = "chromadb" # faiss
MODEL = "openai"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "ls__7fe96d9dfa664e99ad0e78c2f9302178"
os.environ["LANGCHAIN_PROJECT"] = "az104-chatbot"

if "OPENAI_API_KEY" not in st.session_state: 
    st.session_state.OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    
openai_api_key = st.session_state.get("OPENAI_API_KEY")

st.set_page_config(page_title="AZ-104 Chatbot", page_icon="📖", layout="wide")
st.header("📖 AZ-104 Chatbot")

sidebar()

if not openai_api_key:
    st.warning(
        "Missing OpenAI API key in the .env file. You can get a key at"
        " https://platform.openai.com/account/api-keys."
    )

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
        
        folder_index = get_vectorstore("temp_name")

        result = query_folder(
            folder_index=folder_index,
            query=prompt,
            model=MODEL,
            openai_api_key=openai_api_key,
            temperature=0,
        )
        
        st.markdown(result.answer)
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": result.answer})
    
