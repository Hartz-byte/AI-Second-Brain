from backend.retriever import retrieve
from backend.llm_client import generate_answer

def ask_question(question):

    docs = retrieve(question)

    context = "\n".join(docs)

    answer = generate_answer(context, question)

    return answer
