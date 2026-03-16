from openai import OpenAI
from backend.config import GROQ_API_KEY, API_BASE, MODEL_NAME

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=API_BASE
)

def generate_answer(context, question):

    prompt = f"""
Use the following context to answer the question.

Context:
{context}

Question:
{question}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
