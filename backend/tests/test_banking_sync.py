from datetime import date, timedelta
from backend.database.models import Property, BankAccount, Transaction
from backend.api.services import banking_service as bs


def _seed(db_session):
    prop = Property(name="EB-Sync"); db_session.add(prop); db_session.flush()
    acc = BankAccount(property_id=prop.id, eb_account_uid="mock-acc-1", bank_name="Mock", currency="EUR")
    db_session.add(acc); db_session.commit()
    return prop, acc


def test_sync_inserts_booked_ignores_pending(db_session):
    prop, acc = _seed(db_session)
    res = bs.sync_account(db_session, acc)
    assert res["errors"] == []                # contrat de retour : pas d'erreur sur une synchro réussie
    assert res["inserted"] >= 1
    txs = db_session.query(Transaction).filter(Transaction.property_id == prop.id).all()
    noms = {t.nom for t in txs}
    assert "LOYER MOCK" in noms
    assert "PENDING MOCK" not in noms          # pending filtré
    assert all(t.source == "api" for t in txs)


def test_sync_persists_last_sync_at(db_session):
    prop, acc = _seed(db_session)
    assert acc.last_sync_at is None
    bs.sync_account(db_session, acc)
    db_session.refresh(acc)
    assert acc.last_sync_at is not None        # incrémental live : doit survivre au commit


def test_sync_account_failure_isolated(db_session, monkeypatch):
    prop, acc = _seed(db_session)

    def _boom(bank_account, since):
        raise RuntimeError("panne API simulée")

    monkeypatch.setattr(bs, "_fetch_raw", _boom)
    res = bs.sync_account(db_session, acc)     # ne doit PAS lever
    assert res["inserted"] == 0
    assert res["errors"] != []
    db_session.refresh(acc)
    assert acc.last_sync_at is None            # rien persisté sur échec


def test_sync_is_incremental_no_dup_on_second_run(db_session):
    prop, acc = _seed(db_session)
    bs.sync_account(db_session, acc)
    n1 = db_session.query(Transaction).filter(Transaction.property_id == prop.id).count()
    bs.sync_account(db_session, acc)           # 2e passe
    n2 = db_session.query(Transaction).filter(Transaction.property_id == prop.id).count()
    assert n1 == n2                            # dédoublonnage (account_id, external_id)


def test_sync_fx_shared_id_scoped_by_account(db_session):
    prop, acc1 = _seed(db_session)
    acc2 = BankAccount(property_id=prop.id, eb_account_uid="mock-acc-2", bank_name="Mock", currency="EUR")
    # note : un compte par bien en usage réel ; ici 2 comptes pour tester le scoping FX
    db_session.add(acc2); db_session.commit()
    bs.sync_account(db_session, acc1)
    bs.sync_account(db_session, acc2)
    fx = db_session.query(Transaction).filter(Transaction.nom == "FX MOCK").all()
    assert len(fx) == 2                        # même external_id mais 2 account_id → 2 lignes distinctes


def test_disconnect_after_sync_preserves_transactions(db_session):
    """Finding 1 : connecter → synchroniser → déconnecter ne doit PAS violer la FK
    transactions.account_id → bank_accounts.id. Les transactions doivent survivre
    (account_id devient NULL), pas d'IntegrityError."""
    prop, acc = _seed(db_session)
    res = bs.sync_account(db_session, acc)
    assert res["errors"] == []
    n_before = db_session.query(Transaction).filter(Transaction.property_id == prop.id).count()
    assert n_before >= 1

    ok = bs.disconnect(db_session, acc.id)      # ne doit lever aucune IntegrityError
    assert ok is True

    txs = db_session.query(Transaction).filter(Transaction.property_id == prop.id).all()
    assert len(txs) == n_before                 # aucune transaction perdue
    assert all(t.account_id is None for t in txs)  # FK détachée, pas supprimée


def _capture(vu):
    """Intercepte _fetch_raw pour observer la fenêtre demandée, et rend une liste VIDE.

    ⚠️ Ne PAS écrire `lambda ba, since: vu.setdefault("since", since) or []` :
    `setdefault` renvoie la date, et `date or []` vaut la date (truthy). La lambda
    rendait donc une date là où sync_account attend une liste → « 'datetime.date'
    object is not iterable », exception avalée par le try/except de sync_account,
    et le test passait quand même sans jamais exercer l'ingestion.
    """
    def _fake(bank_account, since):
        vu["since"] = since
        return []
    return _fake

