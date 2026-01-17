"""
SQLAlchemy models for the LMNP application.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text, 
    ForeignKey, Boolean, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Transaction(Base):
    """Raw transactions aggregated from CSV files."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    quantite = Column(Float, nullable=False)  # Montant de la transaction
    nom = Column(String(500), nullable=False, index=True)  # Description/nom de la transaction
    solde = Column(Float, nullable=False)  # Solde après transaction
    source_file = Column(String(255))  # Fichier source d'origine
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour détection de doublons
    __table_args__ = (
        Index('idx_transaction_unique', 'date', 'quantite', 'nom'),
    )


class EnrichedTransaction(Base):
    """Transactions with classifications and metadata."""
    __tablename__ = "enriched_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, unique=True)
    mois = Column(Integer, nullable=False, index=True)  # 1-12
    annee = Column(Integer, nullable=False, index=True)
    level_1 = Column(String(100), index=True)  # Catégorie principale
    level_2 = Column(String(100), index=True)  # Sous-catégorie
    level_3 = Column(String(100), index=True)  # Détail spécifique
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    transaction = relationship("Transaction", backref="enriched")
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_enriched_year_month', 'annee', 'mois'),
        Index('idx_enriched_levels', 'level_1', 'level_2', 'level_3'),
    )


class Mapping(Base):
    """Mapping rules for transaction names to categories."""
    __tablename__ = "mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(500), nullable=False, unique=True, index=True)  # Nom/pattern de transaction
    level_1 = Column(String(100), nullable=False)
    level_2 = Column(String(100), nullable=False)
    level_3 = Column(String(100))
    is_prefix_match = Column(Boolean, default=True)  # Si True, match par préfixe
    priority = Column(Integer, default=0)  # Priorité pour résolution de conflits
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Parameter(Base):
    """Configuration parameters for calculations."""
    __tablename__ = "parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(String(500), nullable=False)  # Valeur stockée comme string, conversion selon type
    value_type = Column(String(20), default="float")  # float, int, string
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Amortization(Base):
    """Amortization calculations by category and year."""
    __tablename__ = "amortizations"
    
    id = Column(Integer, primary_key=True, index=True)
    type_amortissement = Column(String(100), nullable=False, index=True)  # meubles, travaux, construction, terrain
    annee = Column(Integer, nullable=False, index=True)
    montant = Column(Float, nullable=False)  # Montant négatif (charge)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))  # Transaction source si applicable
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour regroupements
    __table_args__ = (
        Index('idx_amort_type_year', 'type_amortissement', 'annee'),
    )


class FinancialStatement(Base):
    """Generated financial statements (bilan, compte de résultat)."""
    __tablename__ = "financial_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    statement_type = Column(String(50), nullable=False, index=True)  # bilan_actif, bilan_passif, compte_resultat
    annee = Column(Integer, nullable=False, index=True)
    ligne = Column(String(200), nullable=False)  # Nom de la ligne (ex: "TRAVAUX ET PRESTATIONS DE SERV")
    montant = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches
    __table_args__ = (
        Index('idx_fs_type_year', 'statement_type', 'annee'),
    )


class ConsolidatedFinancialStatement(Base):
    """Consolidated financial statements with coherence analysis."""
    __tablename__ = "consolidated_financial_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    annee = Column(Integer, nullable=False, index=True)
    total_actif = Column(Float, nullable=False)
    total_passif = Column(Float, nullable=False)
    difference = Column(Float)  # Actif - Passif
    pourcentage_ecart = Column(Float)  # ((Passif - Actif) / Passif) * 100
    generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FileImport(Base):
    """Track imported CSV files to prevent duplicate processing."""
    __tablename__ = "file_imports"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)  # Nom du fichier (unique)
    imported_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    imported_count = Column(Integer, default=0)  # Nombre de transactions importées
    duplicates_count = Column(Integer, default=0)  # Nombre de doublons détectés
    errors_count = Column(Integer, default=0)  # Nombre d'erreurs
    period_start = Column(Date)  # Date de début des transactions
    period_end = Column(Date)  # Date de fin des transactions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches
    __table_args__ = (
        Index('idx_file_imports_filename', 'filename'),
        Index('idx_file_imports_imported_at', 'imported_at'),
    )


