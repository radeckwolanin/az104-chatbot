import requests
import streamlit as st
import pandas as pd

from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings

from components.sidebar import sidebar

from ui import (
    wrap_doc_in_html,
    is_query_valid,
    is_file_valid,
    is_open_ai_key_valid,
    display_file_read_error,
)

from core.caching import bootstrap_caching
from core.parsing import read_file
from core.chunking import chunk_file
from core.embedding import embed_files
from core.embedding import get_vectorstore
from core.qa import query_folder

EMBEDDING = "openai"
VECTOR_STORE = "chromadb" # faiss
MODEL = "openai"

url = 'http://20.115.73.2:8000/api/v1/heartbeat'
api_collections = 'http://20.115.73.2:8000/api/v1/collections'

# For testing
# EMBEDDING, VECTOR_STORE, MODEL = ["debug"] * 3

st.set_page_config(page_title="AZ-104 Chatbot", page_icon="📖", layout="wide")
st.header("📖 AZ-104 Chatbot")

# Enable caching for expensive functions
bootstrap_caching()

sidebar()

openai_api_key = st.session_state.get("OPENAI_API_KEY")

if not openai_api_key:
    st.warning(
        "Missing OpenAI API key in the .env file. You can get a key at"
        " https://platform.openai.com/account/api-keys."
    )

# Create 2 tabs
qa_tab, upload_tab = st.tabs(["Question & Answer", "Upload"])

with qa_tab:
                    
    with st.form(key="qa_form"):
        query = st.text_area("Ask a question about the document")
        show_sources = st.checkbox("Show used sources retrieved from vector db", value=True)
        submit = st.form_submit_button("Submit")
        
    if submit:
        if not is_query_valid(query):
            st.stop()

        # Output Columns
        answer_col, sources_col = st.columns(2)
        
        folder_index = get_vectorstore("temp_name")

        result = query_folder(
            folder_index=folder_index,
            query=query,
            model=MODEL,
            openai_api_key=openai_api_key,
            temperature=0,
        )

        with answer_col:
            st.markdown("#### Answer")
            st.markdown(result.answer)

        with sources_col:
            if not show_sources:
                st.stop()
            st.markdown("#### Sources")
            for source in result.sources:
                st.markdown(source.page_content)
                st.markdown(source.metadata["source"])
                st.markdown("---")

with upload_tab:    
    try:
        response = requests.get(api_collections)    # Get list of collections in ChromaDB Server
        response.raise_for_status()  # This will raise an exception for HTTP error status codes

        if response.status_code == 200:
            collections = response.json()
            
            # Prepare data for the table
            table_data = []
            for collection in collections:                
                checked = False
                name = collection.get('name', 'N/A')
                collection_id = collection.get('id', 'N/A')
                collecion_count = requests.get(api_collections+'/'+collection_id+'/count').json()
                metadata = collection.get('metadata', 'N/A')
                table_data.append([checked, name, collection_id, collecion_count, metadata])
            
            # Create a DataFrame
            collections_df = pd.DataFrame(table_data, columns=["Source", "Name", "ID", "Count", "Metadata"])
            
            st.subheader("Available collections:")
            edited_df = st.data_editor(
                collections_df,
                column_config={
                    "Source": st.column_config.CheckboxColumn(
                        "Use as source",
                        default=False,
                        width="small",
                        required=True,
                    )
                },
                disabled=["Name", "ID", "Count", "Metadata"],
                use_container_width=True,
                hide_index=True,
            )
            
            sources = edited_df.loc[edited_df["Source"],"ID"]
        
            # Listen for checkbox changes
            for source in sources:
                st.markdown(f"Source **{source}**")
                st.toast(f"ID {source} checked")
                
        else:
            st.error('Error')
    except requests.exceptions.RequestException as e:
        st.write('An error occurred:', e)
        
    uploaded_file = st.file_uploader(
        "Upload a pdf, docx, or txt file",
        type=["pdf", "docx", "txt"],
        help="Scanned documents are not supported yet!",
    )
    if uploaded_file is not None:
        try:
            file = read_file(uploaded_file)
        except Exception as e:
            display_file_read_error(e)
            
        chunked_file = chunk_file(file, chunk_size=300, chunk_overlap=0)
            
        if not is_file_valid(file):
            st.stop()

        if not is_open_ai_key_valid(openai_api_key):
            st.stop()

        with st.spinner("Indexing document... This may take a while⏳"):
            folder_index = embed_files(
                files=[chunked_file],
                embedding=EMBEDDING,
                vector_store=VECTOR_STORE,
                openai_api_key=openai_api_key,
            )
            
        if folder_index:
            st.write("Folder index does exists!")
            print(folder_index)
            qa = RetrievalQA.from_chain_type(
                llm=OpenAI(), 
                chain_type="stuff", 
                retriever=folder_index.index.as_retriever()
            )
            query = "What is AZURE RBAC and AZURE storage solutons?"
            qa.run(query)
            st.write("Folder index does exists!")
    else:        
        st.stop()



