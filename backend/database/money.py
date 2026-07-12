"""
Type SQLAlchemy pour stocker les montants monétaires en centimes (Étape 2 Task 9).

Décision étape 2 : le stockage des montants devient EXACT (fin du drift des
flottants SQLite) sans réécrire les calculs. On stocke des centimes entiers sur
disque, mais l'ORM continue d'exposer des euros (float) aux services, à l'API et
au frontend — le contrat golden (valeurs API en euros) reste inchangé.

Agrégats : SQLAlchemy 2.0 propage AUTOMATIQUEMENT le type de la colonne à
`func.sum(...)` (la fonction `sum` est un `ReturnTypeFromArgs`), donc
`process_result_value` s'applique aussi au résultat d'un `func.sum(colonne
EuroCents)` : les agrégats ressortent en euros sans rien forcer. Aucun service
n'a besoin de `type_=EuroCents()` — les services bilan/compte de résultat sont
inchangés. Le test `test_func_sum_applies_decorator` verrouille ce comportement.
"""

from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator


class EuroCents(TypeDecorator):
    """Stocke des centimes (INTEGER), expose des euros (float) à l'ORM.

    - bind (euros → centimes) : ``int(round(value * 100))``
    - result (centimes → euros) : ``value / 100.0``
    - None-safe dans les deux sens.

    Arrondi : ``round()`` de Python (half-to-even, dit « bancaire »). Pour une
    valeur pile à x.xx5 (ex. 1.005), Python arrondit vers le pair le plus
    proche du fait de la représentation binaire — cas marginal, absent des
    données réelles (vérifié par le script de migration : SUM préservée).
    """

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):  # euros → centimes
        if value is None:
            return None
        return int(round(float(value) * 100))

    def process_result_value(self, value, dialect):  # centimes → euros
        if value is None:
            return None
        return value / 100.0
