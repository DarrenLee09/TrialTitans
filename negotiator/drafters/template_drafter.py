"""Jinja2-based drafting for structurally rigid outreach documents."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)


def render_template(entry: dict, gap: dict, case_profile: dict) -> str:
    template_name = entry.get("template")
    if not template_name:
        return ""
    ctx = _build_context(entry, gap, case_profile)
    tmpl = _env.get_template(template_name)
    return tmpl.render(**ctx)


def _five_years_before(date_str: str) -> str:
    """Return date_str minus 5 years, formatted identically. Falls back to placeholder."""
    try:
        dt = datetime.strptime(date_str, "%B %d, %Y")
        return dt.replace(year=dt.year - 5).strftime("%B %d, %Y")
    except (ValueError, AttributeError):
        return "[5 YEARS BEFORE INCIDENT DATE]"


def _build_context(entry: dict, gap: dict, case_profile: dict) -> dict:
    # Resolve treating provider and date range for HIPAA requests.
    # Uses the first entry in treating_providers and matches its date range.
    providers = case_profile.get("treating_providers") or []
    date_ranges = case_profile.get("treatment_date_ranges") or []
    provider_name = providers[0] if providers else "[PROVIDER NAME]"
    treatment_start = "[START DATE]"
    treatment_end = "[END DATE]"
    for dr in date_ranges:
        if dr.get("provider") == provider_name:
            treatment_start = dr.get("start", "[START DATE]")
            treatment_end = dr.get("end", "[END DATE]")
            break

    _incident_date_str = case_profile.get("incident_date") or "[INCIDENT DATE]"

    return {
        # Parties
        "plaintiff_name":    case_profile.get("plaintiff_name")    or "[PLAINTIFF NAME]",
        "defendant_name":    case_profile.get("defendant_name")    or "[DEFENDANT NAME]",
        "defendant_employer": case_profile.get("defendant_employer") or "[EMPLOYER]",
        "defendant_vehicle": case_profile.get("defendant_vehicle") or "[VEHICLE]",
        # Incident
        "incident_date":     _incident_date_str,
        "incident_location": case_profile.get("incident_location") or "[LOCATION]",
        # Statutes and injuries
        "statutes_cited":    ", ".join(case_profile.get("statutes_cited") or []),
        "injuries":          ", ".join(case_profile.get("injuries") or []),
        # Attorney/firm
        "attorney_name":     case_profile.get("attorney_name")     or "[ATTORNEY NAME]",
        "attorney_firm":     case_profile.get("attorney_firm")     or "[LAW FIRM]",
        "file_number":       case_profile.get("file_number")       or "[FILE NUMBER]",
        # Insurance
        "at_fault_carrier":       case_profile.get("at_fault_carrier")       or "[CARRIER]",
        "at_fault_claim_number":  case_profile.get("at_fault_claim_number")  or "[CLAIM NUMBER]",
        "at_fault_adjuster":      case_profile.get("at_fault_adjuster")      or "[ADJUSTER]",
        # Court/geography
        "today_date": date.today().strftime("%B %d, %Y"),
        "county":     case_profile.get("county") or "SAN DIEGO",
        "jurisdiction": case_profile.get("jurisdiction") or "CA",
        # HIPAA-specific
        "provider_name":    provider_name,
        "treatment_start":  treatment_start,
        "treatment_end":    treatment_end,
        # Wage verification
        "employer_name":      case_profile.get("plaintiff_employer") or "[EMPLOYER NAME]",
        "missed_work_start":  case_profile.get("missed_work_start")  or "[START DATE]",
        "missed_work_end":    case_profile.get("missed_work_end")    or "[END DATE]",
        # Future-care opinion request
        "mmi_date":           case_profile.get("mmi_date") or "[MMI DATE]",
        # UIM coverage demand (LLM path, but expose for completeness)
        "plaintiff_carrier":  case_profile.get("plaintiff_carrier") or "[PLAINTIFF CARRIER]",
        # Pre-existing records request — 5-year lookback window
        "pre_existing_end":   _incident_date_str,
        "pre_existing_start": _five_years_before(_incident_date_str),
    }
