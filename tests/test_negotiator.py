"""Tests for the Negotiator module.

5A — commercial policy disclosure demand to Pacific Coast Plumbing (LLM path)
5B — phone records subpoena draft for Harmon's wireless carrier (template path)
5C — HIPAA records request to Coastal Rehab Physical Therapy (template path)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from negotiator.outreach import plan_outreach
from negotiator.registry import load_registry, lookup

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(scope="module")
def case_profile():
    return _load("case_profile_santos.json")


@pytest.fixture(scope="module")
def gap_5a():
    return _load("gap_5a_commercial_policy.json")


@pytest.fixture(scope="module")
def gap_5b():
    return _load("gap_5b_phone_records.json")


@pytest.fixture(scope="module")
def gap_5c():
    return _load("gap_5c_coastal_rehab.json")


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_registry_loads():
    reg = load_registry()
    assert "fields" in reg
    assert len(reg["fields"]) > 0


def test_registry_covers_demo_gaps():
    assert lookup("additional_defendants_check") is not None
    assert lookup("medical_expenses_past") is not None
    assert lookup("violation_evidence", "wireless carrier phone records") is not None


def test_registry_phone_records_subtype_routing():
    # closing_action containing "phone" should route to the subpoena entry
    entry = lookup("violation_evidence", "Subpoena to wireless carrier for phone records")
    assert entry is not None
    assert entry["outreach_type"] == "subpoena_draft"
    assert entry["holder_type"] == "wireless_carrier"


def test_registry_unknown_field_returns_none():
    assert lookup("nonexistent_field_xyz") is None


def test_registry_paywalled_fields():
    iso = lookup("prior_claims_history_checked")
    assert iso is not None
    assert iso["paywalled"] is True
    assert iso["outreach_type"] == "none"


# ---------------------------------------------------------------------------
# 5C — HIPAA records request (template path, fully offline)
# ---------------------------------------------------------------------------

def test_5c_hipaa_coastal_rehab(gap_5c, case_profile):
    plan = plan_outreach(gap_5c, case_profile)

    assert plan["gap_field"] == "medical_expenses_past"
    assert plan["holder_type"] == "medical_provider"
    assert plan["outreach_type"] == "hipaa_records_request"
    assert plan["paywalled"] is False
    assert plan["requires_human_followup"] is False

    artifact = plan["drafted_artifact"]
    assert "Coastal Rehab Physical Therapy" in artifact
    assert "164.508" in artifact          # 45 C.F.R. § 164.508
    assert "10/25/2025" in artifact       # treatment start
    assert "12/20/2025" in artifact       # treatment end
    assert "Maria Santos" in artifact


def test_5c_contact_method(gap_5c, case_profile):
    plan = plan_outreach(gap_5c, case_profile)
    # Medical providers don't have a pre-verified address in the registry
    assert plan["contact_method"]["address"] is None
    assert plan["contact_method"]["phone"] is None


# ---------------------------------------------------------------------------
# 5B — phone records subpoena (template path, fully offline)
# ---------------------------------------------------------------------------

def test_5b_phone_records_subpoena(gap_5b, case_profile):
    plan = plan_outreach(gap_5b, case_profile)

    assert plan["gap_field"] == "violation_evidence"
    assert plan["holder_type"] == "wireless_carrier"
    assert plan["outreach_type"] == "subpoena_draft"
    assert plan["paywalled"] is False

    artifact = plan["drafted_artifact"]
    assert "1985" in artifact             # CCP § 1985
    assert "23123.5" in artifact          # CVC texting statute
    assert "7:30" in artifact             # time window start
    assert "7:50" in artifact             # time window end
    assert "Robert Harmon" in artifact
    assert "[CARRIER NAME]" in artifact   # placeholder per option (a)
    assert "[CARRIER ADDRESS]" in artifact


def test_5b_caveats_contain_lawsuit_warning(gap_5b, case_profile):
    plan = plan_outreach(gap_5b, case_profile)
    caveat_text = " ".join(plan["caveats"]).lower()
    assert "lawsuit" in caveat_text or "filed" in caveat_text
    assert len(plan["caveats"]) >= 2      # pre-suit caveat + carrier addresses


def test_5b_caveats_contain_carrier_addresses(gap_5b, case_profile):
    plan = plan_outreach(gap_5b, case_profile)
    combined = " ".join(plan["caveats"])
    assert "AT&T" in combined
    assert "Verizon" in combined
    assert "T-Mobile" in combined


# ---------------------------------------------------------------------------
# 5A — commercial policy demand (LLM path — Anthropic client mocked)
# ---------------------------------------------------------------------------

_MOCK_COMMERCIAL_LETTER = """\
Via Certified Mail, Return Receipt Requested

