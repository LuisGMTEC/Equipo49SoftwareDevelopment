from google import genai
from langchain_openai import ChatOpenAI

client = genai.Client(api_key="...")


def generate_answer(question: str, retrieved_docs: list[str]) -> str:
    """
    Calls Gemini with the user question and retrieved FAQ knowledge.
    """
    context = (
        "\n\n".join(retrieved_docs) if retrieved_docs else "No FAQ data available."
    )

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


def generate_answer_using_openai(question: str, context: str) -> str:
    """
    Calls Gemini with the user question and retrieved FAQ knowledge.
    """
    system_prompt = f"""
You are an assistant answering user questions based on the following FAQ knowledge.

FAQ Knowledge:
{context}

User question:
{question}

Provide a helpful, concise answer. If the answer is not present in the FAQs, say so.
"""

    llm = ChatOpenAI(
        model="gpt-5-nano",
    )
    messages = [
        (
            "system",
            system_prompt,
        ),
        ("human", question),
    ]
    ai_msg = llm.invoke(messages)
    return ai_msg.content
