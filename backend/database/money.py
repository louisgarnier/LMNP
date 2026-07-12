"""
Type SQLAlchemy pour stocker les montants monétaires en centimes (Étape 2 Task 9).

Décision étape 2 : le stockage des montants devient EXACT (fin du drift des
flottants SQLite) sans réécrire les calculs. On stocke des centimes entiers sur
disque, mais l'ORM continue d'exposer des euros (float) aux services, à l'API et
au frontend — le contrat golden (valeurs API en euros) reste inchangé.

⚠️ Limite importante (documentée) : un `TypeDecorator` n'applique
`process_result_value` QUE lors de la lecture directe d'une colonne mappée
(`row.quantite`). Il NE s'applique PAS automatiquement au résultat d'une
fonction d'agrégation SQL comme `func.sum(Transaction.quantite)` : SQLAlchemy
ne propage pas toujours le type de la colonne à l'expression `sum()`. Pour que
les agrégats restent en euros, on force le type de retour côté requête avec
`func.sum(col, type_=EuroCents())` (ou équivalent) là où c'est nécessaire — voir
les services bilan/compte de résultat.
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
