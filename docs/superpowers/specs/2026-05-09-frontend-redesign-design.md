# TrialTitans Frontend Redesign — Design

**Date:** 2026-05-09
**Status:** Draft for review
**Context:** Hackathon project. Optimizing for "looks like a real product in a 5-minute demo," not production rigor.

## Goal

Take the current Streamlit UI from "generic Streamlit demo" to "looks like a focused legal research product." Stay on Streamlit (no framework swap). Optimize for the judge's first impression and a clean golden-path demo: search → pin → export AI memo.

## Non-goals

- No backend changes (retrieval, AI, DB stay as-is).
- No framework migration (no React, no FastAPI).
- No multi-user, auth, persistence beyond session state.
- No edge-case error states beyond a graceful "no results" view.
- No reorder, per-statute notes, or other case-file power features.

## The demo narrative (golden path)

The judge sees:

1. **Landing.** Wordmark, tagline, hero search, three example query chips, an explainer card describing the three retrieval modes.
2. **Click chip "rear-ended at a stop sign".** Query populates, results animate in. Citation chip on each card, highlighted match terms in body, factor tags below.
3. **Pin two results.** Pin icon flips state; left "Case File" sidebar updates with a counter badge and the pinned citations.
4. **Toggle AI on, click "Generate memo".** Right rail streams a structured attorney memo. Citations in the memo are clickable pills that scroll-jump to the source card.
5. **Click "Export"** in the case file → markdown memo download.

Everything else is supporting set dressing.

## Visual language

- **Palette.**
  - Surface: `#0E1116` (near-black) for the app background.
  - Card: `#F6F1E7` (warm ivory) for primary surfaces.
  - Ink: `#161A22` body text on ivory; `#E8E4D9` body on dark.
  - Accent: `#7A1F2B` (oxblood) for primary actions, citation chips, link hover.
  - Muted: `#6B7280` for metadata.
- **Type.**
  - Headings: Source Serif 4 (Google Fonts).
  - Body / UI: Inter.
  - Citations / mono: JetBrains Mono.
- **Spacing & shape.**
  - 8px base grid. Card radius 12px. Chip radius 999px (pill). Generous padding (24px in cards).
  - Subtle 1px hairline borders in `rgba(0,0,0,0.08)`; no heavy shadows.
- **Motion.**
  - 150–200ms ease-out on hover/focus/state changes only. No flashy entrances.

## Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  TRIALTITANS  ·  Statute search for accident litigation     [AI ▢]       │
├──────────────┬──────────────────────────────────────┬─────────────────────┤
│              │                                      │                     │
│  Case File   │  ┌────────────────────────────────┐  │  AI Memo            │
│  (3)         │  │ Hero search input              │  │  (sticky)           │
│              │  │ [chip] [chip] [chip]           │  │                     │
│  § 22107     │  └────────────────────────────────┘  │  Streamed text…     │
│  Turning…    │                                      │  with [§ 22107]     │
│              │  Route: fts · 8 results              │  citation pills     │
│  § 22350     │  ┌────────────────────────────────┐  │                     │
│  Basic spd…  │  │ § 22107  ·  Turning Movements  │  │                     │
│              │  │ [body excerpt with highlights] │  │                     │
│  [Export]    │  │ [factor] [factor]   📌  ↗      │  │                     │
│              │  └────────────────────────────────┘  │                     │
│              │  ┌────────────────────────────────┐  │                     │
│              │  │ … next card …                  │  │                     │
└──────────────┴──────────────────────────────────────┴─────────────────────┘
```

- **Top bar:** wordmark, tagline, AI toggle (right). Sticky.
- **Left sidebar (Case File):** always visible, ~280px. Title with count badge, list of pinned statutes (citation in mono + truncated title), Export-as-markdown button at bottom. Empty state: a one-liner caption "Pin statutes to build a case file."
- **Main column:** hero search (only at top of column, not full width — keeps focus), example chips below input, route/result-count caption, list of result cards.
- **Right rail (AI memo):** ~360px, only when AI toggle is on AND there are results. Sticky to viewport. Otherwise collapsed.

The three-column layout is desktop-only. Streamlit's `st.columns` with widths roughly `[1.2, 3, 2]` for sidebar / main / right rail, plus a single CSS injection to make the left column behave as a sticky sidebar.

## Components

### `top_bar`
- Wordmark + tagline (left), AI toggle (right).
- AI toggle is a styled `st.toggle` with custom CSS to look like a segmented control.

### `hero_search`
- Large `st.text_input` with custom CSS (font-size 18px, height ~56px, ivory bg, focus ring in oxblood).
- Below the input: three example chips rendered via `st.button` styled as pills. Clicking a chip writes the query into session state and reruns. Chips:
  - `CA Veh Code 22107`
  - `rear-ended at a stop sign`
  - `failure to yield at intersection`
- Jurisdiction selector moves out of the search bar into a small dropdown to the right of the input (less visual noise).

### `result_card`
Replaces `frontend/components/result_card.py`. Renders:
- Header row: citation chip (mono, oxblood text on ivory) + factor tags inline at right.
- Title (serif, 20px).
- Body excerpt: 2–3 lines, with FTS5 `<mark>` highlights preserved (already supported via `unsafe_allow_html=True`).
- Footer row: Pin icon-button (toggles state, shows filled state when pinned), source-link icon, optional "Open" expander to show full statute body.
- Card has a stable `id` attribute (`statute-{id}`) so AI memo citation pills can scroll-jump to it.

### `case_file_sidebar`
Replaces `frontend/components/case_workspace.py`. Renders in `st.sidebar`:
- Title "Case File" with a count badge.
- For each pinned statute: citation (mono) + truncated title + small unpin (×) button.
- Sticky bottom: "Export memo" button → triggers `st.download_button` for a markdown file containing the pinned statutes (citation, title, body, source URL) plus the most recent AI memo if one was generated.
- Empty state caption.

### `ai_memo_rail`
Renders in the right column. Replaces the inline AI block in `streamlit_app.py`:
- Title "AI Memo" with a small "Generate" button (only visible when AI toggle is on and results exist; auto-runs on first results).
- Streams the memo using `answer_generator.answer` (today it's a single call; if streaming is non-trivial we render with `st.write_stream` over a generator wrapping the existing call, or fall back to a spinner + final block — see Open Questions).
- Citations like `§ 22107` in the memo are post-processed into HTML anchor pills that scroll the matching result card into view (`<a href="#statute-{id}">`).

### `empty_state`
Shown in the main column when `query` is empty. Three short cards explaining the retrieval modes (Citation / Factor / Natural language) with one example each. Clicking an example fills the search box.

### `loading_state`
Replaces the default spinner. Render 3 skeleton cards (gray bars) while results are being computed. Implemented with a small CSS keyframe shimmer.

## Data flow

Unchanged from today. The redesign is presentational only:

```
User types/clicks chip
  → query in session_state
  → query_router.route(query, jurisdiction)
  → optional reranker.rerank
  → render result_cards
  → user pins → session_state.case_pinned
  → user toggles AI / clicks Generate
  → answer_generator.answer(query, results)
  → render ai_memo_rail
  → user clicks Export → download_button serves markdown
