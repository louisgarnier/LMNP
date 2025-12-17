# Raw Requirements

This document captures the initial, unprocessed requirements for the project. Requirements can be provided in any format - bullet points, paragraphs, user stories, etc.

## How to Use

1. **Add your requirements below** - Write them as you think of them, in any format
2. **Don't worry about structure** - We'll analyze and rephrase them together
3. **Include context** - Add any relevant background information, constraints, or priorities

---

## Initial Requirements

### Contexte du projet
Refonte d'un système de gestion comptable immobilier existant (9 scripts Python) en une application web moderne avec backend et frontend. Le système gère la comptabilité pour un LMNP (Location Meublée Non Professionnelle) en régime réel avec amortissements.

**Régime fiscal** : LMNP régime réel
- Pas de TVA (pas de gestion HT/TTC)
- Gestion des amortissements importante
- Comptabilité simplifiée mais complète

### Architecture cible
- **Backend** : FastAPI (Python)
- **Frontend** : Next.js (TypeScript/React)
- **Base de données** : SQLite (pour V1)
- **Pas d'authentification** en V1 (application single-user)

### Interface utilisateur - Dashboard avec onglets

#### 1. Onglet Transactions
- Visualiser toutes les transactions avec leurs classifications
- Ajouter/modifier les classifications pour les nouvelles transactions
- Modifier les classifications existantes si nécessaire
- Filtrage et recherche des transactions
- Affichage en tableau avec colonnes : Date, Montant, Nom, Solde, Level 1, Level 2, Level 3

#### 2. Onglet Tableau croisé dynamique
- Visualiser les transactions par classification
- Groupby par colonnes spécifiques (level 1, level 2, level 3, mois, année)
- Analyse des répartitions par catégories
- Totaux et sous-totaux

#### 3. Vue Bilan
- Affichage du bilan actif (immobilisations, actif circulant)
- Affichage du bilan passif (capitaux propres, dettes)
- Vérification de l'équilibre Actif = Passif
- Visualisation année par année

#### 4. Vue Amortissements
- Visualisation des amortissements par catégorie (meubles, travaux, construction, terrain)
- Répartition année par année
- Détail par type d'immobilisation

#### 5. Vue Cashflow
- Suivi du solde bancaire disponible
- Traçabilité pour vérifier qu'il ne manque pas de transactions
- Comparaison avec le compte bancaire réel
- Évolution du solde dans le temps

### Fonctionnalités de traitement (basées sur les 9 scripts existants)

#### F1 : Agrégation des transactions
- Upload de fichiers CSV bancaires multiples
- Détection automatique de l'encodage (UTF-8, Latin-1, ISO-8859-1, CP1252)
- Détection automatique du séparateur
- Normalisation des colonnes entre fichiers
- Conversion des dates au format DD/MM/YYYY
- Normalisation des montants (gestion virgules/points)
- Validation et filtrage des lignes invalides
- **Détection et prévention des doublons** lors de l'agrégation
- Tri chronologique
- Stockage dans la base de données

#### F2 : Enrichissement et catégorisation
- Ajout automatique des métadonnées temporelles (mois, année)
- Mapping intelligent des transactions vers les catégories
- Système de correspondance par préfixe
- Gestion des cas spéciaux (PRLV SEPA, VIR STRIPE)
- Catégorisation hiérarchique (level 1, level 2, level 3)
- Interface pour gérer le mapping (créer/modifier les correspondances)
- Rapport des transactions non mappées

#### F3 : Calcul des amortissements
- Calcul automatique des amortissements annuels
- Basé sur les acquisitions d'immobilisations
- Durées d'amortissement configurables par catégorie
- Convention 30/360 pour le calcul
- Répartition proportionnelle année par année
- Catégories : meubles, travaux, construction, terrain

