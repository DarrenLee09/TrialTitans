# Demo Case — *Santos v. Harmon* (and Pacific Coast Plumbing)

A constructed California motor vehicle PI case designed to exercise every part of the system. All facts are fictional but plausible. CVC section numbers are real.

---

## Design rationale

Each element of this case is chosen to make a specific feature visible in the demo:

| Demo target | Why this case has it |
|---|---|
| Harvester multi-statute pull | Three CVC sections at play |
| Per se element checker | Two statutes satisfy all 4 elements; one is "theory pending evidence" |
| Four-bucket gap report | Real gaps in all four buckets |
| Leverage ranking | Tier-1 coverage gap (policy limits) front and center |
| Negotiator outreach drafting | At least one closeable gap per type |
| "Additional defendants" insight | Defendant was driving an employer's vehicle — multiplies case ceiling |
| Closeable vs. unfillable distinction | One pure doctrinal "drop this theory" moment |
| Credibility nuance | Explainable treatment gap + paywalled prior-claims check |

---

## Case summary (the "elevator pitch" for judges)

> *Maria Santos was T-boned at a San Diego intersection on October 14, 2025 by Robert Harmon, who ran a red light while speeding and allegedly texting. He was driving a work van for Pacific Coast Plumbing. Maria sustained a concussion, cervical strain, and a knee injury. She has reached MMI. Her firm is preparing a pre-litigation demand. The system identifies that the **most valuable open question is not Harmon's personal policy limits — it's Pacific Coast Plumbing's commercial policy**, which could multiply the case ceiling.*

---

## Section 1 — Raw intake (what gets pasted into the system)

This is the unstructured text the Intake step parses into structured CaseFacts.

```
INTAKE NOTES — Santos, Maria — File #2026-0341
Intake by: J. Liu, paralegal
Date: April 22, 2026

Client: Maria Santos, age 34, software engineer at Qualcomm
Phone: [redacted] | Email: [redacted]
Address: 4420 Mission Bay Dr, San Diego, CA 92109

ACCIDENT SUMMARY
Date/time: October 14, 2025, approximately 7:45 AM
Location: Intersection of Mission Blvd and Garnet Ave, San Diego, CA
Weather: Clear, dry pavement
Client direction: Northbound on Mission Blvd, right lane, with green signal
Defendant: Robert Harmon, age 45
Defendant direction: Westbound on Garnet Ave
Defendant vehicle: 2023 Ford Transit work van, marked "Pacific Coast
  Plumbing, Inc." Lic. plate noted in police report.

POLICE REPORT (San Diego PD Report #SD-2025-78451)
Responding officer: Officer M. Reyes, badge 4421
Citations issued to Harmon:
  - VC 22350 (Basic Speed Law) — radar 47 mph in posted 35 mph zone
  - VC 21453(a) (Failure to stop at red signal)
Officer's narrative notes a bystander stated Harmon "appeared to be looking
  at his phone" immediately before the collision. Bystander declined to
  provide formal statement at scene; name and contact not recorded.
No citation issued to Santos. Officer noted Santos had right-of-way.

INJURIES
- Concussion (loss of consciousness ~30 sec per ER notes)
- Cervical strain / whiplash, ROM limited
- Right knee contusion with bone bruise (MRI confirmed, no ligament tear)

TREATMENT
- Sharp Memorial Hospital ER, 10/14/2025 — admitted, released same day
  ER bill received: $12,400 (in file)
- Coastal Rehab Physical Therapy, 10/25/2025 through 12/20/2025
  Bills NOT yet requested
- Treating physician: Dr. A. Patel, Scripps Mercy
  MMI declared: March 15, 2026

WORK IMPACT
- Missed work 10/14/2025 through 11/4/2025 (3 weeks fully out)
- Part-time return 11/5/2025 through 11/19/2025 (~50% schedule)
- Full-time return 11/20/2025
- Annual salary: $148,000 (per client; not yet verified)

INSURANCE (per police report)
- Harmon insured by GEICO; claim # GEC-2025-9924411
- Adjuster: K. Nakamura
- Policy limits: NOT YET DISCLOSED
- Pacific Coast Plumbing commercial policy: NOT YET INVESTIGATED
- Santos's own auto policy: State Farm; UM/UIM limits not yet checked

NOTES FROM CLIENT INTERVIEW
- Client mentions prior lower back strain (2022, work-related, resolved
  with 6 weeks PT, not currently symptomatic)
- 11-day gap between ER discharge (10/15) and PT start (10/25) — client
  explains: insurance prior auth delay, has email confirmation
- Client active on Instagram (public); paralegal has not yet reviewed

OPEN ITEMS
- No accident reconstruction engaged
- No witness contact info
- No subpoena yet for any phone records
- ISO ClaimSearch not yet run on Santos
- No DMV pull on Harmon
```

---

## Section 2 — Expected Harvester output