[TODAY'S DATE]

Risk Management / General Counsel
Pacific Coast Plumbing, Inc.
[Address]

Re: Notice of Claim — Maria Santos v. Robert Harmon and Pacific Coast Plumbing, Inc.
    File No.: 2026-0341

Dear Risk Management Representative:

This firm represents Maria Santos in connection with a serious personal injury
arising from an accident on October 14, 2025 at Mission Blvd & Garnet Ave,
San Diego, CA.

Robert Harmon was operating a 2023 Ford Transit work van marked Pacific Coast
Plumbing, Inc. at the time of the accident. As the employer and vehicle owner,
Pacific Coast Plumbing, Inc. is subject to vicarious liability under the doctrine
of respondeat superior (Perez v. Van Groningen & Sons (1986) 41 Cal.3d 962) and
California Vehicle Code § 17150.

We demand disclosure within thirty (30) days of: (a) any commercial auto policy
in effect on October 14, 2025; (b) policy limits for bodily injury; (c) carrier
name, claim number, and adjuster contact. All rights reserved.

Respectfully,
J. Liu
[LAW FIRM NAME]
"""


@patch("negotiator.drafters.llm_drafter.Anthropic")
def test_5a_commercial_policy_demand(mock_cls, gap_5a, case_profile):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=_MOCK_COMMERCIAL_LETTER)]
    )

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        plan = plan_outreach(gap_5a, case_profile)

    assert plan["gap_field"] == "additional_defendants_check"
    assert plan["holder_type"] == "employer"
    assert plan["outreach_type"] == "policy_disclosure_demand"
    assert plan["paywalled"] is False

    artifact = plan["drafted_artifact"]
    assert "Pacific Coast Plumbing" in artifact
    assert "17150" in artifact            # Cal. Veh. Code § 17150
    assert "respondeat superior" in artifact.lower()


@patch("negotiator.drafters.llm_drafter.Anthropic")
def test_5a_prompt_contains_key_facts(mock_cls, gap_5a, case_profile):
    """Verify the prompt sent to the LLM includes critical case facts."""
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=_MOCK_COMMERCIAL_LETTER)]
    )

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        plan_outreach(gap_5a, case_profile)

    call_kwargs = mock_client.messages.create.call_args
    user_message = call_kwargs[1]["messages"][0]["content"]

    assert "Pacific Coast Plumbing" in user_message
    assert "Robert Harmon" in user_message
    assert "17150" in user_message
    assert "respondeat superior" in user_message.lower()


def test_5a_offline_fallback_structure(gap_5a, case_profile):
    """Without an API key the fallback dict must still have the right shape."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        plan = plan_outreach(gap_5a, case_profile)

    assert plan["gap_field"] == "additional_defendants_check"
    assert plan["holder_type"] == "employer"
    assert plan["outreach_type"] == "policy_disclosure_demand"
    assert isinstance(plan["drafted_artifact"], str)
    assert isinstance(plan["caveats"], list)


# ---------------------------------------------------------------------------
# Paywalled gaps — info-only, no artifact
# ---------------------------------------------------------------------------

def test_paywalled_iso_claimsearch(case_profile):
    gap = {
        "bucket": "credibility",
        "field": "prior_claims_history_checked",
        "leverage_tier": 3,
        "closeable": "yes",
        "closing_action": "ISO ClaimSearch query",
        "status": "open",
    }
    plan = plan_outreach(gap, case_profile)

    assert plan["paywalled"] is True
    assert plan["requires_human_followup"] is True
    assert plan["drafted_artifact"] == ""
    assert plan["outreach_type"] == "none"
    assert "verisk.com" in (plan["contact_method"].get("url") or "")


# ---------------------------------------------------------------------------
# Long-tail (unregistered gap) — falls back to search_holder
# ---------------------------------------------------------------------------

def test_unregistered_gap_returns_unidentified(case_profile):
    gap = {
        "bucket": "liability",
        "field": "traffic_signal_maintenance_records",
        "leverage_tier": 2,
        "closeable": "conditional",
        "closing_action": "Request signal maintenance logs from city traffic engineering",
        "status": "open",
    }
    # No API key → offline search fallback
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        plan = plan_outreach(gap, case_profile)

    assert plan["holder_type"] == "unidentified"
    assert plan["requires_human_followup"] is True


# ---------------------------------------------------------------------------
# Demo-case smoke test — every Section 4 gap must route without crashing
# ---------------------------------------------------------------------------

_CATEGORY_C_FIELDS = {
    "defense_anticipation",
    "client_account_consistency",
    "non_economic_damages_basis",
    "treatment_gaps_addressed",
    "client_social_media_review",
}

_MOCK_LLM_LETTER = "[MOCK LETTER — LLM path mocked for smoke test]"


@patch("negotiator.drafters.llm_drafter.Anthropic")
def test_demo_case_smoke(mock_cls, case_profile):
    """Every gap in demo-case.md Section 4 routes without crashing."""
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=_MOCK_LLM_LETTER)]
    )

    import json
    gaps = json.loads((FIXTURES / "gaps_demo_section4.json").read_text())
    required_keys = {
        "gap_field", "data_holder", "holder_type", "contact_method",
        "outreach_type", "drafted_artifact", "caveats",
        "requires_human_followup", "paywalled",
    }

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        for gap in gaps:
            plan = plan_outreach(gap, case_profile)
            assert required_keys.issubset(plan.keys()), (
                f"Missing keys for {gap['field']}: {required_keys - plan.keys()}"
            )
            assert isinstance(plan["drafted_artifact"], str)
            assert isinstance(plan["caveats"], list)
            # Only Category-C gaps are allowed to be unidentified
            if gap["field"] not in _CATEGORY_C_FIELDS:
                assert plan["holder_type"] != "unidentified", (
                    f"{gap['field']} must not be unidentified; "
                    f"got holder_type={plan['holder_type']!r}"
                )


