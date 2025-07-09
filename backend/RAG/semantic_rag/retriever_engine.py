import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

load_dotenv()

class SemanticRAG:
    def __init__(self):
        self.vectorstore_path = "chroma_store"
        self.embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="meta-llama/llama-4-maverick-17b-128e-instruct"
        )

        if not os.path.exists(self.vectorstore_path):
            self._create_vectorstore()

        self.vectorstore = Chroma(
            persist_directory=self.vectorstore_path,
            embedding_function=self.embedding
        )

    def _create_vectorstore(self):
        docs_path = "data/documents"
        text_files = list(Path(docs_path).glob("*.txt"))

        raw_docs = []
        for file_path in text_files:
            loader = TextLoader(str(file_path), encoding="utf-8")
            raw_docs.extend(loader.load())

        if not raw_docs:
            raise ValueError("No documents found for semantic RAG. Please add .txt files to data/documents.")

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        split_docs = splitter.split_documents(raw_docs)

        if not split_docs:
            raise ValueError("Splitting failed. Are your .txt files empty?")

        Chroma.from_documents(split_docs, self.embedding, persist_directory=self.vectorstore_path)

    def retrieve_context(self, query, k=3):
        docs = self.vectorstore.similarity_search(query, k=k)
        return "\n".join([doc.page_content for doc in docs])

    def generate_answer(self, query, context):
        prompt = f"""
Answer the following question based only on the context provided.

Context:
{context}

Question: {query}
Answer:
"""
        return self.llm.invoke(prompt).content.strip()

    def process_query(self, query):
        context = self.retrieve_context(query)
        return self.generate_answer(query, context)