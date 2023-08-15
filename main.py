import requests
import streamlit as st
import pandas as pd

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
from core.qa import query_folder

EMBEDDING = "openai"
VECTOR_STORE = "faiss"
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
    try:
        response = requests.get(api_collections)    # Get list of collections in ChromaDB Server
        response.raise_for_status()  # This will raise an exception for HTTP error status codes

        if response.status_code == 200:
            collections = response.json()
            
            #collections_df = pd.DataFrame(columns=["Source", "Name", "ID", "Metadata"])

            # Prepare data for the table
            table_data = []
            for collection in collections:
                checked = False
                name = collection.get('name', 'N/A')
                collection_id = collection.get('id', 'N/A')
                metadata = collection.get('metadata', 'N/A')
                #checkmark = st.checkbox("", key=collection_id)  # Add a checkbox for each collection
                #table_data.append([checkmark, name, collection_id, metadata])
                table_data.append([checked, name, collection_id, metadata])
                #collections_df = collections_df.append(
                    #{
                    #    "Source": False,
                    #    "Name": collection.get('name', 'N/A')
                    #    "ID": collection.get('id', 'N/A')
                    #    "Metadata": collection.get('metadata', 'N/A')
                    #},
                    #collection,
                    #ignore_index=True
                #)
            
            # Create a DataFrame
            collections_df = pd.DataFrame(table_data, columns=["Source", "Name", "ID", "Metadata"])
            #collections_df = pd.DataFrame(table_data)
                

            # Display the table using st.table
            st.subheader("Available collections:")            
            #st.table(collections_df)
            #st.dataframe(collections_df)
            st.data_editor(
                collections_df,
                column_config={
                    "Source": st.column_config.CheckboxColumn(
                        "Use as source",
                        default=False,
                    )
                },
                disabled=["Name", "ID", "Metadata"],
                use_container_width=True,
                hide_index=True,
            )
            
            # Listen for checkbox changes
            for collection in collections:
                collection_id = collection.get('id', 'N/A')
                checkbox_value = st.session_state[collection_id]
                if checkbox_value:
                    st.toast(f"Collection {collection_id} checked")
        else:
            st.error('Error')
    except requests.exceptions.RequestException as e:
        st.write('An error occurred:', e)
                
    with st.form(key="qa_form"):
        query = st.text_area("Ask a question about the document")
        submit = st.form_submit_button("Submit")
        
    with st.expander("Advanced Options"):
        return_all_chunks = st.checkbox("Show all chunks retrieved from vector search")
        show_full_doc = st.checkbox("Show parsed contents of the document")
        

with upload_tab:
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
    else:
        st.warning("File queue empty.")
        st.stop()

st.stop()

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





if show_full_doc:
    with st.expander("Document"):
        # Hack to get around st.markdown rendering LaTeX
        st.markdown(f"<p>{wrap_doc_in_html(file.docs)}</p>", unsafe_allow_html=True)


if submit:
    if not is_query_valid(query):
        st.stop()

    # Output Columns
    answer_col, sources_col = st.columns(2)

    result = query_folder(
        folder_index=folder_index,
        query=query,
        return_all=return_all_chunks,
        model=MODEL,
        openai_api_key=openai_api_key,
        temperature=0,
    )

    with answer_col:
        st.markdown("#### Answer")
        st.markdown(result.answer)

    with sources_col:
        st.markdown("#### Sources")
        for source in result.sources:
            st.markdown(source.page_content)
            st.markdown(source.metadata["source"])
            st.markdown("---")
