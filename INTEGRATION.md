# Integration Spec — Organizer → Negotiator

This document is the building guide for wiring the Negotiator into the application.
It covers data contracts, what needs to be built, the integration entry point,
persistence options, and Streamlit wiring. It is intended to be handed to a developer
and followed top-to-bottom.

---

## 1. System map

```
 ┌──────────────────────────────────────────────────────────┐
 │  Raw intake text (paralegal paste)                       │
 └──────────────────────┬───────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Organizer — parse_intake()               [NOT BUILT]    │
 │  Input:  raw text                                        │
 │  Output: CaseProfile dict                                │
 └──────────────────────┬───────────────────────────────────┘
                        │  CaseProfile
                        ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Harvester + Retrieval (Statute layer)    [BUILT ✓]      │
 │  Input:  CaseProfile.statutes_cited                      │
 │  Output: list of statute dicts (section, body, factors)  │
 └──────────────────────┬───────────────────────────────────┘
                        │  statutes
                        ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Organizer — detect_gaps()                [NOT BUILT]    │
 │  Input:  CaseProfile + statutes                          │
 │  Output: list[Gap dict]  (ranked, bucketed)              │
 └──────────────────────┬───────────────────────────────────┘
                        │  Gap list
                        ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Negotiator — plan_outreach()             [BUILT ✓]      │
 │  Input:  Gap dict + CaseProfile dict                     │
 │  Output: OutreachPlan dict                               │
 └──────────────────────┬───────────────────────────────────┘
                        │  OutreachPlan list
                        ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Persistence layer                        [NOT BUILT]    │
 │  Session state (demo) / SQLite (prod)                    │
 └──────────────────────┬───────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Streamlit — Case Workspace page          [NOT BUILT]    │
 │  Intake → Gap report → Outreach drafts → Export          │
 └──────────────────────────────────────────────────────────┘
```

**Built today:** Harvester, Retrieval, AI memo, existing Streamlit statute search,
Negotiator (20-gap registry, 4 template engines, 2 LLM paths, 34 tests).

**Not built:** `parse_intake`, `detect_gaps`, persistence layer, Case Workspace page.

---

## 2. Data contracts

These are the three dicts that flow through the pipeline. All are plain Python dicts
with no ORM or schema enforcement — fields are documented here and in
`negotiator/schemas.py`.

### 2.1 CaseProfile

Produced by `parse_intake`. Consumed by `detect_gaps` and `plan_outreach`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `plaintiff_name` | str | Yes | |
| `plaintiff_employer` | str | Yes | Used for wage verification |
| `plaintiff_carrier` | str \| None | No | Plaintiff's own auto carrier (State Farm, etc.) — UIM demand |
| `defendant_name` | str | Yes | |
| `defendant_employer` | str \| None | No | Seeds commercial policy demand |
| `defendant_vehicle` | str \| None | No | |
| `incident_date` | str | Yes | Human-readable: `"October 14, 2025"` |
| `incident_location` | str | Yes | |
| `at_fault_carrier` | str \| None | No | |
| `at_fault_claim_number` | str \| None | No | |
| `at_fault_adjuster` | str \| None | No | |
| `treating_providers` | list[str] | Yes | First entry used for HIPAA/future-care letters |
| `treatment_date_ranges` | list[dict] | Yes | Each: `{provider, start, end}` |
| `injuries` | list[str] | Yes | |
| `statutes_cited` | list[str] | Yes | Seeds Harvester lookup |
| `jurisdiction` | str | Yes | `"CA"` |
| `county` | str \| None | No | Used in DMV + recorder templates |
| `file_number` | str \| None | No | Appears in all letter headers |
| `attorney_name` | str \| None | No | |
| `attorney_firm` | str \| None | No | |
| `missed_work_start` | str \| None | No | |
| `missed_work_end` | str \| None | No | |
| `mmi_date` | str \| None | No | Used in future-care opinion letter |

**Minimal example that makes the Negotiator work offline (no LLM):**

