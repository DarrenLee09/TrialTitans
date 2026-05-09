from retrieval.citation_parser import parse


def test_parses_ca_vehicle_code():
    cite = parse("CA Veh Code 22107")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Veh Code"
    assert cite.section == "22107"


def test_parses_ca_penal_code():
    cite = parse("CA Penal Code 187")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Pen Code"
    assert cite.section == "187"


def test_parses_ca_civil_code():
    cite = parse("Cal. Civ Code § 1714")
    assert cite is not None
    assert cite.jurisdiction == "CA"
    assert cite.code_name == "Civ Code"
    assert cite.section == "1714"


def test_parses_with_section_symbol():
    cite = parse("Cal. Vehicle Code § 22350")
    assert cite is not None
    assert cite.section == "22350"


def test_returns_none_for_garbage():
    assert parse("hello world") is None
