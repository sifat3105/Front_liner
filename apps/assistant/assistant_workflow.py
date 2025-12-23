import json, re, logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from django.conf import settings
from .models import Assistant, AssistantFile
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)



class AssistantState(Dict[str, Any]):
    input_text: str
    history: list
    memory: dict
    flagged: bool = False
    answer: str = ""
    memory_update: dict = None
    user_id: int = None
    session_id: int = None
    call_support_api: Optional[Dict[str, Any]] = None



def compile_dynamic_agent(assistant: Assistant):
    """
    Dynamically compile a LangGraph for a given Assistant instance.
    """

    # Load assistant configuration
    # model_name = assistant.model or "gpt-4o-mini"
    temp = assistant.temperature or 0.7
    max_tokens = assistant.max_tokens or 250
    system_prompt = assistant.system_prompt or "You are a helpful assistant."
    crisis_prompt = assistant.crisis_keywords_prompt.strip() if assistant.crisis_keywords_prompt else None

    # Parse crisis keywords
    crisis_keywords = []
    if assistant.crisis_keywords:
        crisis_keywords = [k.strip().lower() for k in assistant.crisis_keywords.split(",") if k.strip()]
    else:
        crisis_keywords = [
            "suicide", "kill myself", "end my life", "want to die",
            "hurt myself", "self-harm", "danger to myself"
        ]

    # Load any attached text files into memory context
    file_context = ""
    for f in assistant.files.all():
        try:
            file_context += "\n" + f.file.read().decode("utf-8")
        except Exception as e:
            logger.warning(f"Could not read file {f.file.name}: {e}")


    # Build the LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=temp,
        max_tokens=max_tokens,
    )
    # llm = ChatGroq(
    # model="llama-3.3-70b-versatile",
    # api_key="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",
    # temperature=temp,
    # max_tokens=max_tokens,
# )

    # Define nodes
    def safety_check(state: AssistantState):
        text = (state.get("input_text") or "").lower()
        history_text = " ".join([str(m.get("text", "")).lower() for m in state.get("history", [])])
        flagged = any(k in text for k in crisis_keywords) or any(k in history_text for k in crisis_keywords)

        if flagged:
            state["flagged"] = True
            state["answer"] = crisis_prompt or (
                "I'm really concerned about your safety. Please reach out to emergency services or a trusted person immediately. "
                "Would you like me to share local mental health hotlines?"
            )
            return state

        state["flagged"] = False
        return state

    def call_llm(state: AssistantState):
        if state.get("flagged"):
            return state

        user_text = state.get("input_text", "")
        memory = state.get("memory", {}) or {}
        history = state.get("history", []) or []
        formatted_history = ""
        for msg in history:
            sender = msg.get("sender", "user")
            text = msg.get("text", "")
            formatted_history += f"{sender.capitalize()}: {text}\n"

        prompt = f"""
{system_prompt}

User message: {user_text}

Assistant memory: {memory}

History: {formatted_history}

Attached context: {file_context}

Respond in JSON ONLY with:
- "reply": your message to the user
- optional "remember": a short key:value memory update
"""

        try:
            response = llm.invoke(prompt)
            content = getattr(response, "content", "") or str(response)
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", content, re.S)
                parsed = json.loads(json_match.group()) if json_match else {"reply": content}

            state["answer"] = parsed.get("reply", "I'm here to listen.")
            if "remember" in parsed:
                state["memory_update"] = parsed["remember"]
            if "call_support_api" in parsed:
                state["call_support_api"] = parsed["call_support_api"]
                print(f"call_support_api: {state['call_support_api']}")

        except Exception as e:
            print(f"LLM error: {e}")
            logger.error(f"LLM error: {e}")
            state["answer"] = "I’m having trouble responding right now."
        return state

    def write_memory(state: AssistantState):
        memory_update = state.get("memory_update")
        if memory_update:
            memory = state.get("memory", {}) or {}
            memory.update(memory_update)
            state["memory"] = memory
        return state

    # --------------------------
    # Build graph
    # --------------------------
    workflow = StateGraph(AssistantState)
    workflow.add_node("safety_check", safety_check)
    workflow.add_node("llm_node", call_llm)
    workflow.add_node("memory_node", write_memory)
    workflow.set_entry_point("safety_check")

    # conditional edges
    def after_safety(state):
        return END if state.get("flagged") else "llm_node"

    workflow.add_conditional_edges("safety_check", after_safety, {"llm_node": "llm_node", END: END})

    def after_llm(state):
        return "memory_node" if state.get("memory_update") else END

    workflow.add_conditional_edges("llm_node", after_llm, {"memory_node": "memory_node", END: END})
    workflow.add_edge("memory_node", END)

    return workflow.compile()



# from shared.shared_agent import compile_dynamic_agent as cda

# def compile_dynamic_agent(assistant: Assistant):
#     config = {
#         "temperature": assistant.temperature,
#         "max_tokens": assistant.max_tokens,
#         "system_prompt": assistant.system_prompt,
#         "crisis_prompt": assistant.crisis_keywords_prompt,
#         "crisis_keywords": assistant.crisis_keywords.split(",") if assistant.crisis_keywords else [],
#         "llm_api_key": "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",
#     }

#     # load files
#     file_context = ""
#     for f in assistant.files.all():
#         file_context += "\n" + f.file.read().decode("utf-8")

#     return cda(config, file_context)
