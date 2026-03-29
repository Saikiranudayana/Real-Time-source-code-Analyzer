from git import Repo
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
import os


def repo_ingestion(repo_url: str, local_dir: str = "repo") -> str:
	os.makedirs(local_dir, exist_ok=True)

	if not os.listdir(local_dir):
		Repo.clone_from(repo_url, to_path=local_dir)

	return local_dir


def repo_ingejstion(repo_url: str, local_dir: str = "repo") -> str:
	# Backward-compatible alias for common misspelling.
	return repo_ingestion(repo_url=repo_url, local_dir=local_dir)


def load_repo(repo_path: str):
	loader = GenericLoader.from_filesystem(
		repo_path,
		glob="**/*",
		suffixes=[".py"],
		parser=LanguageParser(language=Language.PYTHON, parser_threshold=500),
	)
	documents = loader.load()
	return documents


def text_splitter(documents, chunk_size: int = 2000, chunk_overlap: int = 200):
	documents_splitter = RecursiveCharacterTextSplitter.from_language(
		language=Language.PYTHON,
		chunk_size=chunk_size,
		chunk_overlap=chunk_overlap,
	)
	text_chunks = documents_splitter.split_documents(documents)
	return text_chunks

def load_embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return embeddings

 