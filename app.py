import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryMemory
from src.helper import load_embeddings, repo_ingestion, load_repo, text_splitter

app = Flask(__name__)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment or .env file")
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

embeddings = load_embeddings()
persist_directory = "db"


def _build_chain():
    """Build retrieval chain from persisted vector store."""
    vectordb = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    llm = ChatGroq(
        model_name="llama-3.1-8b-instant",
        temperature=0,
        groq_api_key=GROQ_API_KEY,
    )
    memory = ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history",
        return_messages=True,
    )
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 8}),
        memory=memory,
    )
    return chain


# Initialise lazily so the app starts even before any repo is ingested
qa_chain = None


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/chatbot", methods=["POST"])
def chatbot():
    """Clone, embed, and persist a GitHub repository."""
    global qa_chain

    data = request.get_json(silent=True) or {}
    github_url = data.get("github_url", "").strip()

    if not github_url:
        return jsonify({"error": "github_url is required"}), 400

    try:
        # Clone / reuse repo
        repo_path = repo_ingestion(repo_url=github_url)

        # Load .py files
        documents = load_repo(repo_path)
        if not documents:
            return jsonify({"error": "No Python files found in repository"}), 422

        # Split into chunks
        chunks = text_splitter(documents)

        # Build and persist vector store
        vectordb = Chroma.from_documents(
            chunks,
            embedding=embeddings,
            persist_directory=persist_directory,
        )
        vectordb.persist()

        # Rebuild chain with fresh vector store
        qa_chain = _build_chain()

        return jsonify({
            "message": f"Repository indexed successfully — {len(chunks)} chunks stored."
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get", methods=["POST"])
def get_answer():
    """Answer a question about the indexed codebase."""
    global qa_chain

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "question is required"}), 400

    if qa_chain is None:
        # Try to load from persisted store if it exists
        if os.path.exists(persist_directory):
            try:
                qa_chain = _build_chain()
            except Exception as e:
                return jsonify({"error": f"Could not load index: {str(e)}"}), 500
        else:
            return jsonify({"error": "No repository indexed yet. Please ingest a repo first."}), 400

    try:
        result = qa_chain.run(question)
        return jsonify({"answer": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
