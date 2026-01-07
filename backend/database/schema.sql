-- Database Schema for LMNP Application
-- ⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
-- 
-- This schema is maintained for reference. The actual schema is managed
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

-- Enriched transactions table - Transactions with classifications
CREATE TABLE IF NOT EXISTS enriched_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL UNIQUE,
    mois INTEGER NOT NULL,
    annee INTEGER NOT NULL,
    level_1 VARCHAR(100),
    level_2 VARCHAR(100),
    level_3 VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

CREATE INDEX IF NOT EXISTS idx_enriched_transaction_id ON enriched_transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_enriched_year_month ON enriched_transactions(annee, mois);
CREATE INDEX IF NOT EXISTS idx_enriched_level_1 ON enriched_transactions(level_1);
CREATE INDEX IF NOT EXISTS idx_enriched_level_2 ON enriched_transactions(level_2);
CREATE INDEX IF NOT EXISTS idx_enriched_level_3 ON enriched_transactions(level_3);
CREATE INDEX IF NOT EXISTS idx_enriched_levels ON enriched_transactions(level_1, level_2, level_3);

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
