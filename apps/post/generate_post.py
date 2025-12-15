import json
import re
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# -----------------------------
# STATE
# -----------------------------
class CaptionGeneratorState(dict):
    input_text: str
    topic: str
    platform: str
    tone: str
    hashtags: List[str]
    emojis: bool
    call_to_action: str
    max_length: int
    caption_variants: List[str]
    selected_caption: str
    flagged: bool
    image_description: str
    formatted_caption: str
    character_count: int
    word_count: int
    within_limit: bool


# -----------------------------
# GRAPH COMPILER
# -----------------------------
def compile_social_caption_generator():

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.8,
        max_tokens=600,
    )

    # -----------------------------
    # MODERATION
    # -----------------------------
    def content_moderation(state: CaptionGeneratorState):
        text = (state.get("input_text") or "").lower()

        banned = [
            "hate", "violence", "porn", "nudity",
            "racist", "sexist", "harassment"
        ]

        if any(word in text for word in banned):
            state["flagged"] = True
            state["selected_caption"] = "Content violates moderation policies."
        else:
            state["flagged"] = False

        return state


    # -----------------------------
    # PLATFORM RULES
    # -----------------------------
    def platform_rules(state: CaptionGeneratorState):
        platform = state.get("platform", "general").lower()

        limits = {
            "twitter": 280,
            "instagram": 2200,
            "linkedin": 3000,
            "facebook": 63206,
            "tiktok": 2200,
            "general": 280,
        }

        state["max_length"] = limits.get(platform, 280)

        hashtags = state.get("hashtags", [])

        if platform == "instagram":
            hashtags += ["#InstaGood", "#Photography"]
        elif platform == "twitter":
            hashtags += ["#Twitter"]
        elif platform == "linkedin":
            hashtags += ["#Professional", "#Career"]

        state["hashtags"] = hashtags
        return state


    # -----------------------------
    # CAPTION GENERATION
    # -----------------------------
    def generate_captions(state: CaptionGeneratorState):
        if state.get("flagged"):
            return state

        prompt = f"""
You MUST respond with VALID JSON ONLY.
NO markdown. NO text outside JSON.

Generate 3 social media captions.

JSON FORMAT:
{{
  "captions": ["...", "...", "..."],
  "hashtags": ["#tag1", "#tag2"]
}}

RULES:
- Platform: {state["platform"]}
- Tone: {state["tone"]}
- Topic: {state["topic"]}
- Max length: {state["max_length"]}
- Emojis allowed: {state["emojis"]}
- Call to action: {state["call_to_action"]}
- Image context: {state["image_description"] or "none"}
- Description: {state["input_text"]}
"""

        try:
            response = llm.invoke(prompt)
            content = response.content.strip()

            logger.info("RAW LLM RESPONSE:\n%s", content)

            try:
                parsed = json.loads(content)
            except Exception:
                match = re.search(r"\{[\s\S]*\}", content)
                if not match:
                    raise ValueError("No JSON returned")
                parsed = json.loads(match.group())

            captions = parsed.get("captions", [])
            if not captions:
                raise ValueError("Empty captions")

            state["caption_variants"] = captions
            state["selected_caption"] = captions[0]

            if parsed.get("hashtags"):
                state["hashtags"] = parsed["hashtags"]

        except Exception as e:
            logger.error("Caption generation failed: %s", e)
            state["caption_variants"] = []
            state["selected_caption"] = "Failed to generate captions."

        return state


    # -----------------------------
    # FORMAT OUTPUT
    # -----------------------------
    def format_output(state: CaptionGeneratorState):
        caption = state.get("selected_caption", "")
        hashtags = state.get("hashtags", [])

        if hashtags and not any(tag in caption for tag in hashtags):
            caption = caption + "\n\n" + " ".join(hashtags[:10])

        state["formatted_caption"] = caption
        state["character_count"] = len(caption)
        state["word_count"] = len(caption.split())
        state["within_limit"] = state["character_count"] <= state["max_length"]

        return state


    # -----------------------------
    # BUILD GRAPH
    # -----------------------------
    graph = StateGraph(CaptionGeneratorState)

    graph.add_node("moderation", content_moderation)
    graph.add_node("rules", platform_rules)
    graph.add_node("generate", generate_captions)
    graph.add_node("format", format_output)

    graph.set_entry_point("moderation")

    def route_after_moderation(state):
        return END if state.get("flagged") else "rules"

    graph.add_conditional_edges(
        "moderation",
        route_after_moderation,
        {"rules": "rules", END: END}
    )

    graph.add_edge("rules", "generate")
    graph.add_edge("generate", "format")
    graph.add_edge("format", END)

    return graph.compile()


# -----------------------------
# PUBLIC HELPER FUNCTION
# -----------------------------
def generate_social_caption(
    description: str,
    platform: str = "instagram",
    tone: str = "friendly",
    topic: str = "",
    emojis: bool = True,
    call_to_action: str = "",
    image_description: str = ""
) -> Dict[str, Any]:

    graph = compile_social_caption_generator()

    initial_state = CaptionGeneratorState({
        "input_text": description,
        "platform": platform,
        "tone": tone,
        "topic": topic,
        "emojis": emojis,
        "call_to_action": call_to_action,
        "image_description": image_description,
        "hashtags": [],
    })

    result = graph.invoke(initial_state)

    return {
        "captions": result.get("caption_variants", []),
        "selected_caption": result.get("selected_caption", ""),
        "formatted_caption": result.get("formatted_caption", ""),
        "hashtags": result.get("hashtags", []),
        "character_count": result.get("character_count", 0),
        "word_count": result.get("word_count", 0),
        "within_limit": result.get("within_limit", False),
        "max_length": result.get("max_length", 280),
        "platform": platform,
        "success": not result.get("flagged", False),
    }


# -----------------------------
# TEST
# -----------------------------
if __name__ == "__main__":
    output = generate_social_caption(
        description="A beautiful sunset at the beach with golden hour lighting",
        platform="instagram",
        tone="inspirational",
        topic="travel",
        call_to_action="Share your favorite sunset spot!",
        image_description="Person watching sunset at beach"
    )

    print(json.dumps(output, indent=2))
