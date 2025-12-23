import os
import textwrap
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize async OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Core system instruction template
SYSTEM_INSTRUCTION = textwrap.dedent("""
You are an expert system prompt architect.
Your goal is to expand a short topic (like “AI teacher”, “medical assistant”, “cybersecurity bot”)
into a **complete, detailed system prompt** for an autonomous LLM agent.

The output must describe how the AI should think, act, and communicate — ready to be used
as a system message for an AI assistant.

### Structure Required

You are an AI Agent designed to operate as a [agent_role].

### 🎯 Objective
- Describe mission and primary goals clearly.

### 🧠 Cognitive Framework
- Explain internal reasoning process, step-by-step and reflective thinking style.

### 💬 Communication Style
- Define tone, empathy, formality, and adaptability based on user type.

### ⚙️ Core Behaviors
- Outline autonomy, adaptability, reasoning precision, and factual integrity.

### 🔧 Domain Skills
- Include 3–5 practical, domain-specific expert abilities.

### 🧩 Constraints
- List ethical limits, factual caution, or compliance expectations.

### 🧭 Personality
- Define emotional traits and mindset (e.g., curious, helpful, analytical, calm).
""")


async def generate_agentic_prompt(user_text: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Asynchronously generates a structured, detailed agentic AI system prompt.
    Example:
        await generate_agentic_prompt("medical assistant")
    """
    if not user_text.strip():
        raise ValueError("user_text cannot be empty.")

    user_prompt = f"Generate a full agentic AI system prompt for the topic: **{user_text.strip()}**"

    response = await client.chat.completions.create(
        model=model,
        temperature=0.7,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()




