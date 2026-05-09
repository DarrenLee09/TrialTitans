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

Write a brief memo (under 250 words) with two parts:

**Summary** — open with a 2–4 sentence synthesis that names every statute by
its section number (cite each as "<Jurisdiction> <Code> § <Section>") and
explains how they relate to one another and to the question: which is the
general rule, which carve out exceptions, which impose duties vs. penalties,
how they stack or overlap, and where one provision triggers or limits another.
This summary must mention each section number explicitly.

**Statutes** — then a short bulleted list, one bullet per statute, in this
exact form:
- <Jurisdiction> <Code> § <Section> — one-line note on what it does and how
  it fits the picture above.

Close with one sentence on any gap or ambiguity worth investigating.
"""


def render_statutes_block(statutes: list[dict]) -> str:
    chunks = []
    for s in statutes:
        cite = f"{s.get('jurisdiction', '?')} {s.get('code_name', '?')} § {s.get('section', '?')}"
        title = s.get("title") or ""
        body = (s.get("body") or s.get("full_text") or s.get("snippet") or "").strip()
        chunks.append(f"## {cite} — {title}\n{body}")
    return "\n\n".join(chunks) if chunks else "(none)"
