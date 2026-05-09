"""LLM-powered drafting for narrative outreach documents (policy disclosure demands)."""
from __future__ import annotations

import os

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore

MODEL = "claude-sonnet-4-6"

_SYSTEM = """\
You are a California plaintiff-side personal injury attorney drafting pre-litigation
outreach letters on behalf of a client.

Hard rules:
- Address the letter to the specific recipient identified in the instructions.
- Cite only the statutes and case law explicitly provided — do not invent citations.
- Do not include specific dollar demand amounts unless provided in the instructions.
- Format as a formal letter ready for attorney signature.
- Output letter text only — no preamble, no explanation, no markdown formatting.
- Use [BRACKETED PLACEHOLDERS] for any information not supplied that must be filled
  in before sending (e.g., [LAW FIRM ADDRESS], [STATE BAR NUMBER]).
- Include a "Via Certified Mail, Return Receipt Requested" notation at the top.
"""


def draft_with_llm(entry: dict, gap: dict, case_profile: dict) -> str:
    prompt_key = entry.get("llm_prompt_key", "")

    if Anthropic is None or not os.environ.get("ANTHROPIC_API_KEY"):
        return _offline_fallback(entry, case_profile)

    prompt = _build_prompt(prompt_key, case_profile)
    if not prompt:
        return _offline_fallback(entry, case_profile)

    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text if msg.content else _offline_fallback(entry, case_profile)


def _build_prompt(prompt_key: str, case_profile: dict) -> str:
    if prompt_key == "commercial_policy_demand":
        return _commercial_policy_prompt(case_profile)
    if prompt_key == "personal_policy_demand":
        return _personal_policy_prompt(case_profile)
    if prompt_key == "uim_coverage_demand":
        return _uim_coverage_prompt(case_profile)
    if prompt_key == "expert_engagement_letter":
        return _expert_engagement_prompt(case_profile)
    return ""


def _commercial_policy_prompt(cp: dict) -> str:
    plaintiff      = cp.get("plaintiff_name")       or "[PLAINTIFF NAME]"
    defendant      = cp.get("defendant_name")       or "[DEFENDANT NAME]"
    employer       = cp.get("defendant_employer")   or "[EMPLOYER]"
    vehicle        = cp.get("defendant_vehicle")    or "[VEHICLE]"
    date_          = cp.get("incident_date")        or "[DATE]"
    location       = cp.get("incident_location")   or "[LOCATION]"
    statutes       = ", ".join(cp.get("statutes_cited") or []) or "[STATUTES]"
    attorney       = cp.get("attorney_name")        or "[ATTORNEY NAME]"
    firm           = cp.get("attorney_firm")        or "[LAW FIRM]"
    file_no        = cp.get("file_number")          or "[FILE NUMBER]"

    return f"""\
Draft a formal commercial policy disclosure demand letter with the following facts:

PARTIES:
- Plaintiff: {plaintiff}
- Defendant driver: {defendant}
- Defendant employer / vehicle owner: {employer}
- Vehicle: {vehicle} (marked company vehicle)

INCIDENT:
- Date: {date_}
- Location: {location}
- Citations issued to {defendant}: {statutes}

DRAFTING ATTORNEY:
- Name: {attorney}
- Firm: {firm}
- File No.: {file_no}

The letter must:
1. Open with "Via Certified Mail, Return Receipt Requested" and a date line.
2. Be addressed to: Risk Management / General Counsel, {employer}.
3. Identify the firm and plaintiff; state the date, time, and location of the accident.
4. Assert that {defendant} was acting in the course and scope of employment with
   {employer} at the time of the accident, subjecting {employer} to vicarious liability
   under the doctrine of respondeat superior.
5. Cite California Vehicle Code § 17150, which imposes liability on a vehicle owner
   for the negligence of any person operating the vehicle with the owner's permission.
6. Cite Perez v. Van Groningen & Sons (1986) 41 Cal.3d 962 for the respondeat
   superior doctrine in the employer-liability context.
7. Demand in writing within thirty (30) days:
   (a) Confirmation of any commercial general liability or commercial auto insurance
       policy in effect on {date_} covering the vehicle or {defendant}'s operation of it;
   (b) The policy limits for bodily injury coverage under any such policy;
   (c) The name and contact information of the insurer and the assigned adjuster;
   (d) The policy number and claim number, if a claim has been opened.
8. State that failure to disclose this information may constitute bad faith and that
   all rights are expressly reserved.
9. Close with a 30-day response deadline and the attorney's signature block.
"""


