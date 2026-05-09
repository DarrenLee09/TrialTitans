"""Tests for ai.query_interpreter (offline keyword-matching path).

The Claude path is exercised opportunistically when ANTHROPIC_API_KEY is set;
the offline path is the always-on contract that must work in CI without a key.
"""
from __future__ import annotations

from ai.query_interpreter import interpret


def test_extracts_jurisdiction_by_full_state_name():
    result = interpret(
        "DUI cases in Florida",
        jurisdictions=[("CA", "California"), ("FL", "Florida")],
        factors=[],
    )
    assert "FL" in result["jurisdictions"]


def test_extracts_jurisdiction_by_code():
    result = interpret(
        "statutes in CA about speeding",
        jurisdictions=[("CA", "California"), ("TX", "Texas")],
        factors=[],
    )
    assert "CA" in result["jurisdictions"]


def test_extracts_multiple_jurisdictions():
    result = interpret(
        "compare DUI laws in California and Texas",
        jurisdictions=[("CA", "California"), ("TX", "Texas"), ("FL", "Florida")],
        factors=[],
    )
    assert set(result["jurisdictions"]) == {"CA", "TX"}


def test_extracts_factor_by_label():
    result = interpret(
        "reckless driving in school zones",
        jurisdictions=[],
        factors=[("RECKLESS_DRIVING", "Reckless Driving")],
    )
    assert "RECKLESS_DRIVING" in result["factors"]


def test_intent_strips_matched_jurisdictions_and_factors():
    result = interpret(
        "reckless driving in Florida involving school zones",
        jurisdictions=[("FL", "Florida")],
        factors=[("RECKLESS_DRIVING", "Reckless Driving")],
    )
    intent_lower = result["intent"].lower()
    assert "florida" not in intent_lower
    assert "reckless driving" not in intent_lower
    assert "school zones" in intent_lower


def test_no_matches_returns_query_as_intent():
    result = interpret(
        "photosynthesis",
        jurisdictions=[("CA", "California")],
        factors=[("DUI_DWI", "DUI/DWI")],
    )
    assert result["jurisdictions"] == []
    assert result["factors"] == []
    assert "photosynthesis" in result["intent"]


def test_dedupes_jurisdiction_when_both_code_and_name_appear():
    # "California (CA) statutes" — should match CA once, not twice.
    result = interpret(
        "California CA statutes",
        jurisdictions=[("CA", "California")],
        factors=[],
    )
    assert result["jurisdictions"] == ["CA"]


def test_does_not_match_jurisdiction_code_inside_word():
    # "Cars in CAlamity" — "CA" appears inside "calamity" but is not a word.
    result = interpret(
        "calamity",
        jurisdictions=[("CA", "California")],
        factors=[],
    )
    assert "CA" not in result["jurisdictions"]


def test_matches_factor_via_label_token_when_label_has_separator():
    # "DUI/DWI" — the literal label won't appear if the user just types "DUI".
    # Tokenize and match individual words.
    result = interpret(
        "DUI cases",
        jurisdictions=[],
        factors=[("DUI_DWI", "DUI/DWI")],
    )
    assert "DUI_DWI" in result["factors"]


def test_does_not_match_factor_via_token_shared_across_labels():
    # "Driving" appears in three factor labels. A query like "drunk driving"
    # must NOT pick one of them at random — the token isn't a unique signal.
    factors = [
        ("RECKLESS_DRIVING", "Reckless Driving"),
        ("DISTRACTED_DRIVING", "Distracted Driving"),
        ("WIRELESS_DRIVING", "Wireless Phone While Driving"),
    ]
    result = interpret("drunk driving", jurisdictions=[], factors=factors)
    assert result["factors"] == [], f"expected no factors, got {result['factors']}"


def test_does_not_double_match_when_full_label_already_matched():
    # "fleeing a police officer" should match FLEEING_A_POLICE_OFFICER only,
    # not also FLEEING_THE_SCENE_OF_A_COLLISION just because they share "Fleeing".
    factors = [
        ("FLEEING_THE_SCENE_OF_A_COLLISION", "Fleeing the Scene of a Collision"),
        ("FLEEING_A_POLICE_OFFICER", "Fleeing a Police Officer"),
    ]
    result = interpret("fleeing a police officer", jurisdictions=[], factors=factors)
    assert result["factors"] == ["FLEEING_A_POLICE_OFFICER"]


def test_label_tokens_skip_stopwords_and_short_words():
    # Don't extract "Failure to Maintain Lane" just because the query has "to".
    result = interpret(
        "to a the of",
        jurisdictions=[],
        factors=[("FAILURE_TO_MAINTAIN_LANE", "Failure to Maintain Lane")],
    )
    assert result["factors"] == []


def test_strips_filler_words_from_intent():
    result = interpret(
        "DUI in Florida",
        jurisdictions=[("FL", "Florida")],
        factors=[("DUI_DWI", "DUI/DWI")],
    )
    # "DUI" is a factor label substring (DUI/DWI). After stripping FL and DUI/DWI
    # we're left with "DUI in" or similar — leading "in" should be cleaned.
    assert not result["intent"].lower().startswith("in ")
