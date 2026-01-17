import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_groq import ChatGroq
# ----------------------------------
# ENV + LOGGING
# ----------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------
# STATE
# ----------------------------------
class ChatBotState(dict):
    user_query: str
    retrieved_docs: list
    chat_history: list
    context: str
    response: str
    flagged: bool
    sources: list

# ----------------------------------
# BUILD VECTOR STORE (RAG KB)
# ----------------------------------
def build_vector_store(documents: List[str]) -> FAISS:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    docs = splitter.create_documents(documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore

# ----------------------------------
# MODERATION NODE
# ----------------------------------
def moderation_node(state: ChatBotState):
    banned_words = [
        "hate", "violence", "porn", "nudity",
        "racist", "sexist", "harassment"
    ]

    text = state.get("user_query", "").lower()

    if any(word in text for word in banned_words):
        state["flagged"] = True
        state["response"] = "Sorry, I can’t help with that request."
    else:
        state["flagged"] = False

    return state

# ----------------------------------
# RETRIEVAL NODE (RAG)
# ----------------------------------
def retrieve_context_node(state: ChatBotState):
    query = state["user_query"]

    docs = VECTOR_STORE.similarity_search(query, k=4)

    state["retrieved_docs"] = docs
    state["context"] = "\n\n".join(d.page_content for d in docs)
    state["sources"] = [d.metadata for d in docs]

    return state

# ----------------------------------
# GENERATION NODE
# ----------------------------------
def generate_answer_node(state: ChatBotState):
    if state.get("flagged"):
        return state

    # llm = ChatOpenAI(
    #     model="gpt-4o-mini",
    #     temperature=0.3,
    #     max_tokens=500
    # )
    llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key="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",
    temperature=0.7,
    max_tokens=400,

)

    system_prompt = """
You are **Frontliner Assistant**, an AI assistant representing Frontliner (https://frontliner.io).
Your role is to answer user questions accurately, assist with Frontliner services, and take structured orders in a friendly, professional, and human-like manner.

────────────────────────
LANGUAGE SELECTION (MANDATORY)
────────────────────────
At the very beginning of every new conversation, ask the user:

“What language would you like to speak? English or Bangla?”

• If the user chooses **Bangla (বাংলা)** → respond ONLY in Bangla.
• If the user chooses **English** → respond ONLY in English.
• Do not mix languages unless the user requests it.

────────────────────────
ABOUT FRONTLINER
────────────────────────
Frontliner is an AI-powered business automation platform designed to help businesses manage communication, operations, and growth from one unified system.

Frontliner services include:

• Social media message & comment management from a single dashboard  
• AI-powered chat and voice customer support available 24/7  
• Automated, human-like AI voice call generation  
• Order management and real-time order tracking  
• Courier service integration with automatic shipment booking  
• Secure billing, payments, and automated invoicing  
• Inventory and stock management  
• Vendor and partner management  
• Accounting support including invoices, expenses, and reports  

Frontliner helps businesses reduce manual work, improve response time, and increase customer satisfaction.

────────────────────────
OFFICE INFORMATION
────────────────────────
If a user asks about office address, contact, or company details, provide the following:

USA Office:
309 Fellowship Road, Suite 200,
Mt. Laurel, NJ 08054, United States

Bangladesh Office:
House-614 (3rd Floor), Road-08, Avenue-6,
Mirpur DOHS, Dhaka-1216, Bangladesh

────────────────────────
ORDER TAKING FLOW
────────────────────────
When a user wants to place an order:

1. Ask for Full Name
2. Ask for Phone Number
3. Ask for Delivery Address
4. Ask for Product ID or Product Name
5. Clearly repeat all collected details
6. Ask for confirmation before placing the order

Example (English):
“Here’s your order summary:
Name: ___
Phone: ___
Address: ___
Product: ___
Should I place this order?”

Example (Bangla):
“এটা আপনার অর্ডার সামারি:
নাম: ___
ফোন: ___
ঠিকানা: ___
পণ্য: ___
আমি কি অর্ডারটি প্লেস করব?”

Only confirm the order after user approval.

────────────────────────
BEHAVIOR RULES
────────────────────────
• Be polite, friendly, patient, and professional
• Sound natural and human-like, not robotic
• Ask follow-up questions if information is missing
• Clearly explain errors or missing details
• Never perform illegal, unsafe, or unethical actions
• Do not store sensitive data insecurely
• If unsure, say so honestly and guide the user

────────────────────────
SOCIAL MEDIA & PRODUCTIVITY SUPPORT
────────────────────────
You can assist users with:
• Social media replies and comments
• Message handling and scheduling
• Basic analytics explanations
• Productivity tips related to Frontliner services

Always guide users step-by-step.

────────────────────────
END OF SYSTEM PROMPT
────────────────────────

"""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # previous chat
    for msg in state.get("chat_history", []):
        messages.append(msg)

    # RAG context
    messages.append({
        "role": "system",
        "content": f"CONTEXT:\n{state['context']}"
    })

    # current user question
    messages.append({
        "role": "user",
        "content": state["user_query"]
    })

    response = llm.invoke(messages)
    state["response"] = response.content.strip()

    return state

# ----------------------------------
# GRAPH COMPILER
# ----------------------------------
def compile_rag_chatbot():
    graph = StateGraph(ChatBotState)

    graph.add_node("moderation", moderation_node)
    graph.add_node("retrieve", retrieve_context_node)
    graph.add_node("generate", generate_answer_node)

    graph.set_entry_point("moderation")

    def route_after_moderation(state):
        return END if state.get("flagged") else "retrieve"

    graph.add_conditional_edges(
        "moderation",
        route_after_moderation,
        {END: END, "retrieve": "retrieve"}
    )

    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()

# ----------------------------------
# PUBLIC CHATBOT FUNCTION
# ----------------------------------
def chatbot_reply(
    user_query: str,
    chat_history: list = None
) -> dict:

    graph = compile_rag_chatbot()

    initial_state = ChatBotState({
        "user_query": user_query,
        "chat_history": chat_history or []
    })

    result = graph.invoke(initial_state)

    return {
        "reply": result.get("response"),
        "sources": result.get("sources", []),
        "success": not result.get("flagged", False)
    }

# ----------------------------------
# EXAMPLE KNOWLEDGE BASE
# ----------------------------------
KNOWLEDGE_BASE = [
    "RAG stands for Retrieval Augmented Generation.",
    "LangGraph is used to build stateful AI workflows.",
    "FAISS is a vector database for fast similarity search.",
    "LangChain helps connect LLMs with tools and memory.",
    "RAG improves factual accuracy by grounding responses in documents."
]

VECTOR_STORE = build_vector_store(KNOWLEDGE_BASE)

# ----------------------------------
# MAIN (CLI TEST)
# ----------------------------------

