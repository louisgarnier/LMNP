"""
SQLAlchemy models for the LMNP application.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text,
    ForeignKey, Boolean, Index, UniqueConstraint, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from .money import EuroCents  # Étape 2 Task 9 : montants stockés en centimes (INTEGER)

Base = declarative_base()


class Property(Base):
    """Property (appartement) model for multi-property support."""
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)  # Nom de la propriété (ex: "Appartement 1")
    address = Column(String(500), nullable=True)  # Adresse de la propriété
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    transactions = relationship("Transaction", back_populates="property", cascade="all, delete-orphan")
    mappings = relationship("Mapping", back_populates="property", cascade="all, delete-orphan")
    file_imports = relationship("FileImport", back_populates="property", cascade="all, delete-orphan")
    amortization_types = relationship("AmortizationType", back_populates="property", cascade="all, delete-orphan")
    loan_configs = relationship("LoanConfig", back_populates="property", cascade="all, delete-orphan")
    loan_payments = relationship("LoanPayment", back_populates="property", cascade="all, delete-orphan")
    # Compte de résultat
    compte_resultat_mappings = relationship("CompteResultatMapping", back_populates="property", cascade="all, delete-orphan")
    compte_resultat_config = relationship("CompteResultatConfig", back_populates="property", cascade="all, delete-orphan")
    compte_resultat_overrides = relationship("CompteResultatOverride", back_populates="property", cascade="all, delete-orphan")
    # Bilan
    bilan_mappings = relationship("BilanMapping", back_populates="property", cascade="all, delete-orphan")
    bilan_config = relationship("BilanConfig", back_populates="property", cascade="all, delete-orphan")
    # Pivot
    pivot_configs = relationship("PivotConfig", back_populates="property", cascade="all, delete-orphan")
    # Pro Rata & Forecast
    prorata_settings = relationship("ProRataSettings", back_populates="property", uselist=False, cascade="all, delete-orphan")
    annual_forecast_configs = relationship("AnnualForecastConfig", back_populates="property", cascade="all, delete-orphan")
    # Étape 4 Task 1 : comptes bancaires (peuplés à l'étape 5 Enable Banking)
    bank_accounts = relationship("BankAccount", back_populates="property", cascade="all, delete-orphan")

    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_property_name', 'name', unique=True),
    )


class Transaction(Base):
    """Raw transactions aggregated from CSV files."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    quantite = Column(EuroCents, nullable=False)  # Montant de la transaction (centimes en base, euros à l'ORM)
    nom = Column(String(500), nullable=False, index=True)  # Description/nom de la transaction
    solde = Column(EuroCents, nullable=False)  # Solde après transaction (centimes en base, euros à l'ORM)
    source_file = Column(String(255))  # Fichier source d'origine
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)  # Référentiel category (Étape 2 Task 3)
    # Étape 4 Task 1 : champs d'ingestion (Enable Banking étape 5, imports manuels)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True, index=True)
    external_id = Column(String(255), nullable=True)
    source = Column(String(10), nullable=False, default="csv")  # csv | api | manual
    parent_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, index=True)
    is_split_parent = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    property = relationship("Property", back_populates="transactions")
    category = relationship("Category")

    # Index pour détection de doublons et recherche par property_id
    __table_args__ = (
        Index('idx_transaction_unique', 'date', 'quantite', 'nom'),
        Index('idx_transactions_property_id', 'property_id'),
        Index('idx_tx_account_external_unique', 'account_id', 'external_id',
              unique=True, sqlite_where=text('external_id IS NOT NULL')),
    )


