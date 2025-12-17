# Documentation Fonctionnalités - Système de Gestion Comptable Immobilier

## Vue d'ensemble du système

Le système actuel est composé de 9 scripts Python qui traitent des données financières pour générer des états comptables complets (bilan, compte de résultat, analyses). Il fonctionne avec des fichiers CSV et Excel en entrée et produit des rapports financiers structurés.

## Architecture générale

### Flux de données
```
Input Files → Agrégation → Enrichissement → Calculs → États financiers
     ↓             ↓            ↓           ↓            ↓
  CSV/Excel → all_trades.csv → _extra.csv → Reports → Consolidé
```

### Ordre d'exécution recommandé
1. `1_aggregate_trades.py` - Agrégation des transactions
2. `2_add_extra_columns.py` - Enrichissement avec mapping
3. `amort.py` - Calcul des amortissements
4. `compte_de_resultat.py` - Génération du compte de résultat
5. `bilan_actif.py` - Génération du bilan actif
6. `bilan_passif.py` - Génération du bilan passif
7. `merge_etats_financiers.py` - Consolidation finale
8. `create_pivot.py` - Analyses pivot (optionnel)
9. `simu_addcol.py` - Simulations (optionnel)

---

## FONCTIONNALITÉ 1: Agrégation des transactions
**Script:** `1_aggregate_trades.py`

### Objectif
Consolider tous les fichiers de transactions bancaires en un seul fichier uniforme.

### Fonctionnalités détaillées

#### Inputs
- **Fichier principal:** `data/input/trades/trades_evry_2024.csv`
  - Format: Date;Quantité;nom;solde
  - Encodage: UTF-8
  - Séparateur: `;`
- **Fichiers additionnels:** `data/input/trades/0002*.csv`
  - Formats variables (détection automatique)
  - Encodages multiples supportés (UTF-8, Latin-1, ISO-8859-1, CP1252)

#### Traitement
1. **Lecture sécurisée multi-encodage** - Détecte automatiquement l'encodage et le séparateur
2. **Normalisation des colonnes** - Harmonise les noms de colonnes entre fichiers
3. **Nettoyage des données**:
   - Conversion des dates au format `%d/%m/%Y`
   - Normalisation des montants (gestion virgules/points)
   - Suppression des espaces et caractères indésirables
4. **Validation et filtrage** - Supprime les lignes avec dates invalides
5. **Tri chronologique** - Classe par date croissante

#### Outputs
- **Fichier:** `data/output/all_trades.csv`
- **Format:** Date;Quantité;nom;solde
- **Statistiques:** Nombre de transactions, période couverte, répartition par fichier source

#### Gestion d'erreurs
- Logging détaillé des opérations
- Gestion des encodages problématiques
- Rapport des lignes invalides supprimées
- Archive automatique en cas d'échec

---

## FONCTIONNALITÉ 2: Enrichissement et catégorisation
**Script:** `2_add_extra_columns.py`

### Objectif
Enrichir les transactions avec une catégorisation comptable hiérarchique et des métadonnées temporelles.

### Fonctionnalités détaillées

#### Inputs
- **Transactions:** `data/output/all_trades.csv`
- **Mapping:** `data/mapping/mapping.xlsx`
  - Structure: nom | level 1 | level 2 | level 3
  - Système de correspondance intelligent

#### Traitement
1. **Ajout métadonnées temporelles**:
   - `mois` - Numéro du mois (1-12)
   - `annee` - Année de la transaction
2. **Mapping intelligent**:
   - Correspondance par préfixe de nom
   - Gestion des cas spéciaux (PRLV SEPA, VIR STRIPE)
   - Recherche du meilleur match (plus long préfixe)
3. **Catégorisation hiérarchique**:
   - `level 1` - Catégorie principale (ex: "loyers recu", "charges")
   - `level 2` - Sous-catégorie (ex: "Produit", "Charges", "Impots")
   - `level 3` - Détail spécifique

#### Outputs
- **Fichier:** `data/output/all_trades_extra.csv`
- **Colonnes:** Date;mois;annee;Quantité;nom;solde;level 1;level 2;level 3
- **Rapports:**
  - `missing_mappings.csv` - Transactions non mappées
  - Statistiques de couverture du mapping
  - Répartition par catégorie

