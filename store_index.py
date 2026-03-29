from src.helper import repo_ingestion, load_repo, text_splitter, load_embeddings
from dot_env import load_dotenv
from langchain_community.vectorstores import chromadb
import os 


load_dotenv()

#url = "https://github.com/entbappy/End-to-End-Medical-Chatbot"

#repo_ingestion(repo_url=url, local_dir="repo")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

documents = load_repo(repo_path="repo")

text_chunks = text_splitter(documents=documents)

embeddings = load_embeddings()


vectordb = chromadb.ChromaDB.from_documents(texts=text_chunks, embedding=embeddings,persist_directory="./vectordb")
vectordb.persist()