def _personal_policy_prompt(cp: dict) -> str:
    plaintiff      = cp.get("plaintiff_name")           or "[PLAINTIFF NAME]"
    defendant      = cp.get("defendant_name")           or "[DEFENDANT NAME]"
    carrier        = cp.get("at_fault_carrier")         or "[CARRIER]"
    claim_no       = cp.get("at_fault_claim_number")    or "[CLAIM NUMBER]"
    adjuster       = cp.get("at_fault_adjuster")        or "[ADJUSTER]"
    date_          = cp.get("incident_date")            or "[DATE]"
    location       = cp.get("incident_location")       or "[LOCATION]"
    injuries       = ", ".join(cp.get("injuries") or []) or "[INJURIES]"
    attorney       = cp.get("attorney_name")            or "[ATTORNEY NAME]"
    firm           = cp.get("attorney_firm")            or "[LAW FIRM]"
    file_no        = cp.get("file_number")              or "[FILE NUMBER]"

    return f"""\
Draft a formal policy limits disclosure demand letter with the following facts:

PARTIES AND CLAIM:
- Plaintiff: {plaintiff}
- Defendant: {defendant}
- At-fault carrier: {carrier}
- Claim number: {claim_no}
- Adjuster: {adjuster}

INCIDENT:
- Date: {date_}
- Location: {location}
- Plaintiff's injuries: {injuries}

DRAFTING ATTORNEY:
- Name: {attorney}
- Firm: {firm}
- File No.: {file_no}

The letter must:
1. Open with "Via Certified Mail, Return Receipt Requested" and a Re: line showing
   the claim number.
2. Be addressed to: {adjuster}, {carrier}, Claim No. {claim_no}.
3. Identify the firm and plaintiff; state the accident date and injuries.
4. Assert liability of {defendant} for plaintiff's damages.
5. Demand written disclosure of the full bodily injury policy limits for {defendant}
   under any applicable {carrier} policy.
6. Reference California Insurance Code § 791.13 (limits on withholding personal
   information in insurance transactions).
7. Note that where a plaintiff's demand is at or below policy limits and the carrier
   fails to tender, the carrier may face excess liability beyond policy limits, citing
   Crisci v. Security Insurance Co. (1967) 66 Cal.2d 425 and Comunale v. Traders
   & General Insurance (1958) 50 Cal.2d 654.
8. Request the declarations page or written confirmation of limits within thirty (30)
   days.
9. Close with the attorney's signature block.
"""


def _uim_coverage_prompt(cp: dict) -> str:
    plaintiff         = cp.get("plaintiff_name")       or "[PLAINTIFF NAME]"
    plaintiff_carrier = cp.get("plaintiff_carrier")    or "[PLAINTIFF CARRIER]"
    defendant         = cp.get("defendant_name")       or "[DEFENDANT NAME]"
    at_fault_carrier  = cp.get("at_fault_carrier")     or "[AT-FAULT CARRIER]"
    date_             = cp.get("incident_date")        or "[DATE]"
    location          = cp.get("incident_location")   or "[LOCATION]"
    injuries          = ", ".join(cp.get("injuries") or []) or "[INJURIES]"
    attorney          = cp.get("attorney_name")        or "[ATTORNEY NAME]"
    firm              = cp.get("attorney_firm")        or "[LAW FIRM]"
    file_no           = cp.get("file_number")          or "[FILE NUMBER]"

    return f"""\
Draft a formal uninsured/underinsured motorist (UIM) coverage inquiry and demand
letter to plaintiff's own insurance carrier with the following facts:

PARTIES:
- Plaintiff / Insured: {plaintiff}
- Plaintiff's carrier: {plaintiff_carrier}
- At-fault defendant: {defendant}
- At-fault carrier: {at_fault_carrier}

INCIDENT:
- Date: {date_}
- Location: {location}
- Plaintiff's injuries: {injuries}

DRAFTING ATTORNEY:
- Name: {attorney}
- Firm: {firm}
- File No.: {file_no}

The letter must:
1. Open with "Via Certified Mail, Return Receipt Requested" and a Re: line.
2. Be addressed to the UIM Claims Department at {plaintiff_carrier}.
3. Identify the firm and plaintiff; state that plaintiff is an insured under a
   policy with {plaintiff_carrier} that includes UM/UIM coverage.
4. State that {defendant}'s bodily injury liability limits under {at_fault_carrier}
   may be inadequate to fully compensate plaintiff's damages from the {date_}
   accident and that plaintiff may be entitled to UIM benefits.
5. Cite California Insurance Code § 11580.2 (mandatory UM/UIM coverage requirement).
6. Demand written disclosure within thirty (30) days of: (a) identification of all
   UM/UIM policies covering {plaintiff}; (b) the applicable UIM policy limits;
   (c) confirmation of whether a UIM claim has been opened; (d) the assigned UIM
   adjuster's name and contact information.
7. Close with the attorney's signature block.
"""