#### Algorithme de mapping
```
Pour chaque nom de transaction:
  1. Chercher correspondances par préfixe
  2. Cas spéciaux prioritaires
  3. Sélectionner le match le plus long
  4. Appliquer les 3 niveaux de catégorisation
```

---

## FONCTIONNALITÉ 3: Calcul des amortissements
**Script:** `amort.py`

### Objectif
Calculer les amortissements annuels basés sur les acquisitions d'immobilisations et leurs durées de vie.

### Fonctionnalités détaillées

#### Inputs
- **Transactions:** `data/output/all_trades_extra.csv` (filtrées sur level 2 = "ammortissements")
- **Paramètres:** `data/input/app_data/parametres.xlsx`
  - Durées d'amortissement par catégorie d'actif

#### Catégories d'actifs supportées
1. **meubles** → `ammortissement meubles`
2. **travaux** → `ammortissement travaux`
3. **pret banque - construction** → `ammortissement construction`
4. **pret banque - terrain** → `ammortissement terrain`

#### Algorithme de calcul
1. **Convention 30/360** - Calcul des jours selon standard comptable
2. **Répartition proportionnelle**:
   ```
   Montant_journalier = Montant_total / (Durée_années × 360)
   Montant_année_N = Jours_dans_année_N × Montant_journalier
   ```
3. **Ajustement final** - Garantit que la somme = montant initial
4. **Valeurs négatives** - Les amortissements sont des charges (négatifs)

#### Outputs
- **Fichier:** `data/output/reports/amortissement.csv`
- **Structure:** Type | 2021 | 2022 | ... | 2050
- **Ligne Total** - Somme de tous les amortissements par année

---

## FONCTIONNALITÉ 4: Compte de résultat
**Script:** `compte_de_resultat.py`

### Objectif
Générer le compte de résultat annuel avec produits, charges et résultat net.

### Fonctionnalités détaillées

#### Structure du compte de résultat

##### PRODUITS D'EXPLOITATION
1. **TRAVAUX ET PRESTATIONS DE SERV**
   - Source: level 2 = "Produit" ET level 1 = "loyers recu"
   - Revenus locatifs principaux
2. **TRANSFERT DE CHARGES D'EXPLOIT**
   - Source: level 2 = "Produit" ET level 1 ≠ "loyers recu"
   - Autres produits (remboursements, divers)

##### CHARGES D'EXPLOITATION
1. **Charges**
   - Source: level 2 = "Charges"
   - Charges de copropriété, entretien, etc.
2. **Impots**
   - Source: level 2 = "Impots"
   - Taxes foncières et autres impôts
3. **Amortissements** (par catégorie)
   - Source: `amortissement.csv`
   - Détail par type d'immobilisation

##### CHARGES FINANCIÈRES
1. **CHARGES D'INTERET**
   - Source: `tableau_ammort_taxes.xlsx` (lignes "interets" + "assurance cred")
   - Prorata temporel pour année en cours selon mensualités payées

#### Calculs automatiques
- **Résultat d'exploitation** = Produits - Charges d'exploitation
- **Résultat de l'exercice** = Résultat d'exploitation - Charges financières
- **Prorata année courante** = Ajustement selon nombre de mensualités payées

#### Outputs
- **Fichier:** `data/output/reports/compte_resultat_DD_MM_YYYY.csv`
- **Archivage** automatique des versions précédentes

---

## FONCTIONNALITÉ 5: Bilan actif
**Script:** `bilan_actif.py`

### Objectif
Générer la partie actif du bilan comptable avec immobilisations et actif circulant.

### Fonctionnalités détaillées

#### Structure du bilan actif

##### ACTIF IMMOBILISÉ
1. **Actif immobilisé** (valeur nette)
   - Calcul cumulé: Acquisitions précédentes + Acquisitions année + Amortissements cumulés
   - Évolution année par année
2. **actifs** (acquisitions brutes)
   - Source: level 2 = "ammortissements" par année
   - Montants positifs (×-1 pour inverser le signe)

##### DÉTAIL AMORTISSEMENTS
- **ammort [Type]** par catégorie
- Source: `amortissement.csv`
- Amortissements cumulés par type d'actif

