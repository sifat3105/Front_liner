from openai import OpenAI
import json
import os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def generate_caption(
    context: str,
    post_type: str,
    max_length: int = 180
):
    """
    Generate a social media caption using only context and post type.
    """

    system_prompt = """
    You are a professional social media copywriter.
    You write short, engaging, high-conversion captions.
    Respond ONLY in valid JSON.
    """

    user_prompt = f"""
    Context:
    {context}

    Post Type:
    {post_type}

    Rules:
    - Generate only ONE caption
    - No hashtags
    - No emojis unless natural
    - Max length: {max_length} characters
    - Clear, engaging, human tone

    Return JSON:
    {{
      "caption": "string"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )

    output = response.choices[0].message.content

    try:
        return json.loads(output)["caption"]
    except Exception:
        return output
    
def generate_hashtags(
    caption: str,
    max_hashtags: int = 5
):
    """
    Generate ONLY hashtags using context and post type.
    """

    system_prompt = """
    You are a social media growth expert.
    Generate relevant, high-reach, and safe hashtags.
    Respond ONLY in valid JSON.
    """

    user_prompt = f"""
    Context:
    {caption}



    Rules:
    - Generate only hashtags
    - Use #
    - No spaces inside hashtags
    - No emojis
    - Max hashtags: {max_hashtags}
    - Mix broad + niche tags

    Return JSON:
    {{
      "hashtags": ["#example", "#example2"]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
    )

    output = response.choices[0].message.content

    try:
        return json.loads(output)["hashtags"]
    except Exception:
        return []
