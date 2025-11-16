from src.api.llm import generate_answer
import firebase_admin
from firebase_admin import credentials, firestore


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