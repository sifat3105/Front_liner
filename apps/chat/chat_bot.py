# chat_bot.py
from functools import lru_cache
import json
import os
import logging
import re
from typing import List, Dict, Any, Optional, TypedDict

from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .services.attachment_loader import download_images
from .services.ocr import analyze_image  # ✅ OCR + Vision Caption (must exist)
from langchain_tools.inventory_tools import search_inventory_products, list_inventory_products

# ----------------------------------
# ENV + LOGGING
# ----------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------
# STATE
# ----------------------------------
class ChatBotState(TypedDict, total=False):
    user_query: str
    chat_history: List[Dict[str, Any]]
    owner_user_id: Optional[int]

    attachments: List[Dict[str, Any]]
    attachment_text: str  # OCR + Vision caption combined text

    retrieved_docs: List[Any]
    context: str
    inventory_context: str
    inventory_result: Dict[str, Any]
    response: str
    force_response: bool
    flagged: bool
    sources: List[Any]

    # language control
    language: str  # "bn" or "en"

# ----------------------------------
# KNOWLEDGE BASE / VECTOR STORE
# ----------------------------------
KNOWLEDGE_BASE = [
    "RAG stands for Retrieval Augmented Generation.",
    "LangGraph is used to build stateful AI workflows.",
    "FAISS is a vector database for fast similarity search.",
    "LangChain helps connect LLMs with tools and memory.",
    "RAG improves factual accuracy by grounding responses in documents."
]

def build_vector_store(documents: List[str]) -> FAISS:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.create_documents(documents)
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(docs, embeddings)

@lru_cache(maxsize=1)
def get_vector_store() -> FAISS:
    return build_vector_store(KNOWLEDGE_BASE)

VECTOR_STORE = get_vector_store()

# ----------------------------------
# HELPERS
# ----------------------------------
def _detect_language_choice(text: str) -> Optional[str]:
    """
    Returns:
      "bn" if user chose Bangla
      "en" if user chose English
      None if not chosen clearly
    """
    t = (text or "").strip().lower()

    # Bangla signals
    if "বাংলা" in text or "bangla" in t or "bn" == t:
        return "bn"

    # English signals
    if "english" in t or "ইংরেজি" in text or "en" == t:
        return "en"

    return None

def _is_new_conversation(chat_history: List[Dict[str, Any]]) -> bool:
    return not chat_history or len(chat_history) == 0

def _clean_sources(docs: List[Any]) -> List[Any]:
    out = []
    for d in docs or []:
        md = getattr(d, "metadata", None)
        out.append(md if md is not None else {})
    return out


def _last_assistant_message(chat_history: List[Dict[str, Any]]) -> str:
    for msg in reversed(chat_history or []):
        if msg.get("role") == "assistant":
            return msg.get("content") or ""
    return ""

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text or "", re.S)
        if not match:
            return None
        try:
            return json.loads(match.group())
        except Exception:
            return None

def _detect_inventory_intent_llm(user_query: str, chat_history: List[Dict[str, Any]]) -> str:
    """
    Returns: "list" | "search" | "none"
    Uses LLM so it's language-agnostic and not keyword-based.
    """
    if not (user_query or "").strip():
        return "none"

    last_assistant = _last_assistant_message(chat_history)
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        temperature=0.0,
        max_tokens=60
    )

    system = (
        "You are an intent classifier for a retail chat assistant. "
        "Decide if the user is asking for a product list, asking about a specific product "
        "(availability/price/details), or not about inventory. "
        "Return JSON only: {\"intent\": \"list\"|\"search\"|\"none\"}.\n"
        "- If the user asks to show/list all products or to send the list again, intent=list.\n"
        "- If the user mentions a specific product, brand, size, color, SKU-like code, or asks price/availability "
        "for a particular item, intent=search.\n"
        "- Otherwise intent=none.\n"
        "You must handle any language, including Bangla."
    )

    user = f"User message:\n{user_query}\n\nLast assistant message:\n{last_assistant or '(none)'}"

    try:
        resp = llm.invoke([
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ])
        parsed = _extract_json(getattr(resp, "content", "") or "")
        intent = (parsed or {}).get("intent") if parsed else None
        if intent in {"list", "search", "none"}:
            return intent
    except Exception as e:
        logger.exception(f"Intent classifier failed: {e}")

    return "none"

def _guess_language(text: str) -> str:
    choice = _detect_language_choice(text)
    if choice:
        return choice
    if re.search(r"[\u0980-\u09FF]", text or ""):
        return "bn"
    return "en"

def _format_sell_price(price_min: Optional[str], price_max: Optional[str]) -> Optional[str]:
    if price_min is None and price_max is None:
        return None
    min_str = str(price_min) if price_min is not None else None
    max_str = str(price_max) if price_max is not None else None
    if min_str and max_str:
        return min_str if min_str == max_str else f"{min_str} - {max_str}"
    return min_str or max_str

