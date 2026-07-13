"""Moteur de classification unifié (lit classification_rules).

Reproduit la sémantique historique de enrichment_service.find_best_mapping :
exact d'abord, sinon prefix/contains sous garde de similarité 70 %, puis
priorité décroissante et longueur de motif décroissante ; règle de bien prime
sur règle globale à égalité ; conflit de longueur max → None.
"""
import re

from backend.database.models import ClassificationRule

MIN_SIMILARITY_RATIO = 0.70


def rule_matches(label: str, pattern: str, match_type: str) -> bool:
    label = label.strip()
    pattern = pattern.strip()
    if not label or not pattern:
        return False
    if match_type == "exact":
        return label == pattern
    ratio = len(pattern) / len(label) if len(label) > 0 else 0.0
    if match_type == "prefix":
        return label.startswith(pattern) and ratio >= MIN_SIMILARITY_RATIO
    if match_type == "contains":
        return pattern in label and ratio >= MIN_SIMILARITY_RATIO
    return False


def _sort_key(rule: ClassificationRule) -> tuple:
    # priorité décroissante, longueur motif décroissante, bien avant global
    is_property = 0 if rule.property_id is not None else 1
    return (-rule.priority, -len(rule.pattern.strip()), is_property)


def find_matching_rule(label: str, rules: list[ClassificationRule]) -> ClassificationRule | None:
    label = label.strip()

    # 1) exact prioritaire absolu
    exact = [r for r in rules if r.match_type == "exact" and rule_matches(label, r.pattern, "exact")]
    if exact:
        exact.sort(key=_sort_key)
        return exact[0]

    # 2) prefix / contains sous garde 70 %
    cands = [r for r in rules
             if r.match_type in ("prefix", "contains") and rule_matches(label, r.pattern, r.match_type)]
    if not cands:
        return None

    cands.sort(key=_sort_key)
    best = cands[0]
    best_len = len(best.pattern.strip())
    # conflit : plusieurs motifs de longueur max égale et même priorité, sans départage bien/global
    top = [r for r in cands
           if len(r.pattern.strip()) == best_len and r.priority == best.priority
           and (r.property_id is None) == (best.property_id is None)]
    if len(top) > 1:
        return None
    return best


_VARIABLE_TOKEN = re.compile(r"^(G-\S+|GP\d+|(?=\S*\d)[A-Z0-9]{8,}|\S*\d{6,}\S*)$")


def derive_prefix_pattern(label: str) -> tuple[str, str]:
    """Propose (pattern, match_type) pour une auto-règle inbox.

    Retire les tokens de fin qui ressemblent à un identifiant variable ;
    le préfixe stable restant devient un motif 'prefix'. Si rien n'est retiré,
    repli sur (label, 'exact').
    """
    tokens = label.strip().split()
    end = len(tokens)
    while end > 1 and _VARIABLE_TOKEN.match(tokens[end - 1]):
        end -= 1
    if end == len(tokens):
        return (label.strip(), "exact")
    return (" ".join(tokens[:end]), "prefix")
