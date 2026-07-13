from backend.api.services.classification_engine import derive_prefix_pattern


def test_strips_airbnb_g_suffix():
    p, mt = derive_prefix_pattern("VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROGLGC5S4PWE5OOQQ6HLF45V2S")
    assert p == "VIR AIRBNB PAYMENTS LUXEMBOU"
    assert mt == "prefix"


def test_strips_getaround_ref():
    p, mt = derive_prefix_pattern("VIR GETAROUND GP95000001000001")
    assert p == "VIR GETAROUND"
    assert mt == "prefix"


def test_no_variable_token_falls_back_to_exact():
    p, mt = derive_prefix_pattern("PRLV SEPA EDF")
    assert (p, mt) == ("PRLV SEPA EDF", "exact")
