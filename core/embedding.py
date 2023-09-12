from langchain.vectorstores import VectorStore
from core.parsing import File
from langchain.vectorstores.faiss import FAISS
from langchain.vectorstores import Chroma
import chromadb
from chromadb.utils import embedding_functions
import uuid
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from typing import List, Type
from langchain.docstore.document import Document
from core.debug import FakeVectorStore, FakeEmbeddings


class FolderIndex:
    """Index for a collection of files (a folder)"""

    def __init__(self, files: List[File], index: VectorStore):
        self.name: str = "default"
        self.files = files
        self.index: VectorStore = index

    @staticmethod
    def _combine_files(files: List[File]) -> List[Document]:
        """Combines all the documents in a list of files into a single list."""

        all_texts = []
        for file in files:
            for doc in file.docs:
                doc.metadata["file_name"] = file.name
                doc.metadata["file_id"] = file.id
                all_texts.append(doc)

        return all_texts

    @classmethod
    def from_files(
        cls, files: List[File], embeddings: Embeddings, vector_store: Type[VectorStore]
    ) -> "FolderIndex":
        """
            Creates an index from files.
            TODO: Use HOST and other info from variable, not hard coded
        """

        all_docs = cls._combine_files(files)
        
        client = chromadb.HttpClient(host="20.115.73.2", port=8000)
        
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            #api_key="YOUR_API_KEY",
            model_name="text-embedding-ada-002"
        )
        
        collection = client.get_or_create_collection(
            name="from_files_collection", 
            embedding_function=openai_ef
        )
        
        #embeds = embeddings.embed_documents(all_docs[0].page_content)
        #print(len(embeds)) 1529
        #print('\n\n')
        
        for doc in all_docs:
            #embeds = embeddings.embed_documents(doc.page_content)
            collection.add(
                ids=[str(uuid.uuid1())], 
                #embeddings=[embeddings.embed_documents(doc.page_content)],
                #embeddings=[embeds],
                #embeddings=embeddings,
                #embeddings=embeds,
                metadatas=doc.metadata, 
                documents=doc.page_content
            )
           
        index = Chroma(
            client=client, 
            collection_name="from_files_collection",
            embedding_function=openai_ef
        )
        """
        index = vector_store.from_documents(
            documents=all_docs,
            embedding=embeddings,
            client=client,
            collection_name="from_file_collection"
        )
        """

        return cls(files=files, index=index)
    
    @classmethod
    def from_chromadb(cls) -> "FolderIndex":
        """Creates an ChromaDB client."""
        
        client = chromadb.HttpClient(host="20.115.73.2", port=8000)

        index = Chroma(
            client=client,
        )

        return cls(files=None, index=index)


def embed_files(
    files: List[File], embedding: str, vector_store: str, **kwargs
) -> FolderIndex:
    """Embeds a collection of files and stores them in a FolderIndex."""

    supported_embeddings: dict[str, Type[Embeddings]] = {
        "openai": OpenAIEmbeddings,
        "debug": FakeEmbeddings,
    }
    supported_vector_stores: dict[str, Type[VectorStore]] = {
        "faiss": FAISS,
        "chromadb": Chroma,
        "debug": FakeVectorStore,
    }

    if embedding in supported_embeddings:
        _embeddings = supported_embeddings[embedding](**kwargs)
    else:
        raise NotImplementedError(f"Embedding {embedding} not supported.")

    if vector_store in supported_vector_stores:
        _vector_store = supported_vector_stores[vector_store]
    else:
        raise NotImplementedError(f"Vector store {vector_store} not supported.")

    return FolderIndex.from_files(
        files=files, embeddings=_embeddings, vector_store=_vector_store
    )
    
def get_vectorstore(
    vector_store: str, **kwargs
) -> FolderIndex:
    """Return FolderIndex as ChromaDB client"""
    
    return FolderIndex.from_chromadb()
    
