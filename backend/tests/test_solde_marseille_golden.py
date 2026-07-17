"""
Golden solde Marseille — réconciliation du cumul des transactions avec les
relevés bancaires réels du Crédit Mutuel.

Source de vérité : les exports de relevés `comptes (N).xlsx` téléchargés depuis
le Crédit Mutuel, qui portent un « Solde au JJ/MM/AAAA » officiel. Les valeurs
ci-dessous en sont recopiées (compte 10278 08922 00021394910, COMPTE COURANT
APPARTEMENT MARSEILLE).

Règle métier (formulée par Louis, 2026-07-17) : « le solde doit toujours venir
des transactions… une après l'autre ça somme, puis il doit au final matcher
avec la banque… en aucun cas être importé ». Le cumul part de zéro avant la
première écriture (compte ouvert à l'achat) et doit retomber au centime sur le
relevé à CHAQUE date de contrôle.

Corollaire : toute écriture qui ne passe pas par le compte bancaire (achat
notaire, immobilisations, dépenses payées de la poche de l'associé) doit avoir
sa CONTREPARTIE en compte courant d'associé, pour que le bloc net à zéro et
n'écarte pas le cumul du relevé. C'est ce que fait le bloc d'ouverture
18/01 + 12/03/2024 (+4 915 / -4 915). L'absence de cette contrepartie pour les
850,30 € d'équipement du 11/07/2024 a fait dériver le solde pendant deux ans.

Ce test lit la base de PRODUCTION en LECTURE SEULE (mode=ro) via un engine
dédié — PAS le harnais mémoire (conftest) : il valide l'état RÉEL de la base.
Même motif que test_amortization_evry_golden.py (voir son docstring pour le
pourquoi de l'engine dédié vs le sessionmaker de prod, et la quarantaine).
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
PROD_DB_PATH = REPO_ROOT / "backend" / "database" / "lmnp.db"

MARSEILLE_PROPERTY_ID = 15
TOLERANCE = 0.005  # le centime

# ---------------------------------------------------------------------------
# Vérité bancaire — « Solde au ... » lu dans les relevés Crédit Mutuel.
# (date de contrôle, solde officiel, export d'origine)
#
# La date de contrôle est celle du « Solde au », et le cumul de TOUTES les
# transactions jusqu'à cette date incluse doit l'égaler.
#
# ⚠️ Piège de datation : le relevé liste la date d'OPÉRATION, le CSV de Louis a
# retenu la date de VALEUR — elles diffèrent d'un jour sur les échéances de prêt
# (ex. ECH PRET de mai 2024 : opération 04/05, valeur 05/05, et le « Solde au
# 05/05 » l'inclut). Les dates ci-dessous ont donc été vérifiées une à une : à
# chacune, l'écart observé vaut exactement l'écart attendu (0 avant le
# 11/07/2024, puis les anomalies connues), ce qui prouve qu'aucune n'est prise
# au milieu d'une journée d'opérations à cheval.
#
# Le contrôle du 05/05/2024 est un TÉMOIN : il tombait déjà juste avant
# correction et doit le rester — il garantit que l'historique antérieur au
# 11/07/2024 n'est pas abîmé par les écritures ajoutées.
# ---------------------------------------------------------------------------
RELEVES = [
    # Le bloc notaire (18/01 + 12/03/2024) ne passe par aucun compte bancaire et
    # doit donc nets à zéro : le compte n'est alimenté qu'au 13/03/2024 (APPORT
    # FRAIS DOSSIER, 1er mouvement du relevé). C'est l'invariant « toute écriture
    # hors banque a sa contrepartie », exprimé de la seule façon vérifiable :
    # par le solde, pas par les catégories (elles n'encodent pas bancaire vs non).
    ("2024-03-12", 0.00, "bloc notaire net à zéro — compte pas encore alimenté"),
    ("2024-05-05", 1383.48, "comptes (10).xlsx — Solde au 05/05/2024 (témoin)"),
    ("2024-07-13", 3771.88, "comptes (16).xlsx — Solde au 13/07/2024"),
    ("2024-09-15", 3938.01, "comptes (17).xlsx — Solde au 15/09/2024"),
    ("2025-02-09", 856.22, "comptes (23).xlsx — Solde au 09/02/2025"),
    ("2025-07-01", 1911.25, "comptes (30).xlsx — Solde au 01/07/2025"),
    ("2025-09-02", 1956.17, "comptes (31).xlsx — Solde au 03/09/2025"),
    ("2026-07-16", 3126.88, "comptes (39).xlsx — Solde au 16/07/2026"),
    ("2026-07-17", 2900.21, "solde bancaire live relevé par Louis le 17/07/2026"),
]


@pytest.fixture(scope="module")
def ro_session():
    """Session SQLAlchemy en LECTURE SEULE sur la base de prod."""
    if not PROD_DB_PATH.exists():
        pytest.skip(f"Base de prod introuvable: {PROD_DB_PATH}")
    url = f"sqlite:///file:{PROD_DB_PATH}?mode=ro&uri=true"
    engine = create_engine(url, connect_args={"uri": True})
    ReadOnlySession = sessionmaker(bind=engine)
    session = ReadOnlySession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_prod_db_is_read_only(ro_session):
    """Garde-fou : l'engine ne DOIT PAS pouvoir écrire dans la prod."""
    with pytest.raises(OperationalError):
        ro_session.execute(text("DELETE FROM transactions WHERE id = -1"))
        ro_session.commit()