class BankAccount(Base):
    """Compte bancaire d'un bien. Peuplé à l'étape 5 (Enable Banking) ; vide en étape 4."""
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_name = Column(String(255))
    iban_masked = Column(String(64))
    eb_account_uid = Column(String(255), nullable=True)
    eb_session_id = Column(String(255), nullable=True)
    session_valid_until = Column(Date, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_tx_cursor = Column(String(255), nullable=True)

    property = relationship("Property", back_populates="bank_accounts")


# Étape 2 Task 8 : la classe EnrichedTransaction (table enriched_transactions) a
# été supprimée. La classification vit désormais dans transactions.category_id
# (référentiel category/category_groups). La table physique est droppée par la
# migration drop_enriched_transactions.py.


class Mapping(Base):
    """Mapping rules for transaction names to categories.

    Étape 3 Task 9 : le moteur vivant (routes/services API) ne lit/écrit plus
    cette classe — retirée de `enrichment_service`/`mapping_obligatoire_service`
    et des routes (`mappings.py`, `enrichment.py`, supprimées). La classe ORM
    est VOLONTAIREMENT conservée (déviation du brief Task 9 §C.5) car
    `backend/scripts/migrate_mappings_to_rules.py` (script étape-3 protégé,
    jamais à supprimer) et son test associé (`test_migrate_mappings_to_rules.py`,
    live) en dépendent directement pour lire la table `mappings` comme source
    de migration. La table physique n'est pas droppée (différé Task 10) ; ce
    choix garde le modèle ORM cohérent avec elle tant qu'un consommateur vivant
    existe.
    """
    __tablename__ = "mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    nom = Column(String(500), nullable=False, index=True)  # Nom/pattern de transaction (plus unique, car isolé par property_id)
    level_1 = Column(String(100), nullable=False)
    level_2 = Column(String(100), nullable=False)
    level_3 = Column(String(100))
    is_prefix_match = Column(Boolean, default=True)  # Si True, match par préfixe
    priority = Column(Integer, default=0)  # Priorité pour résolution de conflits
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="mappings")
    
    # Index pour recherche par property_id et unicité par property
    __table_args__ = (
        Index('idx_mappings_property_id', 'property_id'),
        Index('idx_mappings_property_nom_unique', 'property_id', 'nom', unique=True),  # Unique par propriété
    )


class ClassificationRule(Base):
    """Règle de classification unifiée (remplace mappings + allowed_mappings + Excel + hardcodé)."""
    __tablename__ = "classification_rules"

    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(String(500), nullable=False, index=True)
    match_type = Column(String(10), nullable=False)  # exact | prefix | contains
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"),
                         nullable=True, index=True)  # NULL = règle globale
    priority = Column(Integer, nullable=False, default=0)
    source = Column(String(20), nullable=False, default="manual")  # migrated | manual | auto_from_inbox
    strict_ratio = Column(Boolean, nullable=False, default=True)  # False = garde de similarité 70 % désactivée (prélèvements récurrents)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category")

    __table_args__ = (
        Index("idx_rules_property_id", "property_id"),
    )


class FileImport(Base):
    """Track imported CSV files to prevent duplicate processing."""
    __tablename__ = "file_imports"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False, index=True)  # Plus unique globalement, unique par property_id
    imported_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    imported_count = Column(Integer, default=0)  # Nombre de transactions importées
    duplicates_count = Column(Integer, default=0)  # Nombre de doublons détectés
    errors_count = Column(Integer, default=0)  # Nombre d'erreurs
    period_start = Column(Date)  # Date de début des transactions
    period_end = Column(Date)  # Date de fin des transactions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="file_imports")
    
    # Index pour recherches et unicité par property
    __table_args__ = (
        Index('idx_file_imports_property_id', 'property_id'),
        Index('idx_file_imports_filename', 'filename'),
        Index('idx_file_imports_imported_at', 'imported_at'),
        Index('idx_file_imports_property_filename_unique', 'property_id', 'filename', unique=True),  # Unique par propriété
    )


class PivotConfig(Base):
    """Saved pivot table configurations."""
    __tablename__ = "pivot_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)  # Nom du tableau
    config = Column(Text, nullable=False)  # Configuration JSON (rows, columns, data, filters)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation avec Property
    property = relationship("Property", back_populates="pivot_configs")
    
    # Index pour recherches
    __table_args__ = (
        Index('idx_pivot_configs_name', 'name'),
        Index('idx_pivot_configs_property_id', 'property_id'),
    )


class CategoryGroup(Base):
    """Groupe de catégories (ex-« Level 2 »). nature = ex-« Level 3 », enum fermé."""
    __tablename__ = "category_groups"
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(100), nullable=False, unique=True)
    nature = Column(String(30), nullable=False)  # produits|charges_deductibles|emprunt|actif|passif
    created_at = Column(DateTime, default=datetime.utcnow)
    categories = relationship("Category", back_populates="group")


class Category(Base):
    """Catégorie de classification (ex-« Level 1 »). Référentiel GLOBAL (pas de property_id)."""
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(100), nullable=False)
    group_id = Column(Integer, ForeignKey("category_groups.id"), nullable=False)
    is_custom = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("CategoryGroup", back_populates="categories")
    __table_args__ = (UniqueConstraint("label", "group_id", name="uq_category_label_group"),)


