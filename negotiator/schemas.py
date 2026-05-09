"""
Shared dict schemas for the Negotiator module.

Gap        — produced by the Organizer, consumed by plan_outreach()
CaseProfile — produced by the Organizer from parsed intake notes
OutreachPlan — returned by plan_outreach()

All three are plain dicts. This module is the interface contract between
the Organizer and Negotiator teams; the Organizer must produce Gap and
CaseProfile dicts that match the shapes documented here.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Gap
# ---------------------------------------------------------------------------
# bucket:         "liability" | "damages" | "coverage" | "credibility"
# field:          field name from doctrine template (e.g. "at_fault_policy_limits")
# leverage_tier:  int 1–4  (1 = highest impact on case value)
# closeable:      "yes" | "no" | "conditional"
# closing_action: free text from doctrine template describing the outreach
# status:         "open" | "in_progress" | "closed" | "unfillable"

def make_gap(
    bucket: str,
    field: str,
    leverage_tier: int,
    closeable: str,
    closing_action: str,
    status: str = "open",
) -> dict:
    """Construct a Gap dict. Used by the Organizer and in tests."""
    return {
        "bucket": bucket,
        "field": field,
        "leverage_tier": leverage_tier,
        "closeable": closeable,
        "closing_action": closing_action,
        "status": status,
    }


# ---------------------------------------------------------------------------
# CaseProfile
# ---------------------------------------------------------------------------
# plaintiff_name:         str
# plaintiff_employer:     str
# defendant_name:         str
# defendant_employer:     str | None    employer of the at-fault driver
# defendant_vehicle:      str | None    human-readable vehicle description
# incident_date:          str           e.g. "October 14, 2025"
# incident_location:      str           e.g. "Mission Blvd & Garnet Ave, San Diego"
# at_fault_carrier:       str | None    insurance carrier name
# at_fault_claim_number:  str | None
# at_fault_adjuster:      str | None
# treating_providers:     list[str]     names of medical providers
# treatment_date_ranges:  list[dict]    each: {provider, start, end}
# injuries:               list[str]
# statutes_cited:         list[str]
# jurisdiction:           str           "CA"
# county:                 str | None    "San Diego"
# file_number:            str | None
# attorney_name:          str | None
# attorney_firm:          str | None
# missed_work_start:      str | None
# missed_work_end:        str | None
# mmi_date:               str | None    e.g. "March 15, 2026"
# plaintiff_carrier:      str | None    plaintiff's own auto insurance carrier (for UIM demand)

def make_case_profile(**kwargs) -> dict:
    """Construct a CaseProfile dict with sensible empty defaults. Used in tests."""
    defaults: dict = {
        "plaintiff_name": "",
        "plaintiff_employer": "",
        "defendant_name": "",
        "defendant_employer": None,
        "defendant_vehicle": None,
        "incident_date": "",
        "incident_location": "",
        "at_fault_carrier": None,
        "at_fault_claim_number": None,
        "at_fault_adjuster": None,
        "treating_providers": [],
        "treatment_date_ranges": [],
        "injuries": [],
        "statutes_cited": [],
        "jurisdiction": "CA",
        "county": None,
        "file_number": None,
        "attorney_name": None,
        "attorney_firm": None,
        "missed_work_start": None,
        "missed_work_end": None,
        "mmi_date": None,
        "plaintiff_carrier": None,
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# OutreachPlan
# ---------------------------------------------------------------------------
# gap_field:               str    which gap this addresses
# data_holder:             str    name of the record holder
# holder_type:             str    see values below
# contact_method:          dict   {address: str|None, url: str|None, phone: str|None}
# outreach_type:           str    see values below
# drafted_artifact:        str    full letter text; empty string if paywalled/info-only
# caveats:                 list[str]   attorney-facing notes before sending
# requires_human_followup: bool
# paywalled:               bool
#
# holder_type values:
#   "insurance_carrier", "medical_provider", "employer", "wireless_carrier",
#   "government_agency", "paywalled_database", "expert_witness", "unidentified"
#   expert_witness: accident reconstruction firm or other testifying/consulting expert
#                   (requires attorney selection; requires_human_followup is always True)
#
# outreach_type values:
#   "hipaa_records_request", "policy_disclosure_demand", "subpoena_draft",
#   "wage_verification", "foia", "none", "generic"
