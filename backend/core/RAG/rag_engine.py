import os
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant

class RAGEngine:
    def __init__(self,
                 doc_dir: Optional[str] = None,
                 embedding_model_dir: Optional[str] = None,
                 collection_name: str = "my_documents",
                 qdrant_location: str = ":memory:",
                 chunk_size: int = 200,
                 chunk_overlap: int = 10):
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.doc_dir = doc_dir if doc_dir is not None else os.path.join(base_path, "documents")
        self.embedding_model_dir = embedding_model_dir if embedding_model_dir is not None else os.path.join(base_path, "embedding_models", "m3e-base")
        self.collection_name = collection_name
        self.qdrant_location = qdrant_location
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vectorstore = None
        self._init_vectorstore()

    def _load_documents(self) -> List:
        documents = []
        for file in os.listdir(self.doc_dir):
            file_path = os.path.join(self.doc_dir, file)
            if file.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
            elif file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif file.endswith(".docx"):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
        return documents

    def _init_vectorstore(self):
        documents = self._load_documents()
        if not documents:
            self.vectorstore = None
            return
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        chunked_documents = text_splitter.split_documents(documents)
        embedding_model = HuggingFaceEmbeddings(
            model_name=self.embedding_model_dir,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.vectorstore = Qdrant.from_documents(
            documents=chunked_documents,
            embedding=embedding_model,
            location=self.qdrant_location,
            collection_name=self.collection_name
        )

    def get_retriever(self):
        if self.vectorstore is None:
            self._init_vectorstore()
        if self.vectorstore is None:
            raise RuntimeError("No documents loaded for RAG knowledge base.")
        return self.vectorstore.as_retriever()

    def query(self, query_text: str, top_k: int = 3) -> List[str]:
        retriever = self.get_retriever()
        docs = retriever.get_relevant_documents(query_text)
        return [doc.page_content for doc in docs] 