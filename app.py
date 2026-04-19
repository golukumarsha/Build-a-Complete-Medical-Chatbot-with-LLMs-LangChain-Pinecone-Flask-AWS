from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os

# LangChain imports
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import BaseRetriever, Document

# Pinecone + embeddings
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from typing import List

# ------------------ App Initialization ------------------
app = Flask(__name__)
load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# HuggingFace embeddings
embeddings = download_hugging_face_embeddings()

# Index name
index_name = "medical-chatbot"

# Check if index exists
if index_name not in pc.list_indexes().names():
    raise ValueError(
        f"Index '{index_name}' does not exist. Run store_index.py first."
    )

# Load Pinecone index
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

# ------------------ Custom Retriever ------------------


class PineconeRetrieverWrapper(BaseRetriever):
    vectorstore: PineconeVectorStore  # ✅ Pydantic field
    k: int = 3

    def get_relevant_documents(self, query: str) -> List[Document]:
        return self.vectorstore.similarity_search(query, k=self.k)


# Instantiate retriever
retriever = PineconeRetrieverWrapper(vectorstore=docsearch, k=3)

# Prompt template
prompt_template = """You are a medical assistant chatbot. Use the following context to answer the user's question.
If you don't know the answer, just say you don't know. Don't try to make up information.

Context: {context}

Question: {question}

Answer: """

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

# LLM
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    temperature=0.3,
    openai_api_key=OPENAI_API_KEY
)

# RetrievalQA chain
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": PROMPT},
    return_source_documents=True
)

# ------------------ Flask Routes ------------------


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/get", methods=["POST"])
def chat():
    try:
        msg = request.form["msg"]
        result = qa.invoke({"query": msg})
        response = result["result"]
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
