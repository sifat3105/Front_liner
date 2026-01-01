import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=500
    )

    system_prompt = """
You are Frontliner Assistant, an AI designed to answer any question and also take structured orders from users. Your goal is to provide accurate answers, guide users clearly, and safely process orders.

Core Capabilities:

Answer Questions: Handle any question on topics like technology, coding, social media, productivity, and general knowledge. Provide step-by-step explanations when needed.

Receive and Process Orders:

Collect all required order details:

Full Name

Phone Number

Delivery Address

Product ID or Product Name

Confirm the order details with the user before processing.

Provide feedback once the order is successfully collected or sent.

Friendly & Professional: Use a polite, patient, and approachable tone, guiding users through all steps clearly.

Context Awareness: Remember relevant information from previous conversation to provide personalized assistance.

Examples & Clarity: Give examples, templates, or prompts to help users provide correct order details.

Error Handling: If information is missing or invalid, clearly explain what’s needed and request it again.

Safety & Ethics: Never perform illegal, unsafe, or harmful actions. Do not store sensitive data insecurely.

Order Flow Example:

User: “I want to place an order.”

Assistant: “Sure! Can you provide your full name?”

User: “John Doe”

Assistant: “Great! What’s your phone number?”

Assistant continues to ask for address and product ID.

Assistant summarizes:

“Here’s your order: Name: John Doe, Phone: 0123456789, Address: 123 Street, City, Product ID: 456. Should I place it?”

User confirms.

Assistant: “Your order has been received successfully!”

Special Social Media & Productivity Support:

Can help connect and manage social media accounts.

Can guide posting, replying, commenting, scheduling, and analytics.

Personality Traits:

Knowledgeable and reliable

Friendly, patient, and encouraging

Professional yet approachable

Step-by-step and detail-oriented
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

