# Organizer & Negotiator — Question Brainstorm

A working doc for picking which features to build. Questions are framed from an attorney/paralegal perspective.

## Framing

| Tool | Direction | Job |
|---|---|---|
| **Organizer** | Inward-facing | Make sense of what I already have for *this* case — surface state, theory, gaps |
| **Negotiator** | Outward-facing | Go fill the gaps — find data holders, draft outreach, track the pipeline |

The handoff: Organizer surfaces the gap → Negotiator fills it.

---

## Organizer questions

### Case state — "what do I know?"
- Show me everything I have on this case in one view
- What statutes have I already pulled, and why each one?
- What's the timeline of events? (accident → first medical visit → MMI → demand → filing)
- What deadlines am I tracking? (statute of limitations, discovery cutoff, trial date)

### Liability theory
- What's my theory of fault, and what statutes support it?
- For each negligence per se element (duty / breach / causation / harm), do I have the evidence?
- Where are the holes in my liability argument?
- What defenses will the insurer raise, and what's my counter?

### Damages picture
- What's my running damages tally? (medical bills, lost wages, future costs)
- How does this case compare to similar cases — same injury type, fault pattern, jurisdiction?
- What's the realistic settlement range?

### Coverage map
- What insurance policies are in play? (other driver's liability, MedPay, UM/UIM, umbrella)
- What's the maximum recoverable amount given known limits?

### Gap surfacing — "what should I do next?"
- What evidence am I still missing? (police report, medical records, witness statement)
- Which gaps are blockers vs. nice-to-have?
- *(this is the bridge to the Negotiator)*

---

## Negotiator questions

Organized by the four factor buckets.

### Liability gaps
- What were the road and weather conditions at time of crash? → NOAA, local DOT
- Is this intersection known to be dangerous? How many prior crashes here? → city/state crash data
- Was the at-fault vehicle subject to recalls? → NHTSA
- Were there traffic cameras? Who maintains footage?
- Has the at-fault driver been cited or sued before? → court records, DMV

### Damages gaps
- Typical settlement range for *[injury type]* in *[jurisdiction]*? → jury verdict reporters
- Standard cost for *[medical procedure]*? → medical cost benchmarks
- Earning capacity by occupation? → BLS wage data

### Coverage gaps *(highest leverage)*
- What is the at-fault driver's policy limit? → policy disclosure demand
- Does the at-fault driver have personal assets? → property records, business registrations
- Was the driver on the job? Who's the employer? → LinkedIn, business filings, vehicle registration
- Is there a third party we haven't surfaced? → bar (dram shop), manufacturer (product liability), contractor (road condition), city (sovereign immunity)

### Credibility gaps
- Does my client have a prior claims history? → ISO ClaimSearch *(paywalled — exactly the gap the Negotiator is meant to detect)*
- Does the at-fault driver have a prior driving history?

### Outreach workflow — the unique Negotiator capability
1. **Detect** the gap (fed in from Organizer)
2. **Identify** the data holder (records office, agency, publisher)
3. **Draft** the outreach (FOIA letter, records request, subpoena draft)
4. **Track** the pipeline (sent / awaiting / received)

---

## Strategic priority — leverage by question type

Not all questions are equal. These four have outsized impact on case value:

| Question | Why it matters most |
|---|---|
| What's the at-fault policy limit? | Determines the *ceiling* of the case. Everything else sits below this. |
| Is there a third party with deeper pockets? | Can multiply the case ceiling 10–100×. |
| What's my client's comparative fault %? | Each point reduces recovery proportionally. |
| Jurisdiction-specific settlement range for this injury? | Anchors the demand letter number. |

If the Negotiator has time for only a few flagship features, these four are where it should focus.

---

## Open questions for the team

- Given staffing (1 dev each on Organizer and Negotiator?), which 2–3 features per tool actually ship?
- Does the Organizer build on top of the Harvester's existing UI-05 case workspace, or stand alone?
- For the Negotiator, do we ship a real outreach pipeline (sent emails, tracked status) or a generated drafts demo?
