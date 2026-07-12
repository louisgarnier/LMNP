"""
Tests du type `EuroCents` (Étape 2 Task 9) : stockage en centimes entiers,
exposition en euros (float) à l'ORM.

Harnais ISOLÉ : chaque test crée son propre moteur SQLite en mémoire et une
petite table dédiée. Aucun accès à la base de production (pas de SessionLocal,
pas de get_db()).

Points couverts :
- round-trip euros → centimes → euros (valeur stockée entière vérifiée en SQL brut)
- None-safe (lecture et écriture)
- valeurs négatives
- arrondi à >2 décimales (round() Python, half-to-even « bancaire » documenté)
- REGRESSION : `func.sum()` applique bien le décorateur (les services bilan/CR
  s'appuient sur `func.sum(col)` et DOIVENT recevoir des euros, pas des centimes).
"""

import pytest
from sqlalchemy import Column, Integer, create_engine, func, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.money import EuroCents

Base = declarative_base()


class _Money(Base):
    __tablename__ = "money_probe"
    id = Column(Integer, primary_key=True)
    amount = Column(EuroCents, nullable=True)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()


def _raw_stored(session, row_id):
    """Lit la valeur BRUTE en base (sans passer par le décorateur)."""
    return session.execute(
        text("SELECT amount FROM money_probe WHERE id = :i"), {"i": row_id}
    ).scalar()


def test_round_trip_two_decimals(session):
    """1234.56 € est stocké comme l'entier 123456 (centimes) et relu 1234.56 €."""
    row = _Money(amount=1234.56)
    session.add(row)
    session.commit()
    assert _raw_stored(session, row.id) == 123456  # entier centimes en base
    assert isinstance(_raw_stored(session, row.id), int)
    session.expire_all()
    assert session.get(_Money, row.id).amount == 1234.56  # euros float côté ORM


def test_none_is_preserved(session):
    row = _Money(amount=None)
    session.add(row)
    session.commit()
    assert _raw_stored(session, row.id) is None
    session.expire_all()
    assert session.get(_Money, row.id).amount is None


def test_negative_value(session):
    row = _Money(amount=-473.21)
    session.add(row)
    session.commit()
    assert _raw_stored(session, row.id) == -47321
    session.expire_all()
    assert session.get(_Money, row.id).amount == -473.21


def test_more_than_two_decimals_rounds_to_nearest_cent(session):
    """Une valeur dérivée à >2 décimales est arrondie au centime le plus proche.

    -643.7569444... € → -643.7569444*100 = -64375.69... → round → -64376 centimes
    → relu -643.76 €. (C'est exactement pour cette raison que la colonne
    amortization_results.amount reste en Float : voir le rapport Task 9.)
    """
    row = _Money(amount=-643.7569444444443)
    session.add(row)
    session.commit()
    assert _raw_stored(session, row.id) == -64376
    session.expire_all()
    assert session.get(_Money, row.id).amount == -643.76


def test_bankers_rounding_half_to_even_documented(session):
    """`round()` Python est half-to-even ; combiné à la représentation binaire.

    Cas documentés (déterministes sur CPython), qui montrent que l'issue dépend
    À LA FOIS de la représentation binaire ET du half-to-even de round() :
      - 0.125 € : 0.125*100 == 12.5 exactement → round half-to-even → 12 → 0.12 €
      - 2.675 € : 2.675*100 == 267.5 (le flottant arrondit 2.675 vers le haut)
        → round half-to-even → 268 → 2.68 € (et NON 2.67 : contre-intuitif, d'où
        le test qui fige le comportement réel).
    Aucune valeur réelle de production n'est à ±0.005 d'un centime (le script de
    migration le garantit via la préservation des SUM par colonne).
    """
    a = _Money(amount=0.125)
    b = _Money(amount=2.675)
    session.add_all([a, b])
    session.commit()
    assert _raw_stored(session, a.id) == 12
    assert _raw_stored(session, b.id) == 268


def test_func_sum_applies_decorator(session):
    """REGRESSION load-bearing : func.sum(col) DOIT renvoyer des euros.

    Les services bilan/compte de résultat agrègent les montants via
    `func.sum(Transaction.quantite)` / `func.sum(LoanPayment.capital)`. Si le
    décorateur ne s'appliquait pas à l'agrégat, l'API renverrait des centimes
    bruts (×100) et casserait le golden. On fige donc ce comportement.
    """
    session.add_all([_Money(amount=1234.56), _Money(amount=10.00), _Money(amount=5.55)])
    session.commit()
    total = session.query(func.sum(_Money.amount)).scalar()
    assert total == pytest.approx(1250.11, abs=1e-9)
