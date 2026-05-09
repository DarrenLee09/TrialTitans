# Negotiator Module

The Negotiator takes a `Gap` dict (produced by the Organizer) and a `CaseProfile` dict and returns an `OutreachPlan` dict containing: the identified data holder, a real verifiable contact, and a fully drafted outreach artifact (letter, subpoena scaffold, or form instructions). No emails are sent — drafts only.

---

## Public interface

```python
from negotiator import plan_outreach

plan = plan_outreach(gap, case_profile)
```

`gap` and `case_profile` are plain dicts. Schema documentation and factory helpers are in [negotiator/schemas.py](negotiator/schemas.py).

### `Gap` fields

| Field | Type | Description |
|---|---|---|
| `bucket` | str | `"liability"` \| `"damages"` \| `"coverage"` \| `"credibility"` |
| `field` | str | Field name from doctrine template (e.g. `"at_fault_policy_limits"`) |
| `leverage_tier` | int | 1–4 (1 = highest impact on case value) |
| `closeable` | str | `"yes"` \| `"no"` \| `"conditional"` |
| `closing_action` | str | Free-text description of what outreach to draft |
| `status` | str | `"open"` \| `"in_progress"` \| `"closed"` \| `"unfillable"` |

### `CaseProfile` key fields

| Field | Type | Notes |
|---|---|---|
| `plaintiff_name` | str | |
| `plaintiff_employer` | str | Used for wage verification recipient |
| `plaintiff_carrier` | str \| None | Plaintiff's own auto insurance carrier (State Farm, etc.) — used for UIM demand |
| `defendant_name` | str | |
| `defendant_employer` | str \| None | Seeds commercial policy demand (5A) |
| `defendant_vehicle` | str \| None | |
| `incident_date` | str | Human-readable, e.g. `"October 14, 2025"` |
| `incident_location` | str | |
| `at_fault_carrier` | str \| None | Insurance carrier name |
| `at_fault_claim_number` | str \| None | |
| `at_fault_adjuster` | str \| None | |
| `treating_providers` | list[str] | Names of medical providers; first entry used for HIPAA request |
| `treatment_date_ranges` | list[dict] | Each: `{provider, start, end}` |
| `injuries` | list[str] | |
| `statutes_cited` | list[str] | |
| `jurisdiction` | str | `"CA"` |
| `county` | str \| None | |
| `file_number` | str \| None | |
| `attorney_name` / `attorney_firm` | str \| None | Appear in letter headers |
| `missed_work_start` / `missed_work_end` | str \| None | Used for wage verification |
| `mmi_date` | str \| None | Maximum medical improvement date; used in future-care opinion request |

### `OutreachPlan` fields

| Field | Type | Description |
|---|---|---|
| `gap_field` | str | Which gap this addresses |
| `data_holder` | str | Name of the record holder |
| `holder_type` | str | `insurance_carrier` \| `medical_provider` \| `employer` \| `wireless_carrier` \| `government_agency` \| `paywalled_database` \| `expert_witness` \| `unidentified` |
| `contact_method` | dict | `{address, url, phone}` — real verifiable contacts only |
| `outreach_type` | str | `hipaa_records_request` \| `policy_disclosure_demand` \| `subpoena_draft` \| `wage_verification` \| `foia` \| `none` \| `generic` |
| `drafted_artifact` | str | Full letter text; empty string if `paywalled=True` |
| `caveats` | list[str] | Attorney-facing notes to review before sending |
| `requires_human_followup` | bool | True for paywalled holders and web-search-identified holders |
| `paywalled` | bool | True when holder requires subscription access |

---

## Routing logic

```
plan_outreach(gap, case_profile)
        │
        ▼
registry lookup (data/holder_registry.yaml)
        │
        ├── found → engine=template → Jinja2 render
        │                └── HIPAA request, subpoena, DMV request, wage verification
        │
        ├── found → engine=llm → Claude drafting
        │                └── policy disclosure demands (commercial + personal)
        │
        ├── found → engine=none → return info-only plan (paywalled databases)
        │
        └── not found → Claude + web search tool use → generic outreach
                        (always sets requires_human_followup=True)
```

The `violation_evidence` field uses keyword routing. First-match wins:

1. `closing_action` contains `"phone"`, `"wireless"`, `"carrier"`, `"cellular"`, `"cell"`, or `"text message"` → `violation_evidence.phone_records` (subpoena draft)
2. `closing_action` contains `"camera"`, `"surveillance"`, `"footage"`, `"video"`, `"cctv"`, or `"traffic camera"` → `violation_evidence.camera_footage` (CPRA request)

Category-C (internal-task) gaps have registry entries with `engine: none` and `holder_type: unidentified`. They return `outreach_type: "none"`, `drafted_artifact: ""`, and `requires_human_followup: True`, with attorney-facing caveats. They do **not** fall to the web-search path.

Registry entries may include an explicit `requires_human_followup: true` key to override the computed default (used for `umbrella_policy_check` and `causation_chain`).

---

## Demo outputs (5A, 5B, 5C)

### 5A — Commercial policy disclosure demand to Pacific Coast Plumbing

```python
gap = {
    "bucket": "coverage",
    "field": "additional_defendants_check",
    "leverage_tier": 1,
    "closeable": "yes",
    "closing_action": "Letter to Pacific Coast Plumbing requesting commercial policy disclosure under VC §17150; respondeat superior claim",
    "status": "open",
}
plan = plan_outreach(gap, case_profile_santos)
# plan["holder_type"] == "employer"
# plan["outreach_type"] == "policy_disclosure_demand"
# plan["drafted_artifact"] contains: VC §17150, respondeat superior,
#   Perez v. Van Groningen & Sons (1986), Pacific Coast Plumbing
```

**Engine:** LLM (Claude). Requires `ANTHROPIC_API_KEY`.

**Authority:** Cal. Veh. Code § 17150; respondeat superior — *Perez v. Van Groningen & Sons* (1986) 41 Cal.3d 962.

---

### 5B — Phone records subpoena scaffold for Harmon's wireless carrier

```python
gap = {
    "bucket": "liability",
    "field": "violation_evidence",
    "leverage_tier": 1,
    "closeable": "yes",
    "closing_action": "Subpoena duces tecum to Harmon's wireless carrier for phone records covering 7:30–7:50 AM on 10/14/2025",
    "status": "open",
}
plan = plan_outreach(gap, case_profile_santos)
# plan["holder_type"] == "wireless_carrier"
# plan["outreach_type"] == "subpoena_draft"
# plan["drafted_artifact"] contains: CCP §1985, [CARRIER NAME], [CARRIER ADDRESS],
#   7:30 AM – 7:50 AM window, CVC §23123.5
# plan["caveats"][0] — pre-litigation caveat (lawsuit required)
# plan["caveats"][1] — AT&T / Verizon / T-Mobile compliance addresses
```

**Engine:** Jinja2 template. Runs fully offline.

**Carrier placeholder:** `[CARRIER NAME]` / `[CARRIER ADDRESS]` are literal placeholders. Known major carrier compliance addresses are in `caveats[1]`:
- **AT&T:** AT&T Wireless, National Compliance Center, 11760 US Highway 1, North Palm Beach, FL 33408
- **Verizon:** Verizon, Law Enforcement Resource Team, 180 Washington Valley Road, Bedminster, NJ 07921
- **T-Mobile:** T-Mobile Legal Department, 12920 SE 38th St, Bellevue, WA 98006

**Authority:** Cal. Code Civ. Proc. § 1985. Subpoena requires filed lawsuit; see caveat for pre-litigation preservation demand alternative.

---

### 5C — HIPAA records request to Coastal Rehab Physical Therapy

```python
gap = {
    "bucket": "damages",
    "field": "medical_expenses_past",
    "leverage_tier": 1,
    "closeable": "yes",
    "closing_action": "HIPAA-compliant records and billing request to Coastal Rehab Physical Therapy",
    "status": "open",
}
plan = plan_outreach(gap, case_profile_santos)
# plan["holder_type"] == "medical_provider"
# plan["outreach_type"] == "hipaa_records_request"
# plan["drafted_artifact"] contains: 45 C.F.R. §164.508, Coastal Rehab Physical Therapy,
#   10/25/2025 – 12/20/2025, Maria Santos
```

**Engine:** Jinja2 template. Runs fully offline.

**Authority:** 45 C.F.R. § 164.508 (HIPAA right to access and amend PHI).

---

## Holder registry

`data/holder_registry.yaml` covers these gap fields:

| Field | Holder type | Engine | Paywalled | Notes |
|---|---|---|---|---|
| `medical_expenses_past` | medical_provider | Template | No | |
| `lost_wages_past` | employer | Template | No | |
| `damages_comparables` | paywalled_database | None (info only) | Yes | |
| `at_fault_policy_limits` | insurance_carrier | LLM | No | |
| `additional_defendants_check` | employer | LLM | No | |
| `violation_evidence.phone_records` | wireless_carrier | Template | No | Keyword-routed |
| `prior_claims_history_checked` | paywalled_database | None (info only) | Yes | |
| `defendant_driving_history` | government_agency | Template | No | |
| `client_uim_coverage` | insurance_carrier | LLM | No | Plaintiff's own UIM carrier |
| `umbrella_policy_check` | insurance_carrier | None (info only) | No | Carrier unknown; folds into existing demands |
| `defendant_assets_check` | government_agency | Template | No | County recorder + CA SOS |
| `violation_evidence.camera_footage` | government_agency | Template | No | Keyword-routed (CPRA) |
| `causation_chain` | expert_witness | LLM | No | Attorney selects firm from caveat list |
| `medical_expenses_future` | medical_provider | Template | No | Future-care opinion letter to treating physician |
| `pre_existing_conditions_disclosed` | medical_provider | Template | No | 5-year pre-accident HIPAA request |
| `defense_anticipation` | unidentified | None (internal) | No | Category C — attorney task |
| `client_account_consistency` | unidentified | None (internal) | No | Category C — attorney task |
| `non_economic_damages_basis` | unidentified | None (internal) | No | Category C — paralegal/attorney task |
| `treatment_gaps_addressed` | unidentified | None (internal) | No | Category C — gather client docs |
| `client_social_media_review` | unidentified | None (internal) | No | Category C — paralegal task |

Gap fields not in this registry fall through to the Claude + web search path.

---

## Environment

`ANTHROPIC_API_KEY` is required for:
- LLM drafting (5A, personal policy demand)
- Web search long-tail holder identification

Without the key, both paths return an offline fallback stub with the correct dict shape so the app does not crash.

---

## Module layout

```
negotiator/
├── __init__.py              re-exports plan_outreach
├── schemas.py               dict field documentation + make_gap / make_case_profile helpers
├── registry.py              YAML loader + _SUBTYPE_ROUTES keyword routing
├── outreach.py              plan_outreach() entry point + routing logic
├── search.py                Claude tool-use loop + DuckDuckGo scraping
├── drafters/
│   ├── template_drafter.py  Jinja2 rendering + context builder
│   └── llm_drafter.py       Claude drafting + offline fallback
└── templates/
    ├── hipaa_records_request.j2
    ├── pre_existing_records_request.j2
    ├── future_care_opinion_request.j2
    ├── phone_records_subpoena.j2
    ├── dmv_record_request.j2
    ├── defendant_assets_public_records.j2
    ├── traffic_camera_foia.j2
    └── wage_verification.j2
```

---

## Tests

```
tests/
├── fixtures/
│   ├── case_profile_santos.json
│   ├── case_profile_smith.json      (generality test — different parties/jurisdiction)
│   ├── gaps_demo_section4.json      (all 20 demo-case gaps for smoke test)
│   ├── gap_5a_commercial_policy.json
│   ├── gap_5b_phone_records.json
│   ├── gap_5c_coastal_rehab.json
│   ├── gap_client_uim.json
│   ├── gap_umbrella_check.json
│   ├── gap_defendant_assets.json
│   ├── gap_causation_chain.json
│   ├── gap_medical_future.json
│   ├── gap_pre_existing.json
│   └── gap_camera_footage.json
└── test_negotiator.py       34 tests — all pass
```

Run with:

```bash
.venv/bin/python -m pytest tests/test_negotiator.py -v
```

Test coverage:
- Registry loading and subtype routing (phone + camera keywords)
- All three demo-case outputs (5A/5B/5C) — structure and artifact content
- Demo-case smoke test — all 20 Section 4 gaps route without crashing; no unexpected `unidentified` results
- Per-gap content tests for all 7 new Category B gaps
- Category C (internal-task) tests — assert `outreach_type: none`, empty artifact, attorney caveat present
- Generality test — Smith case profile produces no Santos-specific strings in any artifact
- Paywalled gap returns info-only plan with no artifact
- Unregistered gap returns `holder_type: "unidentified"` with `requires_human_followup: True`
- 5A offline fallback (no API key) still returns correct dict shape
- 5A LLM prompt contains required case facts before being sent to Claude