def _format_inventory_list_response(result: Dict[str, Any], lang: str) -> str:
    products = (result or {}).get("products") or []
    if not products:
        return "দুঃখিত, এখন কোনো প্রোডাক্ট পাওয়া যায়নি।" if lang == "bn" else "Sorry, no products were found right now."

    if lang == "bn":
        header = "আপনার জন্য প্রোডাক্ট লিস্ট:"
        name_label = "পণ্যের নাম"
        brand_label = "ব্র্যান্ড"
        price_label = "সেল প্রাইস"
        image_label = "ছবি"
    else:
        header = "Here are the available products:"
        name_label = "Product"
        brand_label = "Brand"
        price_label = "Sell Price"
        image_label = "Image"

    lines = [header]
    for idx, product in enumerate(products, start=1):
        name = product.get("name") or ("নাম নেই" if lang == "bn" else "Unnamed product")
        brand = product.get("brand")
        image_url = product.get("image_url")
        price_text = _format_sell_price(product.get("price_min"), product.get("price_max"))

        lines.append("")
        lines.append(f"{idx}.")
        if image_url:
            lines.append(f"{image_label}: {image_url}")
        lines.append(f"{name_label}: {name}")
        if brand:
            lines.append(f"{brand_label}: {brand}")
        if price_text:
            lines.append(f"{price_label}: {price_text}")

    return "\n".join(lines).strip()

# ----------------------------------
# NODE 0: LANGUAGE GATE (hard rule)
# ----------------------------------
def language_gate_node(state: ChatBotState) -> ChatBotState:

    user_query = state.get("user_query", "")
    chat_history = state.get("chat_history", [])

    # If conversation already started, do nothing
    if not _is_new_conversation(chat_history):
        return state

    # If user already chose language in first message, store it
    lang = _detect_language_choice(user_query)
    if lang:
        state["language"] = lang
        return state

    # Otherwise, force the language selection question and stop graph
    state["flagged"] = True  # reuse flagged to stop routing
    state["response"] = "What language would you like to speak? English or Bangla?"
    return state

# ----------------------------------
# MODERATION NODE (basic)
# ----------------------------------
def moderation_node(state: ChatBotState) -> ChatBotState:
    """
    Keep this lightweight. (Your list is very broad; avoid blocking normal users.)
    """
    banned_words = [
        "child porn", "cp", "rape", "sex with minors",
        "terrorist attack", "make a bomb",
    ]
    text = (state.get("user_query", "") or "").lower()

    if any(word in text for word in banned_words):
        state["flagged"] = True
        # Respect language preference if already set
        if state.get("language") == "bn":
            state["response"] = "দুঃখিত, আমি এই অনুরোধে সাহায্য করতে পারব না।"
        else:
            state["response"] = "Sorry, I can’t help with that request."
    else:
        state["flagged"] = False

    return state

# ----------------------------------
# PROCESS IMAGES NODE (OCR + Vision Caption)
# ----------------------------------
def process_images_node(state: ChatBotState) -> ChatBotState:
    attachments = state.get("attachments", []) or []
    if not attachments:
        state["attachment_text"] = ""
        return state

    # Download images safely
    try:
        images = download_images(attachments)
    except Exception as e:
        logger.exception(f"download_images failed: {e}")
        state["attachment_text"] = ""
        return state

    if not images:
        logger.warning("No images downloaded from attachments.")
        state["attachment_text"] = ""
        return state

    extracted_blocks = []
    for i, img in enumerate(images, start=1):
        img_bytes = img.get("bytes")
        content_type = img.get("content_type", "image/jpeg")
        url = img.get("url", "")

        if not img_bytes:
            extracted_blocks.append(f"[IMAGE {i}]\nURL: {url}\n[ERROR] Missing image bytes.\n")
            continue

        try:
            result = analyze_image(image_bytes=img_bytes, content_type=content_type)
            caption = (result.get("caption") or "").strip()
            ocr_text = (result.get("ocr_text") or "").strip()
        except Exception as e:
            logger.exception(f"analyze_image failed for image {i}: {e}")
            caption = ""
            ocr_text = f"[IMAGE_ANALYSIS_ERROR] {type(e).__name__}: {e}"

        extracted_blocks.append(
            f"""[IMAGE {i}]
URL: {url}

[VISION CAPTION]
{caption if caption else "(no caption extracted)"}

[OCR TEXT]
{ocr_text if ocr_text else "(no text extracted)"}
"""
        )

    state["attachment_text"] = "\n\n".join(extracted_blocks).strip()
    return state

