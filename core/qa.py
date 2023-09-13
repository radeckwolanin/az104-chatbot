from typing import Any, List
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from core.prompts import STUFF_PROMPT
from langchain.docstore.document import Document
from langchain.chat_models import ChatOpenAI
from core.embedding import FolderIndex
from core.debug import FakeChatModel
from pydantic import BaseModel


class AnswerWithSources(BaseModel):
    answer: str
    sources: List[Document]


def query_folder(
    query: str,
    folder_index: FolderIndex,
    model: str = "openai",
    **model_kwargs: Any,
) -> AnswerWithSources:
    """Queries a folder index for an answer.

    Args:
        query (str): The query to search for.
        folder_index (FolderIndex): The folder index to search.
        model (str): The model to use for the answer generation.
        **model_kwargs (Any): Keyword arguments for the model.

    Returns:
        AnswerWithSources: The answer and the source documents.
    """
    supported_models = {
        "openai": ChatOpenAI,
        "debug": FakeChatModel,
    }

    if model in supported_models:
        llm = supported_models[model](**model_kwargs)
    else:
        raise ValueError(f"Model {model} not supported.")

    chain = load_qa_with_sources_chain(
        llm=llm,
        chain_type="stuff",
        prompt=STUFF_PROMPT,
    )

    relevant_docs = folder_index.index.similarity_search(query, k=5)
        
    result = chain(
        {"input_documents": relevant_docs, "question": query}, return_only_outputs=True
    )
    sources = relevant_docs

    answer = result["output_text"].split("SOURCES: ")[0]

    return AnswerWithSources(answer=answer, sources=sources)