# ---------------------------------------------------------------------------
# Category B — new gap content tests
# ---------------------------------------------------------------------------

@patch("negotiator.drafters.llm_drafter.Anthropic")
def test_client_uim_coverage(mock_cls, case_profile):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Via Certified Mail\n\nState Farm UIM Claims Department\n\nRE: UIM demand — 11580.2")]
    )

    gap = _load("gap_client_uim.json")
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        plan = plan_outreach(gap, case_profile)

    assert plan["holder_type"] == "insurance_carrier"
    assert plan["outreach_type"] == "policy_disclosure_demand"
    assert plan["paywalled"] is False
    artifact = plan["drafted_artifact"]
    assert "State Farm" in artifact
    assert "11580.2" in artifact
    # must not bleed at-fault carrier details into plaintiff-side UIM letter
    assert "Nakamura" not in artifact
    assert "GEICO" not in artifact


def test_client_uim_contact_resolves_to_plaintiff_carrier(case_profile):
    gap = _load("gap_client_uim.json")
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        plan = plan_outreach(gap, case_profile)
    assert "State Farm" in (plan["contact_method"]["address"] or "")
    assert "GEICO" not in (plan["contact_method"]["address"] or "")


def test_umbrella_policy_check_is_info_only(case_profile):
    gap = _load("gap_umbrella_check.json")
    plan = plan_outreach(gap, case_profile)

    assert plan["outreach_type"] == "none"
    assert plan["drafted_artifact"] == ""
    assert plan["requires_human_followup"] is True
    assert plan["paywalled"] is False
    caveat_text = " ".join(plan["caveats"]).lower()
    assert "umbrella" in caveat_text


def test_defendant_assets_check_template(case_profile):
    gap = _load("gap_defendant_assets.json")
    plan = plan_outreach(gap, case_profile)

    assert plan["holder_type"] == "government_agency"
    assert plan["outreach_type"] == "foia"
    artifact = plan["drafted_artifact"]
    assert "Robert Harmon" in artifact
    assert "San Diego" in artifact
    assert "County" in artifact
    assert "27201" in artifact