def _cumul_at(session, date_str):
    """Cumul des quantités (en euros) jusqu'à `date_str` incluse.

    Exclut les lignes parentes éclatées, comme balance_utils.
    """
    row = session.execute(
        text(
            """
            SELECT COALESCE(SUM(quantite), 0) / 100.0
            FROM transactions
            WHERE property_id = :pid
              AND is_split_parent = 0
              AND date <= :d
            """
        ),
        {"pid": MARSEILLE_PROPERTY_ID, "d": date_str},
    ).scalar()
    return round(float(row), 2)


@pytest.mark.parametrize("date_str,solde_banque,source", RELEVES)
def test_cumul_transactions_egale_releve_bancaire(
    ro_session, date_str, solde_banque, source
):
    """Le cumul des transactions doit égaler le relevé bancaire, au centime."""
    cumul = _cumul_at(ro_session, date_str)
    ecart = round(cumul - solde_banque, 2)
    assert abs(ecart) < TOLERANCE, (
        f"Solde Marseille désaccordé au {date_str} : "
        f"cumul={cumul:.2f} € vs banque={solde_banque:.2f} € (écart {ecart:+.2f} €). "
        f"Référence : {source}"
    )


def test_aucun_doublon_au_recouvrement_csv_api(ro_session):
    """Aucune transaction ne doit exister en double entre l'import CSV et la synchro API.

    L'index unique de la base ne porte que sur (account_id, external_id) et les
    lignes CSV n'ont ni l'un ni l'autre : une opération présente à la fois dans
    le dernier export CSV et dans le premier lot Enable Banking passe donc au
    travers. C'est arrivé le 19/01/2026 (VIR INST VIREMENT GESTION DEC25,
    -347,28 €, ids 1787 + 1996).
    """
    doublons = ro_session.execute(
        text(
            """
            SELECT csv.date, csv.quantite / 100.0 AS eur, csv.nom, csv.id, api.id
            FROM transactions csv
            JOIN transactions api
              ON api.property_id = csv.property_id
             AND api.date = csv.date
             AND api.quantite = csv.quantite
             AND api.source = 'api'
            WHERE csv.source = 'csv'
              AND csv.is_split_parent = 0
              AND api.is_split_parent = 0
            """
        )
    ).fetchall()
    assert doublons == [], (
        "Opérations comptées deux fois (une fois par l'export CSV, une fois par "
        f"la synchro bancaire) : {doublons}"
    )