# ----------------------------------
# RETRIEVAL NODE (RAG)
# ----------------------------------
def retrieve_context_node(state: ChatBotState) -> ChatBotState:
    query = state.get("user_query", "") or ""
    if not query.strip():
        state["retrieved_docs"] = []
        state["context"] = ""
        state["sources"] = []
        return state

    try:
        docs = VECTOR_STORE.similarity_search(query, k=4)
    except Exception as e:
        logger.exception(f"Vector search failed: {e}")
        docs = []

    state["retrieved_docs"] = docs
    state["context"] = "\n\n".join(getattr(d, "page_content", "") for d in docs if d)
    state["sources"] = _clean_sources(docs)
    return state


# ----------------------------------
# INVENTORY CONTEXT NODE (tools)
# ----------------------------------
def inventory_context_node(state: ChatBotState) -> ChatBotState:
    user_query = state.get("user_query", "") or ""
    chat_history = state.get("chat_history", []) or []
    owner_user_id = state.get("owner_user_id")
    if not owner_user_id:
        state["inventory_context"] = ""
        return state

    intent = _detect_inventory_intent_llm(user_query, chat_history)
    if intent == "none":
        state["inventory_context"] = ""
        return state

    list_mode = intent == "list"

    try:
        if list_mode:
            result = list_inventory_products.invoke({
                "user_id": owner_user_id,
                "limit": 8,
                "status": "published",
            })
        else:
            result = search_inventory_products.invoke({
                "user_id": owner_user_id,
                "query": user_query,
                "limit": 8,
                "status": "published",
                "variant_limit": 5,
            })
    except Exception as e:
        logger.exception(f"Inventory tool failed: {e}")
        state["inventory_context"] = ""
        return state

    state["inventory_result"] = result

    if list_mode:
        lang = state.get("language") or _guess_language(user_query)
        state["response"] = _format_inventory_list_response(result, lang)
        state["force_response"] = True
        state["inventory_context"] = ""
        return state

    try:
        state["inventory_context"] = json.dumps(result, ensure_ascii=False)
    except Exception:
        state["inventory_context"] = str(result)
    return state

# ----------------------------------
# GENERATION NODE
# ----------------------------------
def generate_answer_node(state: ChatBotState) -> ChatBotState:
    if state.get("force_response") and state.get("response"):
        return state
    # If flagged (moderation OR language gate used flagged to stop)
    if state.get("flagged") and state.get("response"):
        return state

    # Determine language if not set yet (for ongoing chat, user may say bangla/english)
    if not state.get("language"):
        choice = _detect_language_choice(state.get("user_query", ""))
        if choice:
            state["language"] = choice

    lang = state.get("language") or "en"

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        temperature=0.3,
        max_tokens=600
    )

    # ✅ Strong instruction: NEVER say "I can’t see the image" if we provide analysis text
    system_prompt_bn = """
আপনি **Frontliner Assistant** (https://frontliner.io)।
আপনি ব্যবহারকারীকে সঠিকভাবে সাহায্য করবেন, বন্ধুসুলভ ও প্রফেশনাল ভাষায় উত্তর দেবেন।

গুরুত্বপূর্ণ নিয়ম:
- আপনি ছবি সরাসরি দেখছেন না। কিন্তু আমরা আপনাকে [VISION CAPTION] এবং [OCR TEXT] দিয়ে দেব।
- যদি [VISION CAPTION]/[OCR TEXT] দেওয়া থাকে, তাহলে কখনো বলবেন না “আমি ছবি দেখতে পারি না”।
- আপনি ওই তথ্য ব্যবহার করে উত্তর দেবেন। অনিশ্চিত হলে “নিশ্চিত নই” বলবেন এবং কী তথ্য লাগবে জিজ্ঞেস করবেন।
- যদি ইউজার “এটা আছে কি না?” জিজ্ঞেস করে, আপনি ইনভেন্টরি ডাটা না পেলে পরিষ্কারভাবে বলবেন যে নিশ্চিত করতে প্রোডাক্ট নাম/কোড/বারকোড বা আপনার সিস্টেমের ইনভেন্টরি সোর্স প্রয়োজন।
- যদি INVENTORY_CONTEXT দেওয়া থাকে, সেটি ব্যবহার করে প্রোডাক্ট, স্টক, দাম বা লিস্ট সম্পর্কে উত্তর দিন।
- কাস্টমারের কাছে কোনো ইন্টারনাল আইডি/ভেন্ডর আইডি/SKU/ভ্যারিয়েন্ট SKU দেখাবেন না।
- প্রোডাক্ট লিস্টে শুধু ছবি (থাকলে), নাম, ব্র্যান্ড (থাকলে) এবং সেল প্রাইস দেখাবেন। স্টক, স্ট্যাটাস বা ভ্যারিয়েন্ট বিস্তারিত দেখাবেন না।
"""

    system_prompt_en = """
You are **Frontliner Assistant** (https://frontliner.io).
You answer accurately, friendly and professional.

Important rules:
- You cannot see images directly, but you WILL be given [VISION CAPTION] and [OCR TEXT].
- If [VISION CAPTION]/[OCR TEXT] is present, NEVER say “I can’t see the image.”
- Use the provided image analysis to answer. If uncertain, say you’re not sure and ask what info is needed.
- If the user asks “is this available?”, and you do not have inventory data, clearly state what you need (product name/code/barcode or access to inventory source).
- If INVENTORY_CONTEXT is provided, use it to answer product, stock, price, or product list questions.
- Never expose internal IDs, vendor IDs, SKUs, or variant SKUs to customers.
- When listing products, show only image (if available), name, brand (if available), and sell price. Do not show stock, status, or variant details.
"""

    system_prompt = system_prompt_bn if lang == "bn" else system_prompt_en

    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

    # previous chat
    for msg in state.get("chat_history", []) or []:
        # keep only valid message shapes
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append(msg)

    # RAG context
    context_text = (state.get("context") or "").strip()
    if context_text:
        messages.append({"role": "system", "content": f"CONTEXT:\n{context_text}"})

    # Inventory context (tool output)
    inventory_text = (state.get("inventory_context") or "").strip()
    if inventory_text:
        messages.append({"role": "system", "content": f"INVENTORY_CONTEXT:\n{inventory_text}"})

    # current user question + image analysis (if any)
    user_content = (state.get("user_query") or "").strip()
    attachment_text = (state.get("attachment_text") or "").strip()
    if attachment_text:
        user_content += "\n\n[ATTACHED IMAGE ANALYSIS]\n" + attachment_text

    messages.append({"role": "user", "content": user_content})

    try:
        resp = llm.invoke(messages)
        state["response"] = (resp.content or "").strip()
    except Exception as e:
        logger.exception(f"LLM invoke failed: {e}")
        if lang == "bn":
            state["response"] = "দুঃখিত, এই মুহূর্তে উত্তর তৈরি করতে সমস্যা হচ্ছে। পরে আবার চেষ্টা করুন।"
        else:
            state["response"] = "Sorry, I’m having trouble generating a reply right now. Please try again."

    # Debug logs (safe)
    logger.info(f"Attachments received: {state.get('attachments')}")
    logger.info(f"Attachment_text length: {len(state.get('attachment_text') or '')}")
    logger.info(f"User query final length: {len(user_content)}")

    return state