```python
{
    "plaintiff_name": "Maria Santos",
    "plaintiff_employer": "Qualcomm",
    "defendant_name": "Robert Harmon",
    "incident_date": "October 14, 2025",
    "incident_location": "Mission Blvd & Garnet Ave, San Diego, CA",
    "treating_providers": ["Coastal Rehab Physical Therapy"],
    "treatment_date_ranges": [
        {"provider": "Coastal Rehab Physical Therapy", "start": "10/25/2025", "end": "12/20/2025"}
    ],
    "injuries": ["concussion", "cervical strain", "right knee contusion"],
    "statutes_cited": ["CVC 22350", "CVC 21453(a)", "CVC 23123.5"],
    "jurisdiction": "CA",
    "county": "San Diego",
    "file_number": "2026-0341",
    "attorney_name": "J. Liu",
    "attorney_firm": "[LAW FIRM NAME]",
    "mmi_date": "March 15, 2026",
}
```

The full Santos fixture is at `tests/fixtures/case_profile_santos.json`.

---

### 2.2 Gap

Produced by `detect_gaps`. Consumed by `plan_outreach`.

| Field | Type | Values |
|---|---|---|
| `bucket` | str | `"liability"` \| `"damages"` \| `"coverage"` \| `"credibility"` |
| `field` | str | Doctrine field name — see §3.2 for the full list |
| `leverage_tier` | int | 1–4 (1 = highest impact) |
| `closeable` | str | `"yes"` \| `"no"` \| `"conditional"` |
| `closing_action` | str | Free text — **the Negotiator's keyword router reads this** |
| `status` | str | `"open"` \| `"in_progress"` \| `"closed"` \| `"unfillable"` |

**Critical:** `closing_action` drives subtype routing for `violation_evidence`.
If it contains phone/wireless keywords → phone records subpoena.
If it contains camera/footage/surveillance keywords → CPRA camera request.
The Organizer must write descriptive `closing_action` strings, not terse codes.

**Example Gap list (coverage bucket):**

```python
[
    {
        "bucket": "coverage",
        "field": "at_fault_policy_limits",
        "leverage_tier": 1,
        "closeable": "yes",
        "closing_action": "Policy disclosure demand to GEICO adjuster Nakamura",
        "status": "open",
    },
    {
        "bucket": "coverage",
        "field": "additional_defendants_check",
        "leverage_tier": 1,
        "closeable": "yes",
        "closing_action": "Letter to Pacific Coast Plumbing requesting commercial policy disclosure under VC §17150",
        "status": "open",
    },
]
```

The full 20-gap demo list is at `tests/fixtures/gaps_demo_section4.json`.

---

### 2.3 OutreachPlan

Returned by `plan_outreach`. This is what gets persisted and displayed.

| Field | Type | Notes |
|---|---|---|
| `gap_field` | str | Which gap this addresses |
| `data_holder` | str | Name of the record holder |
| `holder_type` | str | See enum below |
| `contact_method` | dict | `{address, url, phone}` — real verifiable contacts |
| `outreach_type` | str | See enum below |
| `drafted_artifact` | str | Full letter text; `""` for info-only or internal gaps |
| `caveats` | list[str] | Attorney-facing notes to review before sending |
| `requires_human_followup` | bool | True for paywalled, expert_witness, or internal gaps |
| `paywalled` | bool | True when holder requires subscription access |

**`holder_type` values:**
`insurance_carrier` | `medical_provider` | `employer` | `wireless_carrier` |
`government_agency` | `paywalled_database` | `expert_witness` | `unidentified`

**`outreach_type` values:**
`hipaa_records_request` | `policy_disclosure_demand` | `subpoena_draft` |
`wage_verification` | `foia` | `generic` | `none`

**What `drafted_artifact` contains by gap type:**