```

No new modules under `retrieval/` or `ai/`. The frontend layer reads the same dicts it does today.

## Theming approach

Two layers:

1. **`.streamlit/config.toml`** — sets base palette, fonts, and primary color. Handles what Streamlit's theme system covers (background, text, primary, font).
2. **`frontend/styles.py`** — exports a single `inject()` function that calls `st.markdown(<style>…</style>, unsafe_allow_html=True)` once at app start. This handles everything the theme can't: card styling, chip pills, citation chip, sidebar look, sticky behavior, skeleton shimmer, hero input override, scroll-anchor offset for citation jumps. Called once from `streamlit_app.py`.

Fonts loaded via `<link>` tags injected in the same style block.

## File structure

```
frontend/
  streamlit_app.py            # rewritten as a thin layout shell
  styles.py                   # NEW — single-shot CSS injector + font loading
  components/
    top_bar.py                # NEW
    hero_search.py            # NEW (replaces search_bar.py)
    result_card.py            # rewritten
    case_file_sidebar.py      # NEW (replaces case_workspace.py)
    ai_memo_rail.py           # NEW
    empty_state.py            # NEW
    loading_state.py          # NEW
  search_bar.py               # DELETE
  case_workspace.py           # DELETE
.streamlit/
  config.toml                 # NEW — theme primitives
```

`streamlit_app.py` becomes a thin orchestrator: inject styles, render top bar, set up three columns, dispatch to the right component per state (empty / loading / results).

## State

Session state keys:
- `query: str` — current search input (so chips can write to it).
- `jurisdiction: str | None`.
- `use_ai: bool`.
- `case_pinned: list[dict]` — already exists.
- `last_memo: str | None` — most recent generated memo, used by Export.
- `last_results: list[dict]` — most recent result set, used by Export.

## Error & edge cases (minimum viable for demo)

- **No results:** main column shows a simple "No statutes matched. Try a different phrasing or one of the examples below." with the three example chips again.
- **AI toggle on but no `ANTHROPIC_API_KEY`:** the AI memo rail shows a small inline note "Set `ANTHROPIC_API_KEY` to enable the AI memo." Don't crash.
- **Export with empty case file:** Export button is disabled.
- **Long statute body:** card shows truncated body with an expander; full body in expander.

That's the floor. Other failures fall back to current Streamlit defaults — judges aren't trying to break it.

## Out of scope (named explicitly)

- Reorder / per-statute notes / tags in the case file.
- Multi-jurisdiction comparison view.
- Saved searches / history.
- Mobile / responsive (desktop demo only).
- Auth, persistence beyond session, multi-user.
- Backend / retrieval / AI changes.
- Tests beyond a smoke import-and-render check.

## Open questions for implementation

1. **Streaming memo.** Does `ai/answer_generator.py` currently stream, or return a single string? If single, we either (a) wrap it in `st.write_stream` with a fake chunker for visual effect, or (b) keep the spinner-then-block UX. Decide during implementation based on what `answer` returns.
2. **Citation pills in memo.** Post-process the memo string with a regex over `§ \d+` and replace with anchor HTML. Confirm the model emits citations in this exact form; if not, prompt-tweak the system prompt to enforce it.

These don't block writing the plan — they're small implementation choices that surface when the code is in front of us.

## Acceptance criteria

A reviewer can verify the redesign by running `streamlit run frontend/streamlit_app.py` and confirming, in order:

1. Landing shows wordmark, tagline, hero search, three example chips, and the three-mode explainer cards.
2. Clicking a chip populates the search and renders results without a manual rerun.
3. Each result card shows a citation chip, serif title, body with highlighted matches (when FTS), factor tags, pin icon, source-link icon.
4. Clicking pin updates the left "Case File" sidebar and its count badge.
5. With AI toggle on, the right rail renders an AI memo. Citation pills in the memo, when clicked, scroll the matching result card into view.
6. "Export memo" downloads a markdown file containing pinned statutes plus the most recent AI memo.
7. Empty state and skeleton loading state both appear at the right times.
8. The visual style (palette, fonts, spacing, card shape) matches this spec — no default Streamlit chrome leaking through in the main flow.