@patch("negotiator.drafters.llm_drafter.Anthropic")
def test_causation_chain_expert_witness(mock_cls, case_profile):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Via Certified Mail\n\n[RECONSTRUCTION EXPERT FIRM]\n[EXPERT FIRM ADDRESS]\n\nConflict check requested. CCP § 2034.")]
    )

    gap = _load("gap_causation_chain.json")
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        plan = plan_outreach(gap, case_profile)

    assert plan["holder_type"] == "expert_witness"
    assert plan["requires_human_followup"] is True
    assert plan["paywalled"] is False
    artifact = plan["drafted_artifact"]
    assert "[RECONSTRUCTION EXPERT FIRM]" in artifact
    caveat_text = " ".join(plan["caveats"])
    assert "actar.org" in caveat_text
    assert "Robson" in caveat_text


@patch("negotiator.drafters.llm_drafter.Anthropic")
def test_causation_chain_prompt_contains_key_facts(mock_cls, case_profile):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="[mock letter]")]
    )

    gap = _load("gap_causation_chain.json")
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        plan_outreach(gap, case_profile)

    call_kwargs = mock_client.messages.create.call_args
    user_message = call_kwargs[1]["messages"][0]["content"]
    assert "Robert Harmon" in user_message
    assert "Mission Blvd" in user_message
    assert "2034" in user_message


def test_medical_expenses_future_template(case_profile):
    gap = _load("gap_medical_future.json")
    plan = plan_outreach(gap, case_profile)

    assert plan["holder_type"] == "medical_provider"
    assert plan["paywalled"] is False
    artifact = plan["drafted_artifact"]
    assert "Maria Santos" in artifact
    assert "future" in artifact.lower()
    assert "care" in artifact.lower()
    assert "March 15, 2026" in artifact   # mmi_date
    assert "Coastal Rehab Physical Therapy" in plan["data_holder"]


def test_pre_existing_records_template(case_profile):
    gap = _load("gap_pre_existing.json")
    plan = plan_outreach(gap, case_profile)

    assert plan["holder_type"] == "medical_provider"
    assert plan["outreach_type"] == "hipaa_records_request"
    artifact = plan["drafted_artifact"]
    assert "164.508" in artifact
    assert "Maria Santos" in artifact
    assert "October 14, 2025" in artifact       # pre_existing_end
    assert "October 14, 2020" in artifact       # pre_existing_start (5 years prior)
    # must NOT contain the treatment-episode start date (that's the HIPAA request, not this one)
    assert "10/25/2025" not in artifact


def test_camera_footage_routes(case_profile):
    gap = _load("gap_camera_footage.json")
    plan = plan_outreach(gap, case_profile)

    assert plan["holder_type"] == "government_agency"
    assert plan["outreach_type"] == "foia"
    artifact = plan["drafted_artifact"]
    assert "Mission Blvd" in artifact
    assert "6250" in artifact
    caveat_text = " ".join(plan["caveats"]).lower()
    assert "overwrite" in caveat_text or "retention" in caveat_text or "72" in caveat_text


# ---------------------------------------------------------------------------
# Category C — internal-task tests (no artifact, attorney caveat present)
# ---------------------------------------------------------------------------

def _make_internal_gap(field: str, closing_action: str, bucket: str = "liability") -> dict:
    return {
        "bucket": bucket,
        "field": field,
        "leverage_tier": 3,
        "closeable": "no",
        "closing_action": closing_action,
        "status": "open",
    }


def test_defense_anticipation_internal(case_profile):
    gap = _make_internal_gap("defense_anticipation", "Attorney analysis — sudden emergency rebuttal")
    plan = plan_outreach(gap, case_profile)
    assert plan["outreach_type"] == "none"
    assert plan["drafted_artifact"] == ""
    assert plan["requires_human_followup"] is True
    assert plan["paywalled"] is False
    assert any("attorney" in c.lower() for c in plan["caveats"])


def test_client_account_consistency_internal(case_profile):
    gap = _make_internal_gap("client_account_consistency", "Cross-check intake vs. ER notes vs. police report", bucket="credibility")
    plan = plan_outreach(gap, case_profile)
    assert plan["outreach_type"] == "none"
    assert plan["drafted_artifact"] == ""
    assert plan["requires_human_followup"] is True
    assert plan["paywalled"] is False
    assert any("cross-check" in c.lower() or "internal" in c.lower() for c in plan["caveats"])


def test_non_economic_damages_basis_internal(case_profile):
    gap = _make_internal_gap("non_economic_damages_basis", "Structured client interview + family testimonials", bucket="damages")
    plan = plan_outreach(gap, case_profile)
    assert plan["outreach_type"] == "none"
    assert plan["drafted_artifact"] == ""
    assert plan["requires_human_followup"] is True
    assert plan["paywalled"] is False
    assert any("interview" in c.lower() or "internal" in c.lower() for c in plan["caveats"])