| Gap | artifact |
|---|---|
| `medical_expenses_past` | Full HIPAA records request letter |
| `pre_existing_conditions_disclosed` | Pre-accident HIPAA letter, 5-year lookback |
| `medical_expenses_future` | Future-care opinion request to treating physician |
| `lost_wages_past` | Wage verification letter to plaintiff's employer |
| `defendant_driving_history` | DMV record request letter |
| `defendant_assets_check` | County recorder public records request letter |
| `violation_evidence` (phone) | Subpoena duces tecum scaffold |
| `violation_evidence` (camera) | CPRA traffic camera footage request |
| `at_fault_policy_limits` | LLM-drafted personal policy disclosure demand |
| `additional_defendants_check` | LLM-drafted commercial policy demand |
| `client_uim_coverage` | LLM-drafted UIM coverage inquiry |
| `causation_chain` | LLM-drafted expert engagement + conflict-check letter |
| `damages_comparables` | `""` (paywalled — caveats list Westlaw + JuryVerdicts.net) |
| `prior_claims_history_checked` | `""` (paywalled — caveats list ISO ClaimSearch) |
| `umbrella_policy_check` | `""` (caveat says to include in existing demands) |
| `defense_anticipation` | `""` (internal — caveat is attorney analysis instruction) |
| `client_account_consistency` | `""` (internal — cross-check instruction) |
| `non_economic_damages_basis` | `""` (internal — interview instruction) |
| `treatment_gaps_addressed` | `""` (internal — prior-auth document instruction) |
| `client_social_media_review` | `""` (internal — paralegal review instruction) |

---

## 3. What needs to be built

### 3.1 `organizer/intake.py` — parse_intake

**Input:** raw intake text (string pasted by paralegal)
**Output:** CaseProfile dict

```python
def parse_intake(raw_text: str, jurisdiction: str = "CA") -> dict:
    ...
```

**Implementation options (in order of fidelity):**

| Option | How | Trade-offs |
|---|---|---|
| **LLM extraction** | Claude with structured JSON output mode, prompted with the CaseProfile field list | Best accuracy; requires API key; ~2s latency |
| **Regex + heuristics** | Extract date patterns, name patterns, insurance claim numbers | Faster; brittle on messy intake |
| **Hardcoded fixture** | Load `tests/fixtures/case_profile_santos.json` | Demo only; works offline immediately |

For the demo, start with the hardcoded fixture path. The LLM extraction can be layered on
after the UI is wired up.

**LLM prompt skeleton (when building the real version):**

```python
INTAKE_PARSE_SYSTEM = """\
Extract structured fields from a personal injury intake note.
Return a JSON object matching the CaseProfile schema exactly.
If a field is not present in the notes, return null.
Do not invent information not present in the source text.
"""

INTAKE_PARSE_USER = """\
CASERPROFILE FIELDS: {field_list}

INTAKE TEXT:
{raw_text}

Return valid JSON only. No preamble.
"""
```

---

### 3.2 `organizer/gaps.py` — detect_gaps

**Input:** CaseProfile dict + list of statute dicts from the Harvester
**Output:** list[Gap dict], sorted by `leverage_tier`

```python
def detect_gaps(case_profile: dict, statutes: list[dict]) -> list[dict]:
    ...
```

The Organizer runs a **doctrine template** — a fixed checklist of fields across
the four buckets. For each field, it checks whether the CaseProfile has the
information. If not, it emits a Gap.

**The 20 doctrine fields (with expected `closing_action` language):**

