# src/helper.py
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings   # ✅ naya import
from langchain_core.documents import Document
from typing import List


def load_pdf_file(data: str):
    loader = DirectoryLoader(data, glob="*.pdf", loader_cls=PyPDFLoader)
    return loader.load()


def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    return [
        Document(
            page_content=doc.page_content,
            metadata={"source": doc.metadata.get("source")}
        )
        for doc in docs
    ]


def text_split(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    return splitter.split_documents(docs)


def download_hugging_face_embeddings():
    return HuggingFaceEmbeddings(          # ✅ langchain_huggingface se aa raha hai
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