When the Organizer queries the Harvester with the structured facts, it should pull:

| Citation | Title | Why pulled | All 4 per se elements? |
|---|---|---|---|
| **CVC 22350** | Basic Speed Law | Cited in police report; defendant clocked at 47 in 35 zone | ✅ Yes |
| **CVC 21453(a)** | Failure to stop at red signal | Cited in police report | ✅ Yes |
| **CVC 23123.5** | Prohibition on writing/sending/reading text-based communication while driving | Bystander statement re: phone use; not yet evidenced | ⚠️ Partial — protected class & harm type match; **violation evidence missing** |

Each statute returned with: full text, source URL, protected class (`other drivers / passengers`), harm type prevented (`bodily injury from collision`), contributing factor tags.

---

## Section 3 — Expected case profile (after Organizer structures intake + Harvester output)

Compressed view of the structured CaseFacts the Organizer holds:

```yaml
parties:
  plaintiff:
    name: Maria Santos
    age: 34
    role_at_crash: driver_with_right_of_way
  defendant_primary:
    name: Robert Harmon
    age: 45
    employer: Pacific Coast Plumbing, Inc.
    vehicle: 2023 Ford Transit (employer-owned, marked)
  defendant_secondary_candidate:
    name: Pacific Coast Plumbing, Inc.
    theory: respondeat superior (Harmon on the clock) + permissive use (VC 17150)

incident:
  date: 2025-10-14
  location: Mission Blvd & Garnet Ave, San Diego
  mechanism: T-bone, defendant ran red light at speed

statutes_cited:
  - VC 22350 [verified by police citation]
  - VC 21453(a) [verified by police citation]
  - VC 23123.5 [theory only, evidence pending]

injuries:
  - concussion
  - cervical strain
  - right knee contusion (bone bruise)
mmi_date: 2026-03-15

deadlines:
  statute_of_limitations: 2027-10-14  (CCP §335.1, 2 years)
  government_tort_claim: not_applicable
```

---

## Section 4 — Expected gap report (Organizer output, four buckets, ranked)

This is the centerpiece screen of the demo.

### 🔴 BUCKET 3 — COVERAGE *(highest leverage tier)*

| Gap | Tier | Closeable | Closing action |
|---|---|---|---|
| **`at_fault_policy_limits` (Harmon/GEICO)** | 1 | ✅ Yes | Policy disclosure demand to GEICO adjuster Nakamura |
| **`additional_defendants_check` — Pacific Coast Plumbing commercial policy** | 1 | ✅ Yes | Letter to Pacific Coast Plumbing requesting commercial policy disclosure under VC §17150; respondeat superior claim |
| **`client_uim_coverage` (Santos/State Farm)** | 1 *(if Harmon underinsured)* | ✅ Yes | Request from Santos's own carrier |
| `umbrella_policy_check` | 2 | ✅ Yes | Include in policy disclosure demands |
| `defendant_assets_check` (Harmon personal) | 2 | ✅ Yes | Defer pending policy limit disclosure |

### 🟡 BUCKET 1 — LIABILITY

| Gap | Tier | Closeable | Closing action |
|---|---|---|---|
| `violation_evidence` for **VC 23123.5** (texting) | 1 | ✅ Yes | Subpoena duces tecum to Harmon's wireless carrier for phone records covering 7:30–7:50 AM on 10/14/2025 |
| `violation_evidence` corroboration — eyewitness | 2 | ⚠️ Conditional | Canvas businesses near intersection for camera footage; locate bystander (officer narrative only) |
| `causation_chain` — accident reconstruction | 3 | ✅ Yes | Engage reconstruction expert (vendor list) |
| `defense_anticipation` — sudden emergency rebuttal? | 3 | ❌ Internal | Attorney analysis |

> **Theory note:** VC 23123.5 currently fails the "violation occurred" element. Flagged as **theory pending evidence** — if phone records come back negative, this statute will be **dropped from the case**, not chased further. *(closeable: no — doctrinal)*

### 🟡 BUCKET 2 — DAMAGES

| Gap | Tier | Closeable | Closing action |
|---|---|---|---|
| `medical_expenses_past` — Coastal Rehab PT bills | 1 | ✅ Yes | HIPAA records & billing request to Coastal Rehab |
| `lost_wages_past` — employer verification | 2 | ✅ Yes | Wage verification letter to Qualcomm HR |
| `medical_expenses_future` — Dr. Patel opinion | 2 | ✅ Yes | Future-care opinion request to treating physician |
| `non_economic_damages_basis` | 2 | ⚠️ Conditional | Structured client interview + family testimonials |
| `damages_comparables` (San Diego County, similar injuries) | 2 | ✅ Yes | Jury verdict reporter query |

### 🟢 BUCKET 4 — CREDIBILITY