| Bucket | Field | `closing_action` pattern |
|---|---|---|
| coverage | `at_fault_policy_limits` | `"Policy disclosure demand to [CARRIER] adjuster [ADJUSTER]"` |
| coverage | `additional_defendants_check` | `"Letter to [EMPLOYER] requesting commercial policy disclosure under VC §17150"` |
| coverage | `client_uim_coverage` | `"Request UIM coverage information from [PLAINTIFF CARRIER]"` |
| coverage | `umbrella_policy_check` | `"Include umbrella policy inquiry in policy disclosure demands"` |
| coverage | `defendant_assets_check` | `"Run county recorder and CA SOS search for [DEFENDANT]"` |
| liability | `violation_evidence` (phone) | `"Subpoena to wireless carrier for phone records covering [TIME WINDOW]"` |
| liability | `violation_evidence` (camera) | `"Canvas businesses for camera footage at [LOCATION]"` |
| liability | `causation_chain` | `"Engage accident reconstruction expert"` |
| liability | `defense_anticipation` | `"Attorney analysis — evaluate [DEFENSE THEORY]"` |
| damages | `medical_expenses_past` | `"HIPAA records and billing request to [PROVIDER]"` |
| damages | `lost_wages_past` | `"Wage verification letter to [EMPLOYER] HR"` |
| damages | `medical_expenses_future` | `"Future-care opinion request to treating physician [PHYSICIAN]"` |
| damages | `non_economic_damages_basis` | `"Structured client interview and family testimonials"` |
| damages | `damages_comparables` | `"Jury verdict reporter query — [COUNTY], similar injuries"` |
| credibility | `pre_existing_conditions_disclosed` | `"5-year pre-accident medical records request to [PROVIDER]"` |
| credibility | `prior_claims_history_checked` | `"ISO ClaimSearch query"` |
| credibility | `treatment_gaps_addressed` | `"Document insurance prior-auth email chain for [N]-day gap"` |
| credibility | `client_social_media_review` | `"Public [PLATFORM] review by paralegal"` |
| credibility | `defendant_driving_history` | `"DMV record request for [DEFENDANT]"` |
| credibility | `client_account_consistency` | `"Cross-check intake vs. ER notes vs. police report"` |

**Gap detection logic (pseudocode):**

```python
def detect_gaps(case_profile, statutes):
    gaps = []

    # Coverage — always check, tier 1–2
    if not case_profile.get("at_fault_policy_limits_received"):
        gaps.append(Gap("coverage", "at_fault_policy_limits", tier=1, ...))
    if case_profile.get("defendant_employer"):
        gaps.append(Gap("coverage", "additional_defendants_check", tier=1, ...))
    if case_profile.get("plaintiff_carrier"):
        gaps.append(Gap("coverage", "client_uim_coverage", tier=1, ...))

    # Liability — check statutes for evidence gaps
    for statute in statutes:
        if statute["section"] == "23123.5" and not evidence_exists_for(case_profile, "phone_use"):
            # phone use alleged but not evidenced → two gap types
            gaps.append(Gap("liability", "violation_evidence", tier=1,
                            closing_action="Subpoena to wireless carrier for phone records..."))
            gaps.append(Gap("liability", "violation_evidence", tier=2,
                            closing_action="Canvas businesses for camera footage at intersection..."))
    ...

    return sorted(gaps, key=lambda g: g["leverage_tier"])
```

The full gap detection logic requires knowing which CaseProfile fields indicate
"this gap is already closed" (e.g., `at_fault_policy_limits_received: True` means
the coverage gap is closed). Add these boolean flags to CaseProfile as you build.

---

## 4. Integration entry point

Once `parse_intake` and `detect_gaps` exist, the integration function is:

```python
# organizer/run.py

from negotiator import plan_outreach

def run_case(raw_intake: str, jurisdiction: str = "CA") -> dict:
    """
    Full pipeline: raw text → case profile → gaps → outreach plans.
    Returns a dict ready for persistence and UI rendering.
    """
    from organizer.intake import parse_intake
    from organizer.gaps import detect_gaps
    from retrieval import query_router

    case_profile = parse_intake(raw_intake, jurisdiction)

    # Pull statutes for each cited section
    statutes = []
    for citation in case_profile.get("statutes_cited", []):
        result = query_router.route(citation, jurisdiction=jurisdiction, limit=1)
        statutes.extend(result.get("results", []))

    gaps = detect_gaps(case_profile, statutes)

    plans = []
    for gap in gaps:
        try:
            plan = plan_outreach(gap, case_profile)
        except Exception as exc:
            # Never let one gap crash the whole batch
            plan = _error_plan(gap, exc)
        plans.append(plan)

    return {
        "case_profile": case_profile,
        "statutes": statutes,
        "gaps": gaps,
        "outreach_plans": plans,
    }


def _error_plan(gap: dict, exc: Exception) -> dict:
    return {
        "gap_field": gap.get("field", "unknown"),
        "data_holder": "[ERROR]",
        "holder_type": "unidentified",
        "contact_method": {"address": None, "url": None, "phone": None},
        "outreach_type": "none",
        "drafted_artifact": "",
        "caveats": [f"Plan generation failed: {exc}"],
        "requires_human_followup": True,
        "paywalled": False,
    }
```