#### F4 : Compte de résultat
- Génération automatique du compte de résultat annuel
- Produits d'exploitation (loyers, transferts de charges)
- Charges d'exploitation (charges, impôts, amortissements)
- Charges financières (intérêts, assurance crédit)
- Calcul automatique du résultat d'exploitation et résultat net
- Prorata temporel pour l'année en cours

#### F5 : Bilan actif
- Génération automatique de la partie actif
- Actif immobilisé (valeur nette avec amortissements)
- Détail des amortissements par type
- Actif circulant (liquidités bancaires)
- Calcul cumulé année par année

#### F6 : Bilan passif
- Génération automatique de la partie passif
- Capitaux propres (compte exploitant, résultat, report à nouveau, dépôts)
- Dettes (prêts cumulés - remboursements)
- Dettes fin d'année en cours (prorata)
- Validation de l'équilibre avec l'actif

#### F7 : Consolidation des états financiers
- Fusion automatique de tous les états financiers
- Formatage français (virgule décimale)
- Analyses de cohérence (différence Actif-Passif)
- Détection automatique de la dernière date

#### F8 : Analyse pivot (optionnel)
- Tableaux croisés dynamiques
- Analyses par catégories et années
- Totaux par niveau hiérarchique

#### F9 : Simulation budgétaire (optionnel)
- Projections basées sur des paramètres ajustables
- Scénarios de simulation

### Gestion des fichiers et données

#### Upload de fichiers
- Upload de fichiers CSV via l'interface web
- Support de plusieurs fichiers simultanés
- Prévisualisation avant traitement
- Validation du format
- Gestion des erreurs de format avec messages clairs
- Détection automatique des encodages et séparateurs

#### Prévention des doublons
- Détection des transactions déjà importées
- Critères de détection : Date + Montant + Nom (ou combinaison)
- Option pour ignorer ou remplacer les doublons
- Logs des transactions ignorées

#### Fichiers de configuration
- `mapping.xlsx` → Interface web pour gérer les correspondances
- `parametres.xlsx` → Interface web pour gérer les paramètres (durées amortissement, valeurs simulation)
- `tableau_ammort_taxes.xlsx` → Upload et gestion via interface

### Contraintes techniques

#### Base de données
- Stockage de toutes les transactions dans la DB
- Stockage des états financiers calculés
- Stockage des paramètres et mappings
- Historique des calculs

#### Performance
- Traitement efficace de gros volumes de transactions
- Calculs optimisés pour les états financiers
- Interface réactive

#### Gestion d'erreurs
- Logging détaillé des opérations
- Messages d'erreur clairs pour l'utilisateur
- Validation des données à chaque étape
- Archivage automatique en cas d'échec

### Workflow de test
- **Tester la web app après chaque fonctionnalité/étape**
- Chaque fonctionnalité doit être testable indépendamment
- Tests visuels dans l'interface
- Validation des calculs à chaque étape

---

## Notes & Context

### Ancien système
Le système actuel fonctionne avec 9 scripts Python qui traitent des fichiers CSV/Excel. Voir `DOCUMENTATION_FONCTIONNALITES.md` pour les détails complets de chaque script.

### Priorités
1. **V1** : Fonctionnalités core (F1-F7) avec interface de base
2. **V2** : Analyses avancées (F8-F9) et optimisations
3. **V3** : Multi-utilisateurs et authentification (si nécessaire)

### Format de données
- **Dates** : Format français DD/MM/YYYY
- **Nombres** : Virgule comme séparateur décimal
- **Séparateur CSV** : Point-virgule (;)
- **Encodage** : UTF-8 avec fallbacks multiples

### Points d'attention
- Vérification de la cohérence des bilans (Actif = Passif)
- Traçabilité complète des transactions
- Gestion des cas spéciaux (PRLV SEPA, VIR STRIPE)
- Calculs précis des amortissements (convention 30/360)
- Prorata temporel pour l'année en cours

---

**Next Step**: Once requirements are added, we'll analyze and rephrase them in `ANALYZED_REQUIREMENTS.md`

