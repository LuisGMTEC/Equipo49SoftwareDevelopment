import os

import firebase_admin
from dotenv import find_dotenv, load_dotenv
from firebase_admin import credentials, firestore
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from src.api.llm import generate_answer, generate_answer_using_openai

load_dotenv(find_dotenv())


if not firebase_admin._apps:
    # Opción 1: Usar archivo de credenciales
    # cred = credentials.Certificate("path/to/serviceAccountKey.json")

    # Opción 2: Usar credenciales por defecto (recomendado para producción)
    cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred)


db = firestore.client()
faqs_collection = db.collection("faqs")


def search_faqs(query: str) -> list[str]:
    """
    Very simple FAQ search: returns FAQ documents where
    'question' or 'answer' contains the query (case-insensitive).
    """

    # Example: full scan + filtering in Python (simple and works)
    docs = faqs_collection.stream()
    results = []

    q_lower = query.lower()

    for doc in docs:
        data = doc.to_dict()
        question = data.get("question", "")
        answer = data.get("answer", "")

        if q_lower in question.lower() or q_lower in answer.lower():
            results.append(f"Q: {question}\nA: {answer}")

    return results


def rag_answer(question: str) -> str:
    """
    Retrieves FAQ documents and calls the LLM to produce the final answer.
    """
    faqs = search_faqs(question)
    return generate_answer(question, faqs)


# region RAG usando vector store y OpenAI


def search_faqs_using_vector_store(query: str) -> str:
    # Se encesita la función de embeddings
    OPENAI_EMBEDDINGS_MODEL_DIMENSION = 1024
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large", dimensions=OPENAI_EMBEDDINGS_MODEL_DIMENSION
    )
    # Cargamos la vector store
    vector_store = FAISS.load_local(
        folder_path=os.getenv("VECTOR_STORE_FOLDER_PATH"),
        index_name="MeliFAQsIndex",
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
    # Eejcutamos la query vectorial
    docs = vector_store.similarity_search(query, k=3)
    # Obtenemos el resultado como un string
    result_string = "\n".join([_doc.page_content for _doc in docs])
    return result_string


def rag_answer_using_vector_store(question: str) -> str:
    faqs = search_faqs_using_vector_store(query=question)
    generated_answer = generate_answer_using_openai(question=question, context=faqs)
    return generated_answer