The return dict from `run_case` is the single object that gets persisted and
passed to the UI. Everything downstream reads from this shape.

---

## 5. Persistence

### Option A — Streamlit session state (use this first)

No new code needed. Store the `run_case` return dict in `st.session_state`:

```python
st.session_state["case_run"] = run_case(raw_text)
```

**Scope:** lives for one browser session. Lost on page refresh.
**Good for:** demo, judging day, rapid iteration.

### Option B — JSON file per case

```python
import json, hashlib, pathlib

RUNS_DIR = pathlib.Path("output/case_runs")
RUNS_DIR.mkdir(parents=True, exist_ok=True)

def save_run(run: dict) -> pathlib.Path:
    key = run["case_profile"].get("file_number") or hashlib.md5(
        run["case_profile"].get("plaintiff_name", "").encode()
    ).hexdigest()[:8]
    path = RUNS_DIR / f"{key}.json"
    path.write_text(json.dumps(run, indent=2))
    return path

def load_run(file_number: str) -> dict | None:
    path = RUNS_DIR / f"{file_number}.json"
    return json.loads(path.read_text()) if path.exists() else None
```

**Scope:** survives restarts; one file per case.
**Good for:** local dev, single-user demo with history.

### Option C — SQLite (production path)

Add two tables to `db/legal_harvester.db`:

```sql
CREATE TABLE IF NOT EXISTS case_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_number TEXT,
    plaintiff   TEXT,
    run_json    TEXT NOT NULL,          -- full run_case() return dict, JSON-serialized
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS outreach_plans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_run_id     INTEGER REFERENCES case_runs(id),
    gap_field       TEXT NOT NULL,
    holder_type     TEXT,
    outreach_type   TEXT,
    drafted_artifact TEXT,
    requires_human_followup INTEGER,
    paywalled       INTEGER,
    plan_json       TEXT NOT NULL      -- full OutreachPlan dict, JSON-serialized
);
```

Store the full JSON blobs for flexibility. The structured columns exist for
filtering/querying without deserializing everything.

**Recommendation:** start with Option A for the demo. Add Option B if you need
run history across sessions. Option C only if multiple users or a real case management
workflow is required.

---

## 6. Streamlit wiring

The existing app is a statute search tool (`frontend/streamlit_app.py`).
The Case Workspace is a new page alongside it.

### 6.1 File layout

```
frontend/
├── streamlit_app.py          existing statute search (unchanged)
├── styles.py
├── components/
│   ├── ...existing...
│   ├── intake_form.py        NEW — text area + parse button
│   ├── gap_panel.py          NEW — four-bucket gap report table
│   └── outreach_panel.py     NEW — per-gap OutreachPlan cards with artifact expand
└── pages/
    └── case_workspace.py     NEW — Streamlit multi-page entry point
```

Streamlit multi-page is automatic: any `.py` in `frontend/pages/` becomes a
sidebar nav item. No routing config needed.

### 6.2 Session state keys

All pages share `st.session_state`. Use these keys consistently:

| Key | Type | Set by | Read by |
|---|---|---|---|
| `case_run` | dict | `intake_form` on parse | `gap_panel`, `outreach_panel` |
| `case_profile` | dict | shortcut: `case_run["case_profile"]` | all components |
| `gaps` | list[dict] | shortcut: `case_run["gaps"]` | `gap_panel` |
| `outreach_plans` | list[dict] | shortcut: `case_run["outreach_plans"]` | `outreach_panel` |
| `selected_gap_field` | str \| None | `gap_panel` on row click | `outreach_panel` |
| `case_pinned` | list[dict] | existing statute search | `case_file_sidebar` |

