"""Prompt templates for Claude-powered statute reasoning."""

ATTORNEY_ANSWER_SYSTEM = """\
You are a legal research assistant supporting plaintiff-side personal-injury attorneys.
You read excerpts from official statutes and produce concise, citation-grounded analysis.

Hard rules:
- Quote or paraphrase only from the supplied statutes; do not invent sections.
- Always cite as "<Jurisdiction> <Code> § <Section>" inline.
- If the supplied statutes do not answer the question, say so plainly.
- Do not give legal advice; produce a research memo, not a recommendation to a client.
"""

ATTORNEY_ANSWER_USER_TEMPLATE = """\
# Question
{question}

# Jurisdiction filter
{jurisdiction}

# Retrieved statutes
{statutes_block}

Write a brief memo (under 250 words) covering:
1. Which statutes are on point and why.
2. What each one requires or prohibits.
3. Any obvious gaps or ambiguities the attorney should investigate.
"""


def render_statutes_block(statutes: list[dict]) -> str:
    chunks = []
    for s in statutes:
        cite = f"{s.get('jurisdiction', '?')} {s.get('code_name', '?')} § {s.get('section', '?')}"
        title = s.get("title") or ""
        body = (s.get("body") or s.get("snippet") or "").strip()
        chunks.append(f"## {cite} — {title}\n{body}")
    return "\n\n".join(chunks) if chunks else "(none)"
