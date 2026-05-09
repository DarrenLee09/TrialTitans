# Doctrine Template — Pre-Demand-Ready California Motor Vehicle PI Case

**Target state:** A case file complete enough to send a maximally-leveraged pre-litigation settlement demand letter under California law, premised on negligence per se (Cal. Evid. Code §669 / CACI 418).

**Use:** The Organizer compares this template against the current case profile to compute the four-bucket gap report. Each field has a leverage tier and a closeability flag, which the Organizer uses to rank gaps and which the Negotiator uses to decide whether to draft outreach.

---

## Schema conventions

Each field carries:

- **`required`** — must be filled for pre-demand readiness
- **`leverage_tier`** — 1 (highest impact on case value) → 4 (lowest)
- **`closeable`** — `yes` / `no` / `conditional`. Tells the Negotiator whether to draft outreach when the field is missing
- **`closing_action`** — what the Negotiator should do if missing and closeable
- **`per_se_element`** — for liability fields, which CACI 418 element the field satisfies (1–4)

---

## Top-level deadlines (case-killing if missed)

| Field | Authority | Notes |
|---|---|---|
| `statute_of_limitations_date` | CCP §335.1 | 2 years from date of injury for CA personal injury. Hard deadline. |
| `government_tort_claim_filed` | Gov. Code §911.2 | If any defendant is a public entity: 6-month notice deadline. |

---

## BUCKET 1 — LIABILITY

The negligence per se case-in-chief. Each cited statute must satisfy all four CACI 418 elements.

### `cited_statutes` *(list — one entry per statute being invoked)*
- **required:** yes (at least one)
- **leverage_tier:** 1
- **fields per statute:**
  - `citation` (e.g., "CVC 22350")
  - `full_text` (from Harvester)
  - `source_url` (from Harvester)
  - `protected_class` (from Harvester schema)
  - `harm_type_prevented` (from Harvester schema)

### `violation_evidence` *(per statute)*
- **required:** yes
- **leverage_tier:** 1
- **per_se_element:** 1 (defendant violated the statute)
- **satisfied_by:** police citation, dashcam/surveillance video, defendant admission, eyewitness statement, accident reconstruction
- **closeable:** conditional
- **closing_action:** request police report (if not pulled), subpoena nearby business camera footage, FOIA traffic camera footage

### `causation_chain`
- **required:** yes
- **leverage_tier:** 1
- **per_se_element:** 2 (violation proximately caused harm)
- **satisfied_by:** factual narrative linking violation → collision → injury, supported by physical evidence and medical records
- **closeable:** conditional
- **closing_action:** accident reconstruction expert report; treating physician causation letter

### `harm_type_match`
- **required:** yes
- **leverage_tier:** 2
- **per_se_element:** 3 (harm is the type the statute prevents)
- **satisfied_by:** plaintiff's injuries match the harm category in `harm_type_prevented` (e.g., bodily injury from collision matches CVC speeding statutes)
- **closeable:** no — this is a doctrinal match, not a data gap. If unsatisfied, this statute can't be used for negligence per se; flag for theory revision.

### `protected_class_match`
- **required:** yes
- **leverage_tier:** 2
- **per_se_element:** 4 (plaintiff in class statute protects)
- **satisfied_by:** plaintiff's role at time of crash (other driver / passenger / pedestrian / cyclist) matches `protected_class` field on statute
- **closeable:** no — same as above

### `comparative_fault_assessment`
- **required:** yes
- **leverage_tier:** 1
- **satisfied_by:** documented assessment of plaintiff's % fault, supported by police report and physical evidence
- **closeable:** conditional
- **closing_action:** if police report indicates plaintiff fault, gather rebuttal evidence (witness statements, reconstruction)
- **note:** California is pure comparative fault — every percentage point off the plaintiff reduces recovery proportionally

### `defense_anticipation`
- **required:** no (recommended)
- **leverage_tier:** 3
- **satisfied_by:** documented analysis of likely insurer defenses (CACI 420/421 excused-violation arguments, sudden emergency, plaintiff comparative fault)
- **closeable:** no — internal analysis

---

## BUCKET 2 — DAMAGES

Economic and non-economic damages, anchored by Maximum Medical Improvement.

### `mmi_reached`
- **required:** yes
- **leverage_tier:** 1
- **satisfied_by:** treating physician statement that plaintiff has reached maximum medical improvement (or treatment plateau)
- **closeable:** no — this is a medical milestone, not a data gap. If not reached, demand letter is premature.

### `medical_expenses_past` *(itemized)*
- **required:** yes
- **leverage_tier:** 1
- **satisfied_by:** itemized medical bills with provider, date, service, charge, paid amount
- **closeable:** yes
- **closing_action:** HIPAA-compliant records request to each treating provider

### `medical_expenses_future`
- **required:** yes
- **leverage_tier:** 2
- **satisfied_by:** life care plan, treating physician opinion, or specialist projection of ongoing care costs
- **closeable:** yes
- **closing_action:** request future care opinion from treating physician; engage life care planner if catastrophic

### `lost_wages_past`
- **required:** yes (if applicable)
- **leverage_tier:** 2
- **satisfied_by:** employer wage verification letter, pay stubs covering missed work period, tax returns
- **closeable:** yes
- **closing_action:** request wage verification from employer; obtain plaintiff tax returns

### `lost_earning_capacity_future`
- **required:** conditional (when injuries affect work capacity)
- **leverage_tier:** 2
- **satisfied_by:** vocational expert report, occupational medicine evaluation
- **closeable:** yes
- **closing_action:** engage vocational expert if injuries are work-impairing