### 6.3 Component specs

**`intake_form.render() -> str | None`**

```
┌─────────────────────────────────────────────────────┐
│  Paste intake notes                                  │
│  ┌───────────────────────────────────────────────┐  │
│  │ INTAKE NOTES — Santos, Maria — File #2026-0341│  │
│  │ ...                                           │  │
│  └───────────────────────────────────────────────┘  │
│  [ Parse intake ]   [ Load Santos demo case ]        │
└─────────────────────────────────────────────────────┘
```

- "Load Santos demo case" button loads `tests/fixtures/case_profile_santos.json`
  directly and skips `parse_intake` — makes the demo work without an API key.
- Returns the raw text string (or `None` if nothing entered).
- Calls `run_case(raw_text)` and stores result in `st.session_state["case_run"]`.

**`gap_panel.render(gaps: list[dict], plans: list[dict]) -> str | None`**

Renders the four-bucket gap table from demo-case.md Section 4.
Returns the `gap_field` of the row the user clicked "Draft outreach" on.

```
  BUCKET 3 — COVERAGE                          Tier  Closeable
  ──────────────────────────────────────────────────────────
  at_fault_policy_limits     Policy demand →    1     ✅       [Draft]
  additional_defendants_check Commercial →      1     ✅       [Draft]
  client_uim_coverage        UIM demand →       1     ✅       [Draft]
  umbrella_policy_check      See caveats        2     ✅       [Info]
  defendant_assets_check     Recorder + SOS     2     ✅       [Draft]
```

Color coding:
- Tier 1 = red pill
- Tier 2 = amber pill
- Tier 3/4 = grey pill
- `closeable: no` = strike-through, no Draft button
- `holder_type: unidentified` (Category C) = grey "Internal" badge instead of Draft button

**`outreach_panel.render(plan: dict) -> None`**

Renders a single OutreachPlan. Called when user clicks a Draft button.

```
  ┌─────────────────────────────────────────────────────┐
  │  📋  at_fault_policy_limits                         │
  │  Holder: GEICO · insurance_carrier · policy demand  │
  │  Contact: Attn: K. Nakamura, GEICO Claims Dept      │
  │                                                     │
  │  ▼ Drafted letter                                   │
  │  ┌─────────────────────────────────────────────┐   │
  │  │ Via Certified Mail, Return Receipt Requested│   │
  │  │ ...                                         │   │
  │  └─────────────────────────────────────────────┘   │
  │                                                     │
  │  ⚠ Caveats (1)                                     │
  │  UIM claim triggers only if defendant limits...     │
  │                                                     │
  │  [ Copy to clipboard ]  [ Download .txt ]           │
  └─────────────────────────────────────────────────────┘
```

For info-only gaps (`drafted_artifact == ""`):
- Show caveats prominently instead of a letter box.
- Label it "Attorney action required" rather than "Drafted letter".

**`case_workspace.py` page layout:**

```python
# frontend/pages/case_workspace.py

import streamlit as st
from frontend.components import intake_form, gap_panel, outreach_panel

st.set_page_config(page_title="Case Workspace", layout="wide")

st.markdown("## Case Workspace")

raw_text = intake_form.render()

if "case_run" not in st.session_state:
    st.stop()

run = st.session_state["case_run"]
col_gaps, col_outreach = st.columns([2, 3], gap="large")

with col_gaps:
    selected = gap_panel.render(run["gaps"], run["outreach_plans"])
    if selected:
        st.session_state["selected_gap_field"] = selected

with col_outreach:
    field = st.session_state.get("selected_gap_field")
    if field:
        plan = next((p for p in run["outreach_plans"] if p["gap_field"] == field), None)
        if plan:
            outreach_panel.render(plan)
```

---

## 7. Build order

Follow this sequence. Each step is independently shippable.

### Step 1 — Wire the demo case end-to-end (1–2 hours, no new AI needed)

