"""Long-tail holder identification using Claude + web search tool use."""
from __future__ import annotations

import os
import re

import requests
from bs4 import BeautifulSoup

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore

MODEL = "claude-sonnet-4-6"

_SEARCH_TOOL = {
    "name": "search_web",
    "description": (
        "Search the web for information about who holds a specific type of record "
        "and how to contact them for a personal injury case."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to run.",
            }
        },
        "required": ["query"],
    },
}

_SYSTEM = """\
You are a California plaintiff-side personal injury paralegal identifying who holds a
specific type of record and how to contact them.

Hard rules:
- Only identify real, verifiable data holders. Do not invent contacts or URLs.
- If you find a real contact (address or URL), include it explicitly in your response.
- If you cannot find a verifiable holder, say so plainly and set requires_human_followup.
- Respond with a brief description of the holder, their contact information, and the
  recommended outreach approach. Plain text, no markdown.
"""


def search_web(query: str) -> list[dict]:
    """Scrape DuckDuckGo HTML results. Returns list of {title, url, snippet}."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TrialTitans/1.0; legal-research)"}
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    results = []
    for r in soup.select(".result")[:5]:
        title_el = r.select_one(".result__title")
        url_el = r.select_one(".result__url")
        snippet_el = r.select_one(".result__snippet")
        results.append({
            "title": title_el.get_text(strip=True) if title_el else "",
            "url": url_el.get_text(strip=True) if url_el else "",
            "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
        })
    return [r for r in results if r["title"] or r["url"]]


def _validate_url(url: str) -> bool:
    """HEAD-check a URL; returns True if it responds with a non-error status."""
    if not url.startswith(("http://", "https://")):
        return False
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        return resp.status_code < 400
    except requests.RequestException:
        return False


def search_holder(gap: dict, case_profile: dict) -> dict:
    """
    Use Claude + web search tool use to identify a data holder for a gap not
    found in the registry. Always sets requires_human_followup=True.
    """
    if Anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return _offline_fallback(gap)

    client = Anthropic()
    field = gap.get("field", "")
    closing_action = gap.get("closing_action", "")
    jurisdiction = case_profile.get("jurisdiction", "CA")

    user_message = (
        f"I need to identify who holds the following type of record and how to contact "
        f"them for a personal injury case in {jurisdiction}.\n\n"
        f"Gap field: {field}\n"
        f"What is needed: {closing_action}\n\n"
        f"Search for the specific data holder (agency, company, or repository) and their "
        f"official contact information or process for obtaining these records. Provide a "
        f"verifiable URL or mailing address. Do not invent contacts."
    )

    messages: list[dict] = [{"role": "user", "content": user_message}]
    response = None

    for _ in range(3):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=_SYSTEM,
            tools=[_SEARCH_TOOL],
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            break

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tu in tool_uses:
            if tu.name == "search_web":
                results = search_web(tu.input["query"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": str(results),
                })
        messages.append({"role": "user", "content": tool_results})

    final_text = ""
    if response:
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text

    # Extract and validate any URLs Claude found
    urls = re.findall(r"https?://[^\s'\"<>]+", final_text)
    validated_url = next((u for u in urls if _validate_url(u)), None)

    return {
        "gap_field": field,
        "data_holder": "[Identified via web search — verify before use]",
        "holder_type": "unidentified",
        "contact_method": {
            "address": None,
            "url": validated_url,
            "phone": None,
        },
        "outreach_type": "generic",
        "drafted_artifact": final_text,
        "caveats": [
            "This holder was identified via automated web search. Verify all contact "
            "information before sending any correspondence.",
            "Review the drafted artifact for accuracy before use.",
        ],
        "requires_human_followup": True,
        "paywalled": False,
    }


def _offline_fallback(gap: dict) -> dict:
    return {
        "gap_field": gap.get("field", ""),
        "data_holder": "Unidentified — set ANTHROPIC_API_KEY to enable holder lookup",
        "holder_type": "unidentified",
        "contact_method": {"address": None, "url": None, "phone": None},
        "outreach_type": "generic",
        "drafted_artifact": "",
        "caveats": ["Web search unavailable: ANTHROPIC_API_KEY not set."],
        "requires_human_followup": True,
        "paywalled": False,
    }
