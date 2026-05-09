from retrieval.citation_parser import parse


def test_parses_ca_vehicle_code():
    cite = parse("CA Veh Code 22107")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Vehicle Code"
    assert cite.section == "22107"


def test_parses_with_section_symbol():
    cite = parse("Cal. Vehicle Code § 22350")
    assert cite is not None
    assert cite.section == "22350"


def test_returns_none_for_garbage():
    assert parse("hello world") is None


def test_bare_section_with_symbol_defaults_to_ca_vehicle_code():
    cite = parse("§23152")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Vehicle Code"
    assert cite.section == "23152"


def test_bare_section_without_symbol_defaults_to_ca_vehicle_code():
    cite = parse("23152")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.section == "23152"


def test_jurisdiction_plus_section_defaults_code_to_vehicle_code():
    cite = parse("CA 23152")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Vehicle Code"
    assert cite.section == "23152"


def test_code_plus_section_defaults_jurisdiction_to_ca():
    cite = parse("Veh. Code §23152")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Vehicle Code"
    assert cite.section == "23152"


def test_parses_full_with_subsection():
    cite = parse("Cal. Veh. Code §2800.1(a)")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Vehicle Code"
    assert cite.section == "2800.1"
    assert cite.subsection == "(a)"


def test_parses_il_alias():
    cite = parse("IL 11-501")
    assert cite is not None
    assert cite.jurisdiction == "IL"
    assert cite.section == "11-501"


def test_parses_ga_alias():
    assert parse("GA 40-6-181").jurisdiction == "GA"


def test_parses_oh_alias():
    assert parse("OH 4511.19").jurisdiction == "OH"


def test_bare_section_guard_rejects_section_with_extra_words():
    # "23152 cases" is not a citation — it's a search query about section 23152.
    # Without the guard, the bare-section fallback would eat any number.
    assert parse("23152 cases involving school zones") is None


def test_bare_section_handles_decimal_and_letter_suffix():
    cite = parse("§2800.1")
    assert cite is not None
    assert cite.section == "2800.1"
    assert cite.subsection is None