| Gap | Tier | Closeable | Closing action |
|---|---|---|---|
| `pre_existing_conditions_disclosed` — 2022 back strain | 2 | ✅ Yes | 5-year pre-accident medical records request |
| `prior_claims_history_checked` (Santos) | 3 | ✅ Yes *(paywalled)* | **ISO ClaimSearch query — Negotiator's paywall-aware moment** |
| `treatment_gaps_addressed` — 11-day ER→PT gap | 3 | ✅ Yes | Document insurance prior-auth email chain |
| `client_social_media_review` | 3 | ✅ Yes | Public Instagram review by paralegal |
| `defendant_driving_history` (Harmon) | 3 | ⚠️ Conditional | Court records search for prior citations/civil suits |
| `client_account_consistency` | 2 | ❌ Internal | Cross-check intake vs. ER notes vs. police report |

---

## Section 5 — Expected Negotiator outputs (sample drafted outreach)

For the demo, drafting these three is the visual payoff:

### 5A. Commercial policy disclosure demand to Pacific Coast Plumbing
*(highest-leverage gap closer)*

- **Holder:** Pacific Coast Plumbing, Inc., risk management / general counsel
- **Authority cited:** VC §17150 (vehicle owner liability), respondeat superior doctrine
- **Ask:** Disclosure of commercial auto policy limits, identification of insurance carrier, notice of claim
- **Format:** Formal letter, certified mail, 30-day response window

### 5B. Subpoena duces tecum draft for Harmon's wireless records
*(liability evidence closer)*

- **Holder:** Harmon's wireless carrier (TBD — Negotiator drafts placeholder; attorney specifies after Harmon discovery)
- **Scope:** Call/text records 10/14/2025, 7:30 AM – 7:50 AM PST
- **Authority:** Civil subpoena under CCP §1985
- **Note:** Generally requires litigation to be filed; Negotiator flags this and offers a pre-suit alternative — voluntary preservation letter to Harmon's counsel

### 5C. HIPAA records request to Coastal Rehab
*(damages closer — workhorse, high-volume task)*

- **Holder:** Coastal Rehab Physical Therapy, records custodian
- **Format:** HIPAA-compliant authorization signed by client + cover letter
- **Ask:** Complete treatment records and itemized billing for 10/25/2025 – 12/20/2025
- **Authority:** 45 CFR §164.508

---

## Section 6 — Demo flow (5 minutes)

| Time | Step | What judges see |
|---|---|---|
| 0:00–0:30 | Open | One-screen case summary; *"This is a real flow we'd run on a real intake."* |
| 0:30–1:15 | Paste intake | Raw intake text → structured CaseFacts on screen |
| 1:15–2:15 | Harvester pulls statutes | Three CVC sections appear with full metadata; per se element checker shows 22350 ✅, 21453(a) ✅, 23123.5 ⚠️ *("violation evidence missing — theory pending")* — **demo wow #1** |
| 2:15–3:15 | Gap report | Four-bucket panel; coverage gaps tier-1 highlighted; **Pacific Coast Plumbing commercial policy** flagged as case-multiplying — **demo wow #2** |
| 3:15–4:15 | Negotiator drafts | Click "draft outreach" on the commercial policy gap → letter appears, properly addressed, citing VC §17150 — **demo wow #3** |
| 4:15–5:00 | Close | *"Without the system: paralegal spends a day on this. With the system: case profile + ranked gap analysis + drafted outreach in 90 seconds. And the system found the additional defendant the attorney might've missed."* |

---

## Section 7 — Pre-demo checklist

Things that need to be true before judging:

- [ ] All three CVC sections (22350, 21453(a), 23123.5) are in the Harvester database with full metadata (protected class, harm type, source URL)
- [ ] Doctrine template is loaded and the Organizer can run it against the case profile
- [ ] At least the three sample outreach drafts (5A, 5B, 5C) have working LLM prompts and template scaffolding
- [ ] The case profile is hardcoded as a JSON fixture so the Intake step doesn't have to be live-LLM during judging
- [ ] All source URLs in the demo (CVC sections, statutes referenced in outreach) return HTTP 200
- [ ] One backup recording of the demo exists in case of live failure

---

## Section 8 — Why this case shows the system thinks like a lawyer

Three moments where the system surfaces something a junior paralegal might miss:

1. **Pacific Coast Plumbing as defendant.** The intake mentions a work van but doesn't say "sue the employer." The system's `additional_defendants_check` field forces the question and flags it as the single highest-value open gap.

2. **VC 23123.5 as theory pending.** The system doesn't blindly add the texting statute because a bystander mentioned a phone. It separates "statute that *might* apply" from "statute we can prove" and flags the evidence gap that would convert one to the other.

3. **The 11-day treatment gap.** The system doesn't ignore it (which would let the insurer ambush) and doesn't panic (which would weaken the case). It surfaces it as a closeable credibility gap with a specific action: document the prior-auth delay.

These are exactly the moments where the demo earns its 50 craft + 30 extension + 10 story points.