class MappingImport(Base):
    """Track imported Excel mapping files to prevent duplicate processing."""
    __tablename__ = "mapping_imports"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)  # Nom du fichier (unique)
    imported_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    imported_count = Column(Integer, default=0)  # Nombre de mappings importés
    duplicates_count = Column(Integer, default=0)  # Nombre de doublons détectés
    errors_count = Column(Integer, default=0)  # Nombre d'erreurs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches
    __table_args__ = (
        Index('idx_mapping_imports_filename', 'filename'),
        Index('idx_mapping_imports_imported_at', 'imported_at'),
    )


class PivotConfig(Base):
    """Saved pivot table configurations."""
    __tablename__ = "pivot_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Nom du tableau
    config = Column(Text, nullable=False)  # Configuration JSON (rows, columns, data, filters)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches
    __table_args__ = (
        Index('idx_pivot_configs_name', 'name'),
    )


class AllowedMapping(Base):
    """Allowed mapping combinations (level_1, level_2, level_3) that can be used for transactions."""
    __tablename__ = "allowed_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    level_1 = Column(String(100), nullable=False, index=True)  # Catégorie principale
    level_2 = Column(String(100), nullable=False, index=True)  # Sous-catégorie
    level_3 = Column(String(100), index=True)  # Détail spécifique (nullable)
    is_hardcoded = Column(Boolean, default=False, nullable=False)  # True pour les 50 combinaisons initiales (protégées)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contrainte unique sur la combinaison (level_1, level_2, level_3)
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_allowed_mapping_unique', 'level_1', 'level_2', 'level_3', unique=True),
        Index('idx_allowed_mapping_level_1', 'level_1'),
        Index('idx_allowed_mapping_level_2', 'level_2'),
        Index('idx_allowed_mapping_level_3', 'level_3'),
    )


class AmortizationType(Base):
    """Types d'amortissement configurables pour les immobilisations."""
    __tablename__ = "amortization_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # Nom du type (ex: "Immobilisation terrain")
    level_2_value = Column(String(100), nullable=False, index=True)  # Valeur level_2 à considérer (ex: "ammortissements")
    level_1_values = Column(Text, nullable=False, default="[]")  # JSON array des valeurs level_1 mappées
    start_date = Column(Date, nullable=True)  # Date de début d'amortissement (override, nullable)
    duration = Column(Float, nullable=False, default=0.0)  # Durée d'amortissement en années (0 = non amortissable)
    annual_amount = Column(Float, nullable=True)  # Annuité d'amortissement (override, nullable)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_amortization_type_level_2', 'level_2_value'),
    )


class AmortizationResult(Base):
    """Résultats d'amortissement par transaction, année et catégorie."""
    __tablename__ = "amortization_results"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)  # Année d'amortissement (ex: 2021, 2022)
    category = Column(String(255), nullable=False, index=True)  # Nom du type d'amortissement (ex: "Immobilisation terrain")
    amount = Column(Float, nullable=False)  # Montant amorti pour cette année (négatif)
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
    date = Column(Date, nullable=False, index=True)  # Date de la mensualité (01/01/année)
    capital = Column(Float, nullable=False)  # Montant du capital remboursé
    interest = Column(Float, nullable=False)  # Montant des intérêts
    insurance = Column(Float, nullable=False)  # Montant de l'assurance crédit
    total = Column(Float, nullable=False)  # Total de la mensualité (capital + interest + insurance)
    loan_name = Column(String(255), nullable=False, index=True)  # Nom du prêt (ex: "Prêt principal")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_loan_payment_date', 'date'),
        Index('idx_loan_payment_loan_name', 'loan_name'),
        Index('idx_loan_payment_loan_name_date', 'loan_name', 'date', unique=True),
    )


class LoanConfig(Base):
    """Configurations de crédit (multi-crédits possibles)."""
    __tablename__ = "loan_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)  # Nom du crédit (ex: "Prêt principal", "Prêt construction")
    credit_amount = Column(Float, nullable=False)  # Montant du crédit accordé en euros
    interest_rate = Column(Float, nullable=False)  # Taux fixe actuel hors assurance en %
    duration_years = Column(Integer, nullable=False)  # Durée de l'emprunt en années
    initial_deferral_months = Column(Integer, default=0, nullable=False)  # Décalage initial en mois
    loan_start_date = Column(Date, nullable=True)  # Date d'emprunt
    loan_end_date = Column(Date, nullable=True)  # Date de fin prévisionnelle
    monthly_insurance = Column(Float, default=0.0, nullable=False)  # Assurance mensuelle en euros
    simulation_months = Column(Text, nullable=True)  # JSON array des mensualités personnalisées (ex: "[1, 50, 100, 150, 200]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_loan_config_name', 'name', unique=True),
    )