class AmortizationType(Base):
    """Types d'amortissement configurables pour les immobilisations."""
    __tablename__ = "amortization_types"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)  # Nom du type (ex: "Immobilisation terrain")
    level_2_value = Column(String(100), nullable=False, index=True)  # Valeur level_2 à considérer (ex: "ammortissements")
    level_1_values = Column(Text, nullable=False, default="[]")  # JSON array des valeurs level_1 mappées
    start_date = Column(Date, nullable=True)  # Date de début d'amortissement (override, nullable)
    duration = Column(Float, nullable=False, default=0.0)  # Durée d'amortissement en années (0 = non amortissable)
    annual_amount = Column(EuroCents, nullable=True)  # Annuité d'amortissement (override, nullable) — centimes en base
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="amortization_types")
    
    # Index pour recherches fréquentes et recherche par property_id
    __table_args__ = (
        Index('idx_amortization_type_level_2', 'level_2_value'),
        Index('idx_amortization_types_property_id', 'property_id'),
    )


class AmortizationResult(Base):
    """Résultats d'amortissement par transaction, année et catégorie."""
    __tablename__ = "amortization_results"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)  # Année d'amortissement (ex: 2021, 2022)
    category = Column(String(255), nullable=False, index=True)  # Nom du type d'amortissement (ex: "Immobilisation terrain")
    # Étape 2 Task 9 : cette colonne reste en Float (PAS EuroCents) — c'est le
    # SEUL montant NON converti en centimes. L'amortissement linéaire produit des
    # valeurs dérivées à décimales infinies (ex. total/durée = -643.7569444...).
    # Les arrondir au centime au stockage ferait dériver les lignes cumulées du
    # bilan jusqu'à ~0,06 € (mesuré), au-delà de la tolérance golden de 0,01 €.
    # On conserve donc la précision sub-centime ici. Voir .superpowers/sdd/task-9-report.md.
    amount = Column(Float, nullable=False)  # Montant amorti pour cette année (négatif) — Float délibéré (valeur dérivée)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    transaction = relationship("Transaction", backref="amortization_results")
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_amortization_result_year_category', 'year', 'category'),
        Index('idx_amortization_result_transaction', 'transaction_id'),
    )


class LoanPayment(Base):
    """Mensualités de crédit (capital, intérêt, assurance)."""
    __tablename__ = "loan_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # Date de la mensualité (01/01/année)
    capital = Column(EuroCents, nullable=False)  # Montant du capital remboursé (centimes en base)
    interest = Column(EuroCents, nullable=False)  # Montant des intérêts (centimes en base)
    insurance = Column(EuroCents, nullable=False)  # Montant de l'assurance crédit (centimes en base)
    total = Column(EuroCents, nullable=False)  # Total de la mensualité (centimes en base)
    loan_name = Column(String(255), nullable=False, index=True)  # Nom du prêt (ex: "Prêt principal")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="loan_payments")
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_loan_payment_date', 'date'),
        Index('idx_loan_payment_loan_name', 'loan_name'),
        Index('idx_loan_payment_loan_name_date', 'loan_name', 'date', unique=True),
        Index('idx_loan_payments_property_id', 'property_id'),
    )


class LoanConfig(Base):
    """Configurations de crédit (multi-crédits possibles)."""
    __tablename__ = "loan_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)  # Nom du crédit (ex: "Prêt principal", "Prêt construction")
    credit_amount = Column(EuroCents, nullable=False)  # Montant du crédit accordé (centimes en base, euros à l'ORM)
    interest_rate = Column(Float, nullable=False)  # Taux fixe actuel hors assurance en %
    duration_years = Column(Integer, nullable=False)  # Durée de l'emprunt en années
    initial_deferral_months = Column(Integer, default=0, nullable=False)  # Décalage initial en mois
    loan_start_date = Column(Date, nullable=True)  # Date d'emprunt
    loan_end_date = Column(Date, nullable=True)  # Date de fin prévisionnelle
    monthly_insurance = Column(EuroCents, default=0.0, nullable=False)  # Assurance mensuelle (centimes en base, euros à l'ORM)
    simulation_months = Column(Text, nullable=True)  # JSON array des mensualités personnalisées (ex: "[1, 50, 100, 150, 200]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="loan_configs")
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_loan_configs_property_id', 'property_id'),
        Index('idx_loan_config_property_name', 'property_id', 'name', unique=True),  # Unique par propriété
    )