def test_treatment_gaps_addressed_internal(case_profile):
    gap = _make_internal_gap("treatment_gaps_addressed", "Document insurance prior-auth email chain", bucket="credibility")
    plan = plan_outreach(gap, case_profile)
    assert plan["outreach_type"] == "none"
    assert plan["drafted_artifact"] == ""
    assert plan["requires_human_followup"] is True
    assert plan["paywalled"] is False
    assert any("prior-auth" in c.lower() or "internal" in c.lower() for c in plan["caveats"])


def test_client_social_media_review_internal(case_profile):
    gap = _make_internal_gap("client_social_media_review", "Public Instagram review by paralegal", bucket="credibility")
    plan = plan_outreach(gap, case_profile)
    assert plan["outreach_type"] == "none"
    assert plan["drafted_artifact"] == ""
    assert plan["requires_human_followup"] is True
    assert plan["paywalled"] is False
    assert any("social media" in c.lower() or "paralegal" in c.lower() for c in plan["caveats"])


# ---------------------------------------------------------------------------
# Violation-evidence subtype router — camera vs. phone
# ---------------------------------------------------------------------------

def test_violation_evidence_subtype_routing_camera():
    entry = lookup("violation_evidence", "Canvas businesses near intersection for camera footage")
    assert entry is not None
    assert entry["holder_type"] == "government_agency"
    assert entry["outreach_type"] == "foia"


def test_violation_evidence_subtype_routing_phone_unchanged():
    entry = lookup("violation_evidence", "Subpoena to wireless carrier for phone records")
    assert entry is not None
    assert entry["holder_type"] == "wireless_carrier"
    assert entry["outreach_type"] == "subpoena_draft"


def test_violation_evidence_camera_does_not_match_phone_keywords():
    entry = lookup("violation_evidence", "Canvas businesses near intersection for camera footage")
    assert entry["holder_type"] != "wireless_carrier"


# ---------------------------------------------------------------------------
# Generality test — no Santos-specific strings in any drafted artifact
# ---------------------------------------------------------------------------

_SANTOS_STRINGS = [
    "Santos", "Maria", "Harmon", "Pacific Coast Plumbing",
    "Mission Blvd", "Qualcomm", "GEICO", "Nakamura",
    "Coastal Rehab", "Garnet", "2026-0341",
]


def test_no_santos_strings_in_smith_artifacts():
    """Template artifacts for Smith case must contain no Santos-specific strings."""
    smith = json.loads((FIXTURES / "case_profile_smith.json").read_text())

    template_gaps = [
        {"bucket": "damages", "field": "medical_expenses_past", "leverage_tier": 1,
         "closeable": "yes", "closing_action": "HIPAA records to treating provider", "status": "open"},
        {"bucket": "damages", "field": "lost_wages_past", "leverage_tier": 2,
         "closeable": "yes", "closing_action": "Wage verification to Lockheed Martin HR", "status": "open"},
        {"bucket": "damages", "field": "medical_expenses_future", "leverage_tier": 2,
         "closeable": "yes", "closing_action": "Future-care opinion request to treating physician", "status": "open"},
        {"bucket": "credibility", "field": "pre_existing_conditions_disclosed", "leverage_tier": 2,
         "closeable": "yes", "closing_action": "5-year pre-accident medical records request", "status": "open"},
        {"bucket": "coverage", "field": "defendant_assets_check", "leverage_tier": 2,
         "closeable": "yes", "closing_action": "Run county recorder and CA SOS search", "status": "open"},
        {"bucket": "credibility", "field": "defendant_driving_history", "leverage_tier": 3,
         "closeable": "conditional", "closing_action": "DMV record request", "status": "open"},
        {"bucket": "liability", "field": "violation_evidence", "leverage_tier": 2,
         "closeable": "conditional", "closing_action": "Canvas businesses for camera footage", "status": "open"},
    ]

    for gap in template_gaps:
        plan = plan_outreach(gap, smith)
        artifact = plan["drafted_artifact"]
        for bad_string in _SANTOS_STRINGS:
            assert bad_string not in artifact, (
                f"Santos-specific string {bad_string!r} found in artifact "
                f"for gap {gap['field']} using Smith profile"
            )
