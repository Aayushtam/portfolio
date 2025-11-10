from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from typing import List, Optional
import os
import sys


def parse_resume(resume_path: str) -> str:
    loader = PyPDFLoader(resume_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=20)
    chunks = text_splitter.split_documents(documents)
    return chunks


def build_vectorstore(
    documents: List[Document],
    persist_directory: str = "./.chroma_resume",
    embedding_model: str = "mxbai-embed-large:latest",
) -> Chroma:
    """
    Build (or load) a Chroma vector store for the provided documents using Ollama embeddings.
    """
    os.makedirs(persist_directory, exist_ok=True)
    embeddings = OllamaEmbeddings(model=embedding_model)
    # If a persisted DB exists, load it and update; otherwise create fresh
    if any(os.scandir(persist_directory)):
        db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        # Optionally upsert new docs if content changed
        if documents:
            db.add_documents(documents)
        return db
    else:
        db = Chroma.from_documents(documents=documents, embedding=embeddings, persist_directory=persist_directory)
        db.persist()
        return db


def get_retriever(vectorstore: Chroma, k: int = 4):
    return vectorstore.as_retriever(search_kwargs={"k": k})


def make_llm(model: str = "qwen/qwen3-4b-2507", temperature: float = 0.2):
    """
    Create an Ollama chat LLM. Ensure `ollama serve` is running and the model is pulled locally.
    """
    return ChatOpenAI(model=model, temperature=temperature, base_url="http://localhost:1234/v1", api_key="ollama")


def answer_from_resume(
    question: str,
    retriever,
    llm: ChatOpenAI,
    system_instructions: Optional[str] = None,
) -> str:
    """
    Retrieve relevant chunks from the resume and answer grounded in those chunks.
    """
    # Modern retrievers are Runnable; prefer invoke() over get_relevant_documents()
    docs: List[Document] = retriever.invoke(question)
    context = "\n\n".join([f"[Chunk {i+1}]\n{d.page_content}" for i, d in enumerate(docs)])

    default_system = (
        "You are a helpful personal assistant for Aayush Tamrakar. "
        "Answer ONLY using the information in the provided resume context. "
        "If the answer is not present in the context, say you don't know. "
        "Be concise and factual."
    )
    system_text = system_instructions or default_system

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_text),
            ("human", "Resume context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | llm
    result = chain.invoke({"context": context, "question": question})
    return result.content if hasattr(result, "content") else str(result)


def ensure_resume_path(default_path: str = "./sources/AayushTamrakarResume.pdf") -> str:
    """
    Determine the resume path to use. Prefer CLI arg if provided; else default path.
    """
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        resume_path = default_path
    if not os.path.exists(resume_path):
        raise FileNotFoundError(
            f"Resume PDF not found at '{resume_path}'. "
            f"Provide the path as an argument or place it at the default."
        )
    return resume_path


def interactive_cli():
    """
    Run an interactive CLI that answers questions from the resume.
    Usage:
        python personal_assistant.py [optional_path_to_resume_pdf]
    """
    try:
        resume_path = ensure_resume_path()
        print(f"Loading resume from: {resume_path}")
        chunks = parse_resume(resume_path)
        print(f"Parsed {len(chunks)} chunks.")
        vectordb = build_vectorstore(chunks)
        retriever = get_retriever(vectordb, k=4)
        llm = make_llm(model="llama3.2", temperature=0.2)

        print("\nPersonal Resume Assistant ready. Ask me about Aayush!")
        print("Type 'exit' or 'quit' to end.\n")
        while True:
            try:
                user_q = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break
            if not user_q:
                continue
            if user_q.lower() in {"exit", "quit"}:
                print("Goodbye.")
                break
            answer = answer_from_resume(user_q, retriever, llm)
            print(f"\nAssistant: {answer}\n")
    except Exception as e:
        print(f"Error: {e}")
        print(
            "\nTroubleshooting tips:\n"
            "- Ensure `ollama` is installed and running: `ollama serve`\n"
            "- Pull required models, e.g.: `ollama pull llama3.2` and `ollama pull nomic-embed-text`\n"
            "- Ensure LangChain, langchain_ollama, langchain_community, and Chroma are installed in your environment.\n"
            "- Verify the resume PDF path is correct."
        )


if __name__ == "__main__":
    interactive_cli()