##### ACTIF CIRCULANT
- **Actif circulant**
- Source: Dernier solde bancaire de chaque année
- Liquidités disponibles

#### Algorithme de calcul
```
Pour chaque année N:
  Actif_immobilisé_N = Actif_immobilisé_(N-1) + Acquisitions_N + Amortissements_N
  Actif_circulant_N = Dernier_solde_année_N
  Total_Bilan_Actif_N = Actif_immobilisé_N + Actif_circulant_N
```

#### Outputs
- **Fichier:** `data/output/reports/bilan_actif_DD_MM_YYYY.csv`
- **Ligne totale** - Total du Bilan Actif par année

---

## FONCTIONNALITÉ 6: Bilan passif
**Script:** `bilan_passif.py`

### Objectif
Générer la partie passif du bilan avec capitaux propres et dettes.

### Fonctionnalités détaillées

#### Structure du bilan passif

##### CAPITAUX PROPRES
1. **COMPTE DE L'EXPLOITANT**
   - Source: level 2 = "perso" (apports/retraits cumulés)
   - Accumulation des apports personnels
2. **Résultat de l'exercice**
   - Source: Dernière ligne du compte de résultat
   - Résultat net de chaque année
3. **Report à nouveau**
   - Cumul des résultats des exercices précédents
   - Report_N = Report_(N-1) + Résultat_(N-1)
4. **Dépôts et cautionnements reçus**
   - Source: level 2 = "Cautions" (cumulés)
   - Cautions locataires et autres dépôts

##### DETTES
1. **Dettes**
   - Calcul: Prêts_cumulés - Remboursements_cumulés
   - Sources:
     - Prêts: level 2 = "prêt (inflows)"
     - Remboursements: `tableau_ammort_taxes.xlsx` (ligne "capital")
2. **Dettes fin d'année en cours**
   - Uniquement pour l'année courante
   - Capital restant à rembourser selon mensualités payées
   - Calcul prorata: (12 - mois_payés) / 12 × capital_annuel

#### Calculs complexes
```
Capitaux_propres = Compte_exploitant + Résultat + Report + Dépôts
Dettes_totales = Dette_principale + Dette_fin_année_courante (si applicable)
Total_Bilan_Passif = Capitaux_propres + Dettes_totales
```

#### Outputs
- **Fichier:** `data/output/reports/bilan_passif_DD_MM_YYYY.csv`
- **Validation** - Total doit équilibrer avec total actif

---

## FONCTIONNALITÉ 7: Consolidation des états financiers
**Script:** `merge_etats_financiers.py`

### Objectif
Fusionner tous les états financiers en un document unique avec analyses de cohérence.

### Fonctionnalités détaillées

#### Traitement automatique
1. **Détection de la dernière date** - Trouve automatiquement les fichiers les plus récents
2. **Formatage français** - Conversion des nombres au format français (virgule décimale)
3. **Gestion des valeurs manquantes** - Traitement des NaN et valeurs vides

#### Structure du fichier consolidé
1. **BILAN ACTIF** complet
2. **Ligne vide**
3. **BILAN PASSIF** complet
4. **ANALYSES DE COHÉRENCE**:
   - **Différence Actif-Passif** par année
   - **Pourcentage différence (P-A)/P** en %
5. **Double ligne vide**
6. **COMPTE DE RÉSULTAT** complet

#### Contrôles qualité
```
Différence = Total_Actif - Total_Passif
Pourcentage_écart = ((Passif - Actif) / Passif) × 100
```

#### Outputs
- **Fichier:** `data/output/reports/etats_financiers_consolides_DD_MM_YYYY.csv`
- **Format:** CSV avec séparateur `;` et virgules décimales
- **Logging** complet des opérations

---

## FONCTIONNALITÉ 8: Analyse pivot
**Script:** `create_pivot.py`

### Objectif
Créer des analyses croisées par catégories et années pour l'aide à la décision.

### Fonctionnalités détaillées

#### Structure de l'analyse
- **Dimensions:** level 3 × level 2 × level 1 / années
- **Valeurs:** Somme des quantités par croisement
- **Totaux:** Par niveau hiérarchique + Grand total