# ---------------------------------------------------------------------------
# Fenêtre de synchro : ancrée sur les DONNÉES, pas sur l'horloge (2026-07-17)
# ---------------------------------------------------------------------------
# Avant : `since = bank_account.last_sync_at`. Deux conséquences graves —
#  1. supprimer des transactions ne les fait JAMAIS revenir : la synchro repart
#     de la dernière synchro, pas du dernier trou ;
#  2. une synchro à moitié échouée avance quand même last_sync_at → les
#     transactions manquantes sont perdues pour toujours.
# Idée de Louis : la fenêtre doit se caler sur la dernière transaction EN BASE.

def test_un_trou_AU_MILIEU_est_rebouche(db_session, monkeypatch):
    """LE cas qui a fait échouer le test du 2026-07-17.

    Se caler sur « la dernière transaction en base » ne marche que si le trou est
    à la FIN. Ici juin est supprimé mais une transaction du 17/07 subsiste : la
    fenêtre repartirait du 17/07 et passerait par-dessus le trou. Seule une
    fenêtre GLISSANTE rebouche un trou où qu'il soit.
    """
    prop, acc = _seed(db_session)
    for d, ext in [(date(2026, 5, 12), "ext-mai"), (date.today(), "ext-auj")]:
        db_session.add(Transaction(property_id=prop.id, account_id=acc.id, date=d, quantite=100.0,
                                   nom="TX", solde=0.0, source="api", external_id=ext))
    db_session.commit()

    vu = {}
    monkeypatch.setattr(bs, "_fetch_raw", _capture(vu))
    bs.sync_account(db_session, acc)
    assert vu["since"] <= date.today() - timedelta(days=80), (
        f"la fenêtre doit couvrir les dernières semaines pour reboucher un trou, "
        f"pas repartir de la dernière transaction ({vu['since']})"
    )


def test_since_ignore_last_sync_at_si_des_transactions_ont_ete_supprimees(db_session, monkeypatch):
    """Le cœur du correctif : last_sync_at ne doit plus dicter la fenêtre.

    Scénario réel : last_sync_at est à aujourd'hui, mais on a supprimé juin et
    juillet. L'ancien code aurait redemandé « depuis aujourd'hui » et les
    transactions supprimées ne seraient jamais revenues.
    """
    from datetime import datetime
    prop, acc = _seed(db_session)
    acc.last_sync_at = datetime(2026, 7, 17, 6, 33)
    db_session.add(Transaction(property_id=prop.id, account_id=acc.id, date=date(2026, 5, 12),
                               quantite=100.0, nom="ANCIENNE", solde=0.0, source="api",
                               external_id="ext-mai"))
    db_session.commit()

    vu = {}
    monkeypatch.setattr(bs, "_fetch_raw", _capture(vu))
    bs.sync_account(db_session, acc)
    assert vu["since"] <= date.today() - timedelta(days=80), (
        f"last_sync_at (17/07) ne doit plus dicter la fenêtre — reçu {vu['since']}"
    )


def test_since_ne_remonte_JAMAIS_avant_l_historique_csv(db_session, monkeypatch):
    """Garde-fou anti-catastrophe : ne pas réimporter par-dessus le CSV.

    Les lignes CSV n'ont ni account_id ni external_id : l'anti-doublon ne les
    voit pas (c'est le bug du 19/01/2026, 347,28 € comptés deux fois). Si un
    compte n'a aucune transaction API, se caler sur « rien » ferait rechercher
    depuis 2020 et dupliquerait TOUT l'historique CSV. On se rabat donc sur la
    dernière transaction du BIEN, quelle qu'en soit la source.
    """
    prop, acc = _seed(db_session)
    # CSV RÉCENT (il y a 10 jours) : la fenêtre glissante de 90 jours le
    # recouvrirait et redemanderait à la banque des opérations déjà importées
    # depuis le fichier — sans external_id pour les reconnaître.
    csv_recent = date.today() - timedelta(days=10)
    db_session.add(Transaction(property_id=prop.id, account_id=None, date=csv_recent,
                               quantite=100.0, nom="HISTORIQUE CSV", solde=0.0, source="csv"))
    db_session.commit()

    vu = {}
    monkeypatch.setattr(bs, "_fetch_raw", _capture(vu))
    bs.sync_account(db_session, acc)
    assert vu["since"] == csv_recent, (
        f"la fenêtre doit être plafonnée au dernier import CSV ({csv_recent}), "
        f"reçu {vu['since']} — les lignes CSV n'ont pas d'external_id, l'anti-doublon "
        f"est aveugle sur elles et on dupliquerait tout l'historique importé"
    )


def test_since_est_None_sur_un_compte_vraiment_neuf(db_session, monkeypatch):
    """Aucune donnée nulle part → première synchro, on prend tout l'historique."""
    prop, acc = _seed(db_session)
    vu = {}
    monkeypatch.setattr(bs, "_fetch_raw", _capture(vu))
    bs.sync_account(db_session, acc)
    assert vu.get("since") is None
