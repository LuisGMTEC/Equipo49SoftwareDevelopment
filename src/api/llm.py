from google import genai

client = genai.Client(api_key="...")

def generate_answer(question: str, retrieved_docs: list[str]) -> str:
    """
    Calls Gemini with the user question and retrieved FAQ knowledge.
    """
    context = "\n\n".join(retrieved_docs) if retrieved_docs else "No FAQ data available."

    prompt = f"""
You are an assistant answering user questions based on the following FAQ knowledge.

FAQ Knowledge:
{context}

User question:
{question}

Provide a helpful, concise answer. If the answer is not present in the FAQs, say so.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text