#### Types de totaux
1. **Totaux level 2** - Par sous-catégorie
2. **Totaux level 3** - Par catégorie principale
3. **Grand Total** - Toutes transactions confondues
4. **Colonne Grand Total** - Somme toutes années

#### Outputs
- **Fichier:** `data/output/reports/pivot.csv`
- **Usage:** Analyses de répartition, évolutions, budgets

---

## FONCTIONNALITÉ 9: Simulation budgétaire
**Script:** `simu_addcol.py`

### Objectif
Créer des projections budgétaires basées sur des paramètres ajustables.

### Fonctionnalités détaillées

#### Mécanisme de simulation
1. **Base de simulation** - Dernière année réelle
2. **Paramètres ajustables**:
   - `loyer` → "TRAVAUX ET PRESTATIONSDE SERV"
   - `charges copro` → "Charges"
   - `taxe fonciere` → "Impots"
3. **Source des paramètres** - `parametres.xlsx`

#### Traitement
1. Copie de la dernière année vers colonne "(sim)"
2. Remplacement des valeurs par les paramètres
3. Maintien des autres lignes inchangées

#### Outputs
- **Fichier:** `data/output/reports/simu_step_1.csv`
- **Usage:** Projections, analyses de sensibilité

---

## Configuration et paramètres

### Fichiers de paramétrage

#### `parametres.xlsx`
- **Usage:** Durées d'amortissement, valeurs de simulation
- **Structure:** Paramètre | Valeur
- **Exemples:**
  - `ammortissement meubles` : 5
  - `ammortissement travaux` : 10
  - `loyer` : 850
  - `charges copro` : -120

#### `tableau_ammort_taxes.xlsx`
- **Usage:** Échéancier de prêt détaillé
- **Lignes importantes:**
  - `capital` : Remboursement capital par année
  - `interets` : Charges d'intérêts
  - `assurance cred` : Assurance emprunteur

#### `mapping.xlsx`
- **Usage:** Correspondance noms transactions → catégories
- **Structure:** nom | level 1 | level 2 | level 3
- **Logique:** Mapping par préfixe le plus long

### Gestion des erreurs et logs
- **Répertoire logs:** `logs/`
- **Fichiers horodatés** pour chaque exécution
- **Niveaux de log:** INFO, WARNING, ERROR, DEBUG
- **Archivage automatique** des anciens rapports

### Formats de données
- **Dates:** Format français DD/MM/YYYY
- **Nombres:** Virgule comme séparateur décimal
- **Séparateur CSV:** Point-virgule (;)
- **Encodage:** UTF-8 avec fallbacks multiples

---

## Recommandations pour l'interface utilisateur

### Fonctionnalités prioritaires à implémenter

#### 1. Gestionnaire de fichiers d'entrée
- Upload/import des CSV bancaires
- Prévisualisation et validation des formats
- Gestion multi-encodage automatique
- Interface de correction des erreurs de format

#### 2. Éditeur de mapping intelligent
- Interface graphique pour créer/modifier les correspondances
- Suggestions automatiques basées sur l'historique
- Prévisualisation du mapping avant application
- Gestion des cas spéciaux et exceptions

#### 3. Dashboard de contrôle qualité
- Indicateurs de cohérence des bilans
- Alertes sur écarts Actif/Passif
- Suivi des transactions non mappées
- Historique des corrections appliquées

#### 4. Générateur de rapports interactif
- Sélection des périodes d'analyse
- Export dans multiple formats (PDF, Excel, CSV)
- Graphiques et visualisations automatiques
- Comparaisons inter-périodes

#### 5. Module de simulation avancé
- Interface de modification des paramètres
- Analyses de sensibilité multi-variables
- Projections sur plusieurs années
- Scénarios comparatifs

### Architecture technique suggérée
- **Backend:** API REST pour logique métier
- **Frontend:** Interface moderne (React/Vue.js)
- **Base de données:** Stockage structuré des transactions et paramètres
- **Sécurité:** Authentification et sauvegarde des données
- **Performance:** Cache et traitement asynchrone pour gros volumes

Cette documentation devrait vous permettre de recréer toutes les fonctionnalités dans un environnement plus user-friendly avec une interface graphique moderne.
