from backend.database.models import ClassificationRule
from backend.api.services.classification_engine import rule_matches, find_matching_rule


def _rule(pattern, match_type, category_id=1, property_id=25, priority=0):
    return ClassificationRule(pattern=pattern, match_type=match_type,
                              category_id=category_id, property_id=property_id,
                              priority=priority, source="migrated")


def test_exact_wins_even_if_short():
    assert rule_matches("VIR STRIPE", "VIR STRIPE", "exact")
    assert not rule_matches("VIR STRIPE PAIEMENT", "VIR STRIPE", "exact")


def test_prefix_requires_70pct():
    # motif 10 / libellé 60 ≈ 16.7 % → rejeté
    long_label = "VIR AIRBNB PAYMENTS LUXEMBOU G-ZE7ROGLGC5S4PWE5OOQQ6HLF45V2S"
    assert not rule_matches(long_label, "VIR AIRBNB", "prefix")   # 10/60 trop court
    # motif 28 / libellé 31 ≈ 90.3 % → accepté
    assert rule_matches("VIR AIRBNB PAYMENTS LUXEMBOU X1", "VIR AIRBNB PAYMENTS LUXEMBOU", "prefix")


def test_contains_requires_70pct():
    assert rule_matches("XX PRLV SEPA EDF", "PRLV SEPA EDF", "contains")   # 13/16 = 81.25 %
    assert not rule_matches("PRLV SEPA EDF FACTURE ELECTRICITE LONGUE", "EDF", "contains")


def test_longest_pattern_wins():
    rules = [_rule("VIR", "prefix"), _rule("VIR AIRBNB PAYMENTS LUXEMBOU", "prefix", category_id=2)]
    got = find_matching_rule("VIR AIRBNB PAYMENTS LUXEMBOU X1", rules)
    assert got.category_id == 2


def test_tie_on_max_length_returns_none():
    # deux motifs 'contains' distincts, longueur égale, tous deux présents et
    # ≥70 % du libellé, même priorité et même portée → conflit → None
    label = "ABCDE"
    rules = [_rule("ABCD", "contains", category_id=2),
             _rule("BCDE", "contains", category_id=3)]
    assert find_matching_rule(label, rules) is None


def test_property_rule_beats_global_on_tie():
    prop = _rule("EDF", "exact", category_id=5, property_id=25)
    glob = _rule("EDF", "exact", category_id=6, property_id=None)
    assert find_matching_rule("EDF", [glob, prop]).category_id == 5


def test_strict_ratio_flag_bypasses_similarity_guard():
    # motif 22 / libellé 48 ≈ 0.46 → sous la garde 70 % : rejeté quand strict_ratio=True,
    # accepté quand strict_ratio=False (bypass historique PRLV SEPA / VIR STRIPE).
    label = "PRLV SEPA FREE TELECOM FREE HAUTDEBIT 1350216259"
    pattern = "PRLV SEPA FREE TELECOM"
    strict_rule = ClassificationRule(pattern=pattern, match_type="prefix", category_id=1,
                                     property_id=25, priority=0, source="migrated",
                                     strict_ratio=True)
    lenient_rule = ClassificationRule(pattern=pattern, match_type="prefix", category_id=2,
                                      property_id=25, priority=0, source="migrated",
                                      strict_ratio=False)
    assert find_matching_rule(label, [strict_rule]) is None
    got = find_matching_rule(label, [lenient_rule])
    assert got is not None and got.category_id == 2
