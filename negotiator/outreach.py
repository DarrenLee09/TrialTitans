"""Public entry point for the Negotiator module."""
from __future__ import annotations

from negotiator.registry import lookup
from negotiator.drafters.template_drafter import render_template
from negotiator.drafters.llm_drafter import draft_with_llm
from negotiator.search import search_holder


def plan_outreach(gap: dict, case_profile: dict) -> dict:
    """
    Given a Gap dict and CaseProfile dict, return an OutreachPlan dict.

    Routing order:
      1. Registry lookup by gap field (+ keyword subtype for ambiguous fields)
      2. Template drafting (structurally rigid documents: HIPAA, subpoena, DMV, wage)
      3. LLM drafting (narrative documents: policy disclosure demands)
      4. Web search fallback for unregistered gap types
    """
    field = gap.get("field", "")
    closing_action = gap.get("closing_action", "")

    entry = lookup(field, closing_action)
    if entry is None:
        return search_holder(gap, case_profile)

    return _build_plan(entry, gap, case_profile)


def _build_plan(entry: dict, gap: dict, case_profile: dict) -> dict:
    field = gap.get("field", "")
    engine = entry.get("engine", "none")
    outreach_type = entry.get("outreach_type", "none")
    holder_type = entry.get("holder_type", "unidentified")
    paywalled = entry.get("paywalled", False)
    caveats = list(entry.get("caveats") or [])

    holder_name = _resolve_holder_name(entry, case_profile)
    contact = _resolve_contact(entry, case_profile)

    if engine == "template":
        artifact = render_template(entry, gap, case_profile)
    elif engine == "llm":
        artifact = draft_with_llm(entry, gap, case_profile)
    else:
        artifact = ""

    rfh_override = entry.get("requires_human_followup")
    requires_human_followup = (
        rfh_override if rfh_override is not None
        else (paywalled or holder_type == "unidentified")
    )

    return {
        "gap_field": field,
        "data_holder": holder_name,
        "holder_type": holder_type,
        "contact_method": contact,
        "outreach_type": outreach_type,
        "drafted_artifact": artifact,
        "caveats": caveats,
        "requires_human_followup": requires_human_followup,
        "paywalled": paywalled,
    }


def _resolve_holder_name(entry: dict, case_profile: dict) -> str:
    source = entry.get("holder_name_source")
    if source:
        val = case_profile.get(source)
        if isinstance(val, list):
            return val[0] if val else entry.get("holder_name") or "[UNKNOWN HOLDER]"
        if val:
            return val
    return entry.get("holder_name") or "[UNKNOWN HOLDER]"


def _resolve_contact(entry: dict, case_profile: dict) -> dict:
    address = entry.get("holder_address")
    url = entry.get("contact_url")

    # For insurance carriers, surface carrier name as address hint.
    # Use holder_name_source to determine which carrier key to read so that
    # plaintiff-side UIM entries don't pull the at-fault adjuster.
    if entry.get("holder_type") == "insurance_carrier":
        name_source = entry.get("holder_name_source", "at_fault_carrier")
        if name_source == "plaintiff_carrier":
            carrier = case_profile.get("plaintiff_carrier")
            if carrier:
                address = f"{carrier} UIM Claims Department"
        else:
            adjuster = case_profile.get("at_fault_adjuster")
            carrier = case_profile.get("at_fault_carrier")
            if adjuster and carrier:
                address = f"Attn: {adjuster}, {carrier} Claims Department"
            elif carrier:
                address = f"{carrier} Claims Department"

    return {"address": address, "url": url, "phone": None}