class CompteResultatMapping(Base):
    """Mappings pour le compte de résultat (level_1 → catégories comptables)."""
    __tablename__ = "compte_resultat_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(255), nullable=False, index=True)  # Nom de la catégorie comptable (ex: "Loyers hors charge encaissés")
    type = Column(String(50), nullable=True)  # Type: "Produits d'exploitation" ou "Charges d'exploitation" (pour les catégories personnalisées)
    level_1_values = Column(Text, nullable=True)  # JSON array des level_1 à inclure (ex: '["LOYERS", "REVENUS"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_compte_resultat_mapping_category', 'category_name'),
    )


class CompteResultatData(Base):
    """Données du compte de résultat par année et catégorie."""
    __tablename__ = "compte_resultat_data"
    
    id = Column(Integer, primary_key=True, index=True)
    annee = Column(Integer, nullable=False, index=True)  # Année du compte de résultat
    category_name = Column(String(255), nullable=False, index=True)  # Nom de la catégorie comptable
    amount = Column(Float, nullable=False)  # Montant pour cette catégorie et cette année
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_compte_resultat_data_year_category', 'annee', 'category_name'),
        Index('idx_compte_resultat_data_year', 'annee'),
        Index('idx_compte_resultat_data_category', 'category_name'),
    )


class CompteResultatConfig(Base):
    """Configuration globale pour le compte de résultat (filtre Level 3)."""
    __tablename__ = "compte_resultat_config"
    
    id = Column(Integer, primary_key=True, index=True)
    level_3_values = Column(Text, nullable=False, default="[]")  # JSON array des level_3 sélectionnés (ex: '["VALEUR1", "VALEUR2"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompteResultatOverride(Base):
    """Override manuel du résultat de l'exercice par année."""
    __tablename__ = "compte_resultat_override"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, unique=True, index=True)  # Année du compte de résultat
    override_value = Column(Float, nullable=False)  # Valeur override du résultat de l'exercice
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_compte_resultat_override_year', 'year'),
    )


class BilanMapping(Base):
    """Mappings pour le bilan (level_1 → catégories comptables)."""
    __tablename__ = "bilan_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(255), nullable=False, index=True)  # Nom de la catégorie comptable (niveau C)
    type = Column(String(50), nullable=False, index=True)  # Type: "ACTIF" ou "PASSIF"
    sub_category = Column(String(100), nullable=False, index=True)  # Sous-catégorie (niveau B)
    level_1_values = Column(Text, nullable=True)  # JSON array des level_1 à inclure (ex: '["LOYERS", "REVENUS"]')
    is_special = Column(Boolean, nullable=False, default=False)  # Indique si c'est une catégorie spéciale
    special_source = Column(String(100), nullable=True)  # Source pour les catégories spéciales ("amortization_result", "transactions", "compte_resultat", "compte_resultat_cumul", "loan_payments")
    compte_resultat_view_id = Column(Integer, nullable=True)  # Pour catégorie "Résultat de l'exercice" (ForeignKey vers compte_resultat_mapping_views.id - table à créer si nécessaire)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_bilan_mapping_category', 'category_name'),
        Index('idx_bilan_mapping_type', 'type'),
        Index('idx_bilan_mapping_sub_category', 'sub_category'),
        Index('idx_bilan_mapping_type_sub_category', 'type', 'sub_category'),
    )


class BilanData(Base):
    """Données du bilan par année et catégorie."""
    __tablename__ = "bilan_data"
    
    id = Column(Integer, primary_key=True, index=True)
    annee = Column(Integer, nullable=False, index=True)  # Année du bilan
    category_name = Column(String(255), nullable=False, index=True)  # Nom de la catégorie comptable
    amount = Column(Float, nullable=False)  # Montant pour cette catégorie et cette année
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Index pour recherches fréquentes
    __table_args__ = (
        Index('idx_bilan_data_year_category', 'annee', 'category_name'),
        Index('idx_bilan_data_year', 'annee'),
        Index('idx_bilan_data_category', 'category_name'),
    )


class BilanConfig(Base):
    """Configuration globale pour le bilan (filtre Level 3)."""
    __tablename__ = "bilan_config"
    
    id = Column(Integer, primary_key=True, index=True)
    level_3_values = Column(Text, nullable=False, default="[]")  # JSON array des level_3 sélectionnés (ex: '["VALEUR1", "VALEUR2"]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

