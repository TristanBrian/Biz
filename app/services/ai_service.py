# ============================================================
# app/services/ai_service.py
# AI advisory service powered by Anthropic's Claude API.
# Provides simple, actionable business advice to SMEs.
#
# MVP scope: one endpoint, one prompt, clean structured response.
# ============================================================

import httpx

from app.core.config import settings

# The Claude model to use — Sonnet is fast and cost-effective for this use case
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Base URL for the Anthropic messages API
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

# System prompt — tells Claude its role and output format
SYSTEM_PROMPT = """
You are BizSafi AI, a friendly and practical business advisor for small businesses (SMEs) 
in Kenya and East Africa. Your users are everyday entrepreneurs — salon owners, 
cafe operators, market traders, and similar.

Your job is to give clear, simple, actionable advice. Follow these rules:
- Use plain English. Avoid jargon.
- Keep responses short (3–5 bullet points or 2–3 short paragraphs max).
- Always ground advice in the Kenyan/East African business context.
- If the user asks about money, use KES (Kenyan Shillings).
- Never make up legal or financial facts. Say "check with a professional" when appropriate.
- Always be encouraging and respectful.
"""


async def query_ai(user_prompt: str, business_context: str = "") -> dict:
    """
    Send a business question to Claude and return structured advice.

    Args:
        user_prompt:      The SME's question (e.g. "How do I track daily profits?")
        business_context: Optional context about the business (category, location)
                          prepended to the prompt to personalise the response.

    Returns:
        dict with keys:
            - advice (str): The AI's response text
            - prompt_used (str): The final prompt sent (useful for debugging)

    Raises:
        RuntimeError if the API call fails.
    """
    # Build the full prompt — inject business context if available
    full_prompt = user_prompt
    if business_context:
        full_prompt = f"[Business context: {business_context}]\n\n{user_prompt}"

    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    body = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": full_prompt}
        ],
    }

    # Use httpx async client for non-blocking I/O
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(ANTHROPIC_API_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise RuntimeError(
            f"Claude API error {response.status_code}: {response.text}"
        )

    data = response.json()

    # Extract the text content from Claude's response
    advice_text = data["content"][0]["text"]

    return {
        "advice": advice_text,
        "prompt_used": full_prompt,
        "model": CLAUDE_MODEL,
    }