def test_apport_contrepartie_equipement_juillet_2024(ro_session):
    """Les 850,30 € d'équipement payés hors banque ont bien leur contrepartie.

    Régression directe du bug de 2026-07-17. Les 5 achats du 11/07/2024
    (bricorama, electro depot, mr bricolage, boitié clefs) ont été payés par
    Louis de sa poche : ils n'apparaissent pas au relevé. Sans apport en compte
    courant d'associé pour les compenser, le cumul décroche du relevé de
    850,30 € — définitivement, comme il l'a fait pendant deux ans.

    NB : il n'existe volontairement PAS de test générique « toute écriture hors
    banque a sa contrepartie ». Les catégories n'encodent pas le caractère
    bancaire d'une ligne (une immobilisation peut être payée par le compte —
    AMEUBLEA — comme hors compte — bricorama), donc aucun invariant par groupe
    comptable n'est vrai. Le vrai garde-fou générique, ce sont les relevés
    ci-dessus : une écriture hors banque non compensée les fait tomber.
    """
    achats = ro_session.execute(
        text(
            """
            SELECT COALESCE(SUM(quantite), 0) / 100.0
            FROM transactions
            WHERE property_id = :pid
              AND date = '2024-07-11'
              -- noms tels qu'ils sont EN BASE : l'import a nettoyé l'espace
              -- finale de « mr bricolage » présente dans le CSV source.
              AND nom IN ('boitié clefs', 'electro depot', 'mr bricolage',
                          'bricorama')
            """
        ),
        {"pid": MARSEILLE_PROPERTY_ID},
    ).scalar()
    apport = ro_session.execute(
        text(
            """
            SELECT COALESCE(SUM(quantite), 0) / 100.0
            FROM transactions
            WHERE property_id = :pid
              AND date = '2024-07-11'
              AND nom = 'apport compte courant - achats equipement'
            """
        ),
        {"pid": MARSEILLE_PROPERTY_ID},
    ).scalar()
    achats, apport = round(float(achats), 2), round(float(apport), 2)

    assert abs(achats + 850.30) < TOLERANCE, (
        f"Les 5 achats d'équipement du 11/07/2024 ne totalisent plus -850,30 € "
        f"mais {achats:+.2f} € — la contrepartie ci-dessous n'est plus la bonne."
    )
    assert abs(apport + achats) < TOLERANCE, (
        f"Les {achats:+.2f} € d'équipement payés hors banque le 11/07/2024 n'ont "
        f"pas leur contrepartie en compte courant d'associé (apport trouvé : "
        f"{apport:+.2f} €). Sans elle, le solde décroche du relevé de ce montant."
    )


def test_echeancier_pret_colle_aux_prelevements_bancaires(ro_session):
    """L'échéancier du prêt doit correspondre aux mensualités réellement débitées.

    Régression de la modulation MODULIMMO de février 2026 : le prêt « mars » est
    modulable, Louis a baissé sa mensualité de 931,22 € à ~892,48 €, et l'app a
    continué d'appliquer l'ancien tableau pendant 6 mois — amortissant 217,71 €
    de capital de trop et déséquilibrant le bilan 2026 de 231,18 €.

    Le code SUPPOSE que l'échéancier théorique égale les débits bancaires, sans
    jamais réconcilier ni alerter : c'est le bilan qui a fini par le trahir, par
    accident. Ce test ferme cette classe d'écart pour de bon, sur les 3 biens.
    """
    lignes = ro_session.execute(
        text(
            """
            SELECT t.property_id,
                   COALESCE(SUM(t.quantite), 0) / 100.0 AS banque,
                   (SELECT COALESCE(SUM(lp.total), 0) / 100.0
                      FROM loan_payments lp
                     WHERE lp.property_id = t.property_id
                       AND lp.date >= '2026-01-01'
                       AND lp.date <= (SELECT MAX(t2.date) FROM transactions t2
                                        WHERE t2.property_id = t.property_id)) AS echeancier
              FROM transactions t
             WHERE t.property_id IN (15, 25, 26)
               AND t.is_split_parent = 0
               AND t.date >= '2026-01-01'
               AND (t.nom LIKE 'ECH PRET%' OR t.nom LIKE '%PRET IMMOBILIER ECH%')
             GROUP BY t.property_id
            """
        )
    ).fetchall()
    assert lignes, "aucune mensualité de prêt trouvée en 2026 — requête à revoir"
    for property_id, banque, echeancier in lignes:
        ecart = round(abs(float(banque)) - float(echeancier), 2)
        assert abs(ecart) < 0.02, (
            f"Bien {property_id} : l'échéancier ({float(echeancier):.2f} €) ne colle pas aux "
            f"mensualités réellement débitées ({abs(float(banque)):.2f} €) — écart {ecart:+.2f} €. "
            f"Le tableau d'amortissement est périmé (modulation ? renégociation ?) et "
            f"déséquilibrera le bilan d'autant."
        )