class CompteResultatMapping(Base):
    """Mappings pour le compte de résultat (level_1 → catégories comptables)."""
    __tablename__ = "compte_resultat_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    category_name = Column(String(255), nullable=False, index=True)  # Nom de la catégorie comptable (ex: "Loyers hors charge encaissés")
    type = Column(String(50), nullable=True)  # Type: "Produits d'exploitation" ou "Charges d'exploitation" (pour les catégories personnalisées)
    # NB étape 2 Task 8 : ex-colonne level_1_values retirée du modèle (remplacée
    # par la liaison category_links). La colonne SQLite reste physiquement (morte).
    line_code = Column(String(30), nullable=True)  # Code de ligne stable (ex: 'AMORT', 'COUT_FINANCEMENT') — étape 2 Task 5. NULL pour les lignes ordinaires.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    property = relationship("Property", back_populates="compte_resultat_mappings")
    # Liaison vers le référentiel category (étape 2 Task 5) : source de LECTURE
    # du calcul CR, remplace level_1_values JSON. Cascade ORM pour que la
    # suppression d'un mapping efface ses liaisons même si le PRAGMA foreign_keys
    # de SQLite n'est pas actif sur la connexion.
    category_links = relationship(
        "CompteResultatMappingCategory",
        back_populates="mapping",
        cascade="all, delete-orphan",
    )

    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_compte_resultat_mapping_category', 'category_name'),
        Index('idx_compte_resultat_mapping_property_id', 'property_id'),
    )


class CompteResultatMappingCategory(Base):
    """Liaison ligne CR ↔ catégorie du référentiel (étape 2 Task 5).

    Remplace `CompteResultatMapping.level_1_values` (JSON de labels) comme
    source de lecture du calcul du compte de résultat. Une ligne par
    (mapping, category). La sérialisation API continue d'exposer des labels
    (reconstruits depuis `categories.label`), byte-identiques à l'ancien JSON.
    """
    __tablename__ = "compte_resultat_mapping_categories"

    id = Column(Integer, primary_key=True, index=True)
    mapping_id = Column(Integer, ForeignKey("compte_resultat_mappings.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    mapping = relationship("CompteResultatMapping", back_populates="category_links")
    category = relationship("Category")

    __table_args__ = (
        UniqueConstraint("mapping_id", "category_id", name="uq_cr_mapping_category"),
    )


class CompteResultatConfig(Base):
    """Configuration globale pour le compte de résultat (filtre Level 3)."""
    __tablename__ = "compte_resultat_config"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    level_3_values = Column(Text, nullable=False, default="[]")  # JSON array des level_3 sélectionnés (ex: '["VALEUR1", "VALEUR2"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="compte_resultat_config")
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_compte_resultat_config_property_id', 'property_id'),
    )


class CompteResultatOverride(Base):
    """Override manuel du résultat de l'exercice par année."""
    __tablename__ = "compte_resultat_override"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)  # Année du compte de résultat (unique par property_id)
    override_value = Column(EuroCents, nullable=False)  # Valeur override du résultat de l'exercice (centimes en base)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="compte_resultat_overrides")
    
    # Index pour recherches fréquentes - contrainte unique (year, property_id)
    __table_args__ = (
        Index('idx_compte_resultat_override_year', 'year'),
        Index('idx_compte_resultat_override_property_id', 'property_id'),
        Index('idx_compte_resultat_override_year_property', 'year', 'property_id', unique=True),
    )