# ----------------------------------
# GRAPH COMPILER (cached)
# ----------------------------------
_GRAPH = None

def compile_rag_chatbot():
    graph = StateGraph(ChatBotState)

    graph.add_node("language_gate", language_gate_node)
    graph.add_node("moderation", moderation_node)
    graph.add_node("process_images", process_images_node)
    graph.add_node("retrieve", retrieve_context_node)
    graph.add_node("inventory_context", inventory_context_node)
    graph.add_node("generate", generate_answer_node)

    graph.set_entry_point("language_gate")

    def route_after_language_gate(state: ChatBotState):
        # language gate uses flagged+response to stop
        return END if state.get("flagged") and state.get("response") else "moderation"

    graph.add_conditional_edges(
        "language_gate",
        route_after_language_gate,
        {END: END, "moderation": "moderation"},
    )

    def route_after_moderation(state: ChatBotState):
        return END if state.get("flagged") else "process_images"

    graph.add_conditional_edges(
        "moderation",
        route_after_moderation,
        {END: END, "process_images": "process_images"},
    )

    graph.add_edge("process_images", "retrieve")
    graph.add_edge("retrieve", "inventory_context")
    graph.add_edge("inventory_context", "generate")
    graph.add_edge("generate", END)

    return graph.compile()

# ----------------------------------
# PUBLIC CHATBOT FUNCTION
# ----------------------------------
def chatbot_reply(
    user_query: str,
    chat_history: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    owner_user_id: Optional[int] = None,
) -> Dict[str, Any]:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = compile_rag_chatbot()

    initial_state: ChatBotState = {
        "user_query": user_query,
        "chat_history": chat_history or [],
        "owner_user_id": owner_user_id,
        "attachments": attachments or [],
        "attachment_text": "",
        "context": "",
        "inventory_context": "",
        "inventory_result": {},
        "sources": [],
        "flagged": False,
        "force_response": False,
    }

    result = _GRAPH.invoke(initial_state)

    return {
        "reply": result.get("response"),
        "sources": result.get("sources", []),
        "success": not (result.get("flagged", False) and bool(result.get("response"))),
        "inventory_result": result.get("inventory_result"),
    }