def _expert_engagement_prompt(cp: dict) -> str:
    plaintiff = cp.get("plaintiff_name")       or "[PLAINTIFF NAME]"
    defendant = cp.get("defendant_name")       or "[DEFENDANT NAME]"
    date_     = cp.get("incident_date")        or "[DATE]"
    location  = cp.get("incident_location")   or "[LOCATION]"
    injuries  = ", ".join(cp.get("injuries") or []) or "[INJURIES]"
    statutes  = ", ".join(cp.get("statutes_cited") or []) or "[STATUTES]"
    attorney  = cp.get("attorney_name")        or "[ATTORNEY NAME]"
    firm      = cp.get("attorney_firm")        or "[LAW FIRM]"
    file_no   = cp.get("file_number")          or "[FILE NUMBER]"

    return f"""\
Draft a formal expert engagement and conflict-check letter to an accident
reconstruction firm with the following facts:

CASE:
- Plaintiff: {plaintiff}
- Defendant: {defendant}
- Incident date: {date_}
- Incident location: {location}
- Plaintiff's injuries: {injuries}
- Traffic citations issued to {defendant}: {statutes}

DRAFTING ATTORNEY:
- Name: {attorney}
- Firm: {firm}
- File No.: {file_no}

The letter must:
1. Open with "Via Certified Mail, Return Receipt Requested" and a Re: line.
2. Be addressed to: Expert Services Coordinator / Principal Engineer,
   [RECONSTRUCTION EXPERT FIRM], [EXPERT FIRM ADDRESS].
3. Briefly describe the accident: date, location, mechanism (intersection collision),
   citations issued to {defendant}, and the allegation of phone use at the time.
4. Request: (a) a conflict-of-interest check to confirm the firm has not been retained
   by {defendant} or any defendant-side carrier in this matter; (b) the firm's
   curriculum vitae, rate sheet, and examples of relevant prior casework.
5. State that if no conflict exists, the firm is being considered for retention as a
   consulting accident reconstruction expert under Cal. Code Civ. Proc. § 2034.
6. Specify the anticipated scope of work: reconstruction of vehicle speeds, point of
   impact, sight lines, and an opinion on whether phone use was consistent with the
   observed collision dynamics.
7. Include [BRACKETED PLACEHOLDERS] for the firm's name and address throughout.
8. Close with the attorney's signature block and contact information.
"""


def _offline_fallback(entry: dict, case_profile: dict) -> str:
    """Stub returned when ANTHROPIC_API_KEY is not set."""
    prompt_key = entry.get("llm_prompt_key", "outreach")
    recipient = (
        case_profile.get("defendant_employer")
        or case_profile.get("at_fault_adjuster")
        or "[RECIPIENT]"
    )
    plaintiff = case_profile.get("plaintiff_name") or "[PLAINTIFF]"
    authority = entry.get("authority") or ""
    return (
        f"[OFFLINE DRAFT — set ANTHROPIC_API_KEY for full LLM drafting]\n\n"
        f"TO: {recipient}\n"
        f"RE: {prompt_key.replace('_', ' ').title()} — {plaintiff}\n\n"
        f"This is a placeholder letter for a {entry.get('outreach_type', 'formal')} "
        f"outreach document.\n"
        f"Authority: {authority}\n\n"
        f"[Full letter text will be generated when ANTHROPIC_API_KEY is set.]"
    )
