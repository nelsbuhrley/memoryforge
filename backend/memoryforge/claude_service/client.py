"""Claude agent-sdk wrapper for MemoryForge.

Handles all communication with Claude through the agent SDK.
All prompts come from prompts.py — this module only handles
sending/receiving and parsing responses.
"""

import json
from typing import Any


async def query_claude(prompt: str) -> str:
    """Send a prompt to Claude and return the text response.

    Uses claude-agent-sdk's query() function.
    Falls back gracefully if the SDK is not available.
    """
    try:
        from claude_agent_sdk import query as agent_query
    except ImportError:
        raise RuntimeError(
            "claude-agent-sdk is not installed. "
            "Install with: pip install claude-agent-sdk"
        )

    response_parts = []
    async for message in agent_query(prompt=prompt):
        if hasattr(message, "content"):
            response_parts.append(str(message.content))
        else:
            response_parts.append(str(message))

    return "".join(response_parts)


async def query_claude_json(prompt: str) -> dict[str, Any]:
    """Send a prompt and parse the JSON response."""
    raw = await query_claude(prompt)

    # Extract JSON from response — Claude may wrap it in markdown code blocks
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json and ```)
        text = "\n".join(lines[1:-1])

    return json.loads(text)