1. Create `frontend/pages/case_workspace.py` with the layout above.
2. Create `frontend/components/intake_form.py` with the "Load Santos demo case"
   button that reads `tests/fixtures/case_profile_santos.json` and
   `tests/fixtures/gaps_demo_section4.json` directly into session state — no
   `parse_intake` or `detect_gaps` needed yet.
3. Create `frontend/components/gap_panel.py` that renders the four-bucket table
   from the gaps list in session state.
4. Create `frontend/components/outreach_panel.py` that renders the OutreachPlan
   returned by `plan_outreach(selected_gap, case_profile)`.
5. Wire `plan_outreach` calls into the "Draft" button handler.
6. Run the app: `streamlit run frontend/streamlit_app.py`.

At the end of Step 1, the demo case from `demo-case.md` runs live in the browser.
This is the judging-day demo path.

### Step 2 — Add the LLM intake parser (2–3 hours, requires API key)

1. Create `organizer/intake.py` with `parse_intake(raw_text) -> CaseProfile`.
2. Use Claude with `response_format={"type": "json_object"}` and the CaseProfile
   field list as the extraction schema.
3. Replace the hardcoded fixture load in `intake_form` with a call to `parse_intake`.
4. Test against the Santos raw intake text in `demo-case.md` Section 1.
5. Assert the output matches `tests/fixtures/case_profile_santos.json` on the
   required fields.

### Step 3 — Add gap detection (2–4 hours)

1. Create `organizer/gaps.py` with `detect_gaps(case_profile, statutes) -> list[Gap]`.
2. Start with a rule-based implementation: for each of the 20 doctrine fields in §3.2,
   check whether the corresponding CaseProfile field is populated/None and emit a Gap.
3. Wire `detect_gaps` output into session state and confirm the gap panel renders
   the same 20 gaps as the hardcoded fixture.
4. Remove the hardcoded gaps fixture from `intake_form`; the full pipeline now runs.

### Step 4 — Persistence (1 hour)

1. Add `organizer/run.py` with the `run_case` and `save_run`/`load_run` functions
   from §4 and §5.
2. Add a "Case history" sidebar section in `case_workspace.py` that lists saved runs
   and lets the user reload one.
3. Use Option B (JSON files) unless SQLite is already warranted.

### Step 5 — Export and polish

1. Add a "Download outreach packet" button that zips all drafted artifacts into a
   `.zip` file: one `.txt` per gap, named `{gap_field}_{holder_type}.txt`.
2. Add status tracking: a "Mark as sent" button per OutreachPlan that flips a
   `status` field in session state / the JSON file.
3. Update the existing `case_file_sidebar` export to include outreach plans alongside
   the pinned statutes.

---

## 8. Environment and dependencies

All dependencies are already in `requirements.txt`. No additions needed.

The Negotiator works fully offline for all template-engine gaps (no API key).
LLM-engine gaps (`at_fault_policy_limits`, `additional_defendants_check`,
`client_uim_coverage`, `causation_chain`) fall back to a stub letter if
`ANTHROPIC_API_KEY` is not set — the app never crashes.

```
ANTHROPIC_API_KEY=sk-ant-...   # required for LLM drafting and intake parsing
```

---

## 9. Quick reference — Negotiator call

```python
from negotiator import plan_outreach

# gap comes from detect_gaps() or the demo fixture
# case_profile comes from parse_intake() or the Santos fixture
plan = plan_outreach(gap, case_profile)

# what you get back
print(plan["holder_type"])        # "insurance_carrier"
print(plan["outreach_type"])      # "policy_disclosure_demand"
print(plan["drafted_artifact"])   # full letter text (or "" for internal/paywalled)
print(plan["caveats"])            # list of attorney notes
print(plan["requires_human_followup"])  # bool
```

The registry currently covers all 20 gaps from `demo-case.md` Section 4.
Unregistered gap fields fall back to a Claude + web search path and return
`holder_type: "unidentified"` with `requires_human_followup: True`.