### `property_damage`
- **required:** yes
- **leverage_tier:** 4
- **satisfied_by:** repair estimate or total loss valuation, photos
- **closeable:** yes
- **closing_action:** obtain repair shop estimate or insurance valuation

### `non_economic_damages_basis`
- **required:** yes
- **leverage_tier:** 2
- **satisfied_by:** documented impact on daily life (pain, sleep disruption, loss of enjoyment, relationship effects); CA recognizes these as "life damages"
- **closeable:** conditional
- **closing_action:** structured client interview; family/friend testimonials

### `damages_comparables`
- **required:** no (recommended)
- **leverage_tier:** 2
- **satisfied_by:** jury verdict reports for similar injury type in same county (CA results vary heavily by venue)
- **closeable:** yes
- **closing_action:** query jury verdict reporter (Westlaw Verdict Reporter, JuryVerdicts.net)

---

## BUCKET 3 — COVERAGE

What's actually collectible. Often the practical ceiling on case value.

### `at_fault_carrier_identified`
- **required:** yes
- **leverage_tier:** 1
- **satisfied_by:** carrier name, claim number, adjuster contact
- **closeable:** yes
- **closing_action:** policy disclosure demand to defendant

### `at_fault_policy_limits`
- **required:** yes
- **leverage_tier:** 1 *(case-defining)*
- **satisfied_by:** declaration page or written confirmation from carrier of bodily injury policy limit
- **closeable:** yes
- **closing_action:** Insurance Code §791.13-style policy limits demand letter to carrier
- **note:** A demand at or below policy limits creates an "open policy" risk for the carrier if they fail to tender — a major negotiation lever

### `client_medpay_coverage`
- **required:** yes
- **leverage_tier:** 3
- **satisfied_by:** plaintiff's auto policy declarations
- **closeable:** yes
- **closing_action:** request from plaintiff's own carrier

### `client_uim_coverage`
- **required:** yes
- **leverage_tier:** 1 *(if at-fault is underinsured)*
- **satisfied_by:** plaintiff's auto policy declarations showing UIM limits
- **closeable:** yes
- **closing_action:** request from plaintiff's own carrier

### `additional_defendants_check`
- **required:** yes
- **leverage_tier:** 1 *(can multiply case ceiling)*
- **satisfied_by:** documented investigation of:
  - Employer (if at-fault driver was on the clock — respondeat superior)
  - Vehicle owner (if different from driver — permissive use)
  - Vehicle manufacturer (if defect contributed — product liability)
  - Bar/restaurant (if defendant was overserved — dram shop, Bus. & Prof. Code §25602.1)
  - Government entity (if dangerous condition of public property — Gov. Code §835)
- **closeable:** yes
- **closing_action:** for each candidate, identify holder and request relevant records

### `defendant_assets_check`
- **required:** conditional (if uninsured or underinsured)
- **leverage_tier:** 2
- **satisfied_by:** property records, business registrations, public asset search
- **closeable:** yes
- **closing_action:** county recorder property search; SOS business filings

### `umbrella_policy_check`
- **required:** yes
- **leverage_tier:** 2
- **satisfied_by:** documented inquiry into excess/umbrella coverage on either side
- **closeable:** yes
- **closing_action:** include in policy disclosure demand

---

## BUCKET 4 — CREDIBILITY

Factors that strengthen or weaken the case narrative. Insurers discount cases with credibility flags.

### `treatment_gaps_addressed`
- **required:** yes
- **leverage_tier:** 2
- **satisfied_by:** continuous treatment record from accident → MMI, OR documented explanation for any gap >2 weeks
- **closeable:** conditional
- **closing_action:** if gap exists, gather explanation (insurance issues, work conflicts, follow-up scheduling)

### `client_account_consistency`
- **required:** yes
- **leverage_tier:** 2
- **satisfied_by:** client's account aligns with police report, medical intake notes, and physical evidence
- **closeable:** no — internal review

### `prior_claims_history_checked`
- **required:** yes
- **leverage_tier:** 3
- **satisfied_by:** ISO ClaimSearch or equivalent prior-claims report on plaintiff
- **closeable:** yes (paywalled — Negotiator outreach territory)
- **closing_action:** ISO ClaimSearch query

### `pre_existing_conditions_disclosed`
- **required:** yes
- **leverage_tier:** 2
- **satisfied_by:** plaintiff medical history reviewed; pre-existing conditions identified and addressed in causation analysis
- **closeable:** yes
- **closing_action:** request plaintiff medical records for 5 years pre-accident

### `defendant_driving_history`
- **required:** no (recommended)
- **leverage_tier:** 3
- **satisfied_by:** defendant's CA DMV record (where accessible) or court records of prior traffic citations/civil suits
- **closeable:** conditional
- **closing_action:** court records search; DMV record request (limited access)

### `client_social_media_review`
- **required:** yes
- **leverage_tier:** 3
- **satisfied_by:** documented review of client's public social media for posts that contradict injury claims
- **closeable:** yes
- **closing_action:** public profile review

---

## Gap report structure (output of Organizer)

For each missing required field, the Organizer produces:

```
{
  bucket: "liability" | "damages" | "coverage" | "credibility",
  field: "<field_name>",
  leverage_tier: 1-4,
  closeable: "yes" | "no" | "conditional",
  closing_action: "<text from template>",
  status: "open" | "in_progress" | "closed" | "unfillable"
}
```

Sorting: by `leverage_tier` ascending, then `closeable=yes` first within each tier.

This is the input the Negotiator uses to decide which gaps to draft outreach for.
