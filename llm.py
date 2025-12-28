# vehi_agent/llm.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0.0
)

def groq_llm(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content
