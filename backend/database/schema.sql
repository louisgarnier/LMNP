-- Database Schema for LMNP Application
-- ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
--
-- ============================================================================
-- ⚠️ OBSOLÈTE / NON FAISANT AUTORITÉ (mis à jour étape 2 Task 10, 2026-07-12)
-- ============================================================================
-- Ce fichier n'est JAMAIS exécuté et a divergé de la réalité. La source de
-- vérité du schéma est backend/database/models.py (SQLAlchemy), matérialisée
-- par init_database(). Ne pas s'y fier pour la structure courante.
--
-- Écarts connus avec les modèles actuels (liste non exhaustive) :
--   • Le référentiel de l'étape 2 est ABSENT ici : category_groups, categories,
--     compte_resultat_mapping_categories, bilan_mapping_categories, ainsi que
--     transactions.category_id et les colonnes line_code des configs.
--   • Les montants monétaires sont désormais stockés en CENTIMES (INTEGER) via
--     le TypeDecorator EuroCents (étape 2 Task 9), pas en REAL/euros.
--   • Des tables listées plus bas (amortizations, financial_statements,
--     consolidated_financial_statements, parameters, pivot_configs, …) ne
--     reflètent plus les modèles ; se reporter à models.py.
--   • enriched_transactions et 8 tables orphelines ont été supprimées à
--     l'étape 2 (Tasks 1 & 8) — le bloc enriched_transactions a été retiré
--     ci-dessous, mais le reste n'a pas été réconcilié.
-- ============================================================================
--
-- This schema is maintained for reference only. The actual schema is managed
-- by SQLAlchemy models in models.py and created via init_database().

-- Transactions table - Raw transactions aggregated from CSV files
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    quantite REAL NOT NULL,
    nom VARCHAR(500) NOT NULL,
    solde REAL NOT NULL,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_nom ON transactions(nom);
CREATE INDEX IF NOT EXISTS idx_transaction_unique ON transactions(date, quantite, nom);

-- (étape 2 Task 8) La table enriched_transactions a été SUPPRIMÉE. Les
-- classifications passent désormais par transactions.category_id → categories →
-- category_groups (voir models.py). Bloc retiré volontairement de ce fichier.

-- Mappings table - Mapping rules for transaction names to categories
CREATE TABLE IF NOT EXISTS mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom VARCHAR(500) NOT NULL UNIQUE,
    level_1 VARCHAR(100) NOT NULL,
    level_2 VARCHAR(100) NOT NULL,
    level_3 VARCHAR(100),
    is_prefix_match BOOLEAN DEFAULT 1,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mappings_nom ON mappings(nom);

-- Allowed mappings table - Allowed mapping combinations (level_1, level_2, level_3)
CREATE TABLE IF NOT EXISTS allowed_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_1 VARCHAR(100) NOT NULL,
    level_2 VARCHAR(100) NOT NULL,
    level_3 VARCHAR(100),
    is_hardcoded BOOLEAN DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_allowed_mapping_unique ON allowed_mappings(level_1, level_2, level_3);
CREATE INDEX IF NOT EXISTS idx_allowed_mapping_level_1 ON allowed_mappings(level_1);
CREATE INDEX IF NOT EXISTS idx_allowed_mapping_level_2 ON allowed_mappings(level_2);
CREATE INDEX IF NOT EXISTS idx_allowed_mapping_level_3 ON allowed_mappings(level_3);

-- Parameters table - Configuration parameters
CREATE TABLE IF NOT EXISTS parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) NOT NULL UNIQUE,
    value VARCHAR(500) NOT NULL,
    value_type VARCHAR(20) DEFAULT 'float',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parameters_key ON parameters(key);

-- Amortizations table - Amortization calculations
CREATE TABLE IF NOT EXISTS amortizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_amortissement VARCHAR(100) NOT NULL,
    annee INTEGER NOT NULL,
    montant REAL NOT NULL,
    transaction_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

CREATE INDEX IF NOT EXISTS idx_amortizations_type ON amortizations(type_amortissement);
CREATE INDEX IF NOT EXISTS idx_amortizations_annee ON amortizations(annee);
CREATE INDEX IF NOT EXISTS idx_amort_type_year ON amortizations(type_amortissement, annee);

-- Financial statements table - Generated financial statements
CREATE TABLE IF NOT EXISTS financial_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_type VARCHAR(50) NOT NULL,
    annee INTEGER NOT NULL,
    ligne VARCHAR(200) NOT NULL,
    montant REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fs_type ON financial_statements(statement_type);
CREATE INDEX IF NOT EXISTS idx_fs_annee ON financial_statements(annee);
CREATE INDEX IF NOT EXISTS idx_fs_type_year ON financial_statements(statement_type, annee);

-- Consolidated financial statements table
CREATE TABLE IF NOT EXISTS consolidated_financial_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    annee INTEGER NOT NULL,
    total_actif REAL NOT NULL,
    total_passif REAL NOT NULL,
    difference REAL,
    pourcentage_ecart REAL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_consolidated_annee ON consolidated_financial_statements(annee);

-- File imports table - Track imported CSV files to prevent duplicate processing
CREATE TABLE IF NOT EXISTS file_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL UNIQUE,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    imported_count INTEGER DEFAULT 0,
    duplicates_count INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_file_imports_filename ON file_imports(filename);
CREATE INDEX IF NOT EXISTS idx_file_imports_imported_at ON file_imports(imported_at);

-- Mapping imports table - Track imported Excel mapping files to prevent duplicate processing
CREATE TABLE IF NOT EXISTS mapping_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL UNIQUE,
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    imported_count INTEGER DEFAULT 0,
    duplicates_count INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mapping_imports_filename ON mapping_imports(filename);
CREATE INDEX IF NOT EXISTS idx_mapping_imports_imported_at ON mapping_imports(imported_at);

-- Pivot configs table - Saved pivot table configurations
CREATE TABLE IF NOT EXISTS pivot_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    config TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pivot_configs_name ON pivot_configs(name);

-- Loan payments table - Mensualités de crédit (capital, intérêt, assurance)
CREATE TABLE IF NOT EXISTS loan_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    capital REAL NOT NULL,
    interest REAL NOT NULL,
    insurance REAL NOT NULL,
    total REAL NOT NULL,
    loan_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loan_payment_date ON loan_payments(date);
CREATE INDEX IF NOT EXISTS idx_loan_payment_loan_name ON loan_payments(loan_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_loan_payment_loan_name_date ON loan_payments(loan_name, date);

-- Loan configs table - Configurations de crédit (multi-crédits possibles)
CREATE TABLE IF NOT EXISTS loan_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    credit_amount REAL NOT NULL,
    interest_rate REAL NOT NULL,
    duration_years INTEGER NOT NULL,
    initial_deferral_months INTEGER NOT NULL DEFAULT 0,
    loan_start_date DATE,
    loan_end_date DATE,
    monthly_insurance REAL NOT NULL DEFAULT 0.0,
    simulation_months TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_loan_config_name ON loan_configs(name);

-- Compte de résultat override table - Override manuel du résultat de l'exercice par année
CREATE TABLE IF NOT EXISTS compte_resultat_override (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL UNIQUE,
    override_value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_compte_resultat_override_year ON compte_resultat_override(year);