class BilanMapping(Base):
    """Mappings pour le bilan (level_1 → catégories comptables)."""
    __tablename__ = "bilan_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    category_name = Column(String(255), nullable=False, index=True)  # Nom de la catégorie comptable (niveau C)
    type = Column(String(50), nullable=False, index=True)  # Type: "ACTIF" ou "PASSIF"
    sub_category = Column(String(100), nullable=False, index=True)  # Sous-catégorie (niveau B)
    # NB étape 2 Task 8 : ex-colonnes level_1_values (remplacée par category_links)
    # et special_source (remplacée par line_code) retirées du modèle. Les colonnes
    # SQLite restent physiquement (mortes) — un DROP COLUMN SQLite exige un rebuild.
    is_special = Column(Boolean, nullable=False, default=False)  # Indique si c'est une catégorie spéciale
    line_code = Column(String(30), nullable=True)  # Code de ligne spéciale stable (ex: 'AMORT_CUMULES', 'COMPTE_BANCAIRE', 'RESULTAT_EXERCICE', 'REPORT_A_NOUVEAU', 'CAPITAL_RESTANT_DU') — étape 2 Task 6/8 : unique source de dispatch. NULL pour les lignes normales.
    compte_resultat_view_id = Column(Integer, nullable=True)  # Pour catégorie "Résultat de l'exercice" (ForeignKey vers compte_resultat_mapping_views.id - table à créer si nécessaire)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relation avec Property
    property = relationship("Property", back_populates="bilan_mappings")
    # Liaison vers le référentiel category (étape 2 Task 6) : source de LECTURE
    # du calcul des lignes normales du bilan, remplace level_1_values JSON.
    # Cascade ORM pour effacer les liaisons à la suppression d'un mapping même
    # si le PRAGMA foreign_keys de SQLite n'est pas actif sur la connexion.
    category_links = relationship(
        "BilanMappingCategory",
        back_populates="mapping",
        cascade="all, delete-orphan",
    )

    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_bilan_mapping_category', 'category_name'),
        Index('idx_bilan_mapping_type', 'type'),
        Index('idx_bilan_mapping_sub_category', 'sub_category'),
        Index('idx_bilan_mapping_type_sub_category', 'type', 'sub_category'),
        Index('idx_bilan_mapping_property_id', 'property_id'),
    )


class BilanMappingCategory(Base):
    """Liaison ligne bilan ↔ catégorie du référentiel (étape 2 Task 6).

    Remplace `BilanMapping.level_1_values` (JSON de labels) comme source de
    lecture du calcul des lignes normales du bilan. Une ligne par
    (mapping, category). La sérialisation API continue d'exposer des labels
    (reconstruits depuis `categories.label`), byte-identiques à l'ancien JSON.
    """
    __tablename__ = "bilan_mapping_categories"

    id = Column(Integer, primary_key=True, index=True)
    mapping_id = Column(Integer, ForeignKey("bilan_mappings.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    mapping = relationship("BilanMapping", back_populates="category_links")
    category = relationship("Category")

    __table_args__ = (
        UniqueConstraint("mapping_id", "category_id", name="uq_bilan_mapping_category"),
    )


class BilanConfig(Base):
    """Configuration globale pour le bilan (filtre Level 3)."""
    __tablename__ = "bilan_config"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    level_3_values = Column(Text, nullable=False, default="[]")  # JSON array des level_3 sélectionnés (ex: '["VALEUR1", "VALEUR2"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation avec Property
    property = relationship("Property", back_populates="bilan_config")
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_bilan_config_property_id', 'property_id'),
    )


class ProRataSettings(Base):
    """Paramètres globaux Pro Rata & Forecast par propriété."""
    __tablename__ = "prorata_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    prorata_enabled = Column(Boolean, default=False, nullable=False)  # Activer prévisions année en cours
    forecast_enabled = Column(Boolean, default=False, nullable=False)  # Activer projection multi-années
    forecast_years = Column(Integer, default=3, nullable=False)  # Nombre d'années à projeter (1-10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="prorata_settings")


class AnnualForecastConfig(Base):
    """Configuration des prévisions annuelles par propriété et catégorie comptable."""
    __tablename__ = "annual_forecast_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)  # Année de base (ex: 2026)
    level_1 = Column(String(100), nullable=False, index=True)  # Catégorie comptable
    target_type = Column(String(50), nullable=False, index=True)  # "compte_resultat", "bilan_actif", "bilan_passif"
    base_annual_amount = Column(EuroCents, nullable=False)  # Montant prévu annuel (centimes en base, euros à l'ORM)
    annual_growth_rate = Column(Float, default=0.0, nullable=False)  # Taux d'évolution (ex: 0.02 = +2%)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    property = relationship("Property", back_populates="annual_forecast_configs")
    
    # Index et contraintes
    __table_args__ = (
        Index('idx_forecast_config_property_year', 'property_id', 'year'),
        Index('idx_forecast_config_property_level1', 'property_id', 'level_1'),
        Index('idx_forecast_config_property_year_level1_type', 'property_id', 'year', 'level_1', 'target_type', unique=True),
    )

