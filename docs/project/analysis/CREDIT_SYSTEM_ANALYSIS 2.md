# État des lieux : Système de gestion des Crédits

**Date** : 02/02/2026  
**Contexte** : Analyse suite au déséquilibre du bilan pour la propriété "mars colloc"

---

## 📋 Vue d'ensemble

L'onglet "Crédit" fait partie de l'onglet "États financiers" et permet de gérer :
- Les **configurations de crédit** (LoanConfig)
- Les **échéanciers de paiement** mensuels (LoanPayment)
- L'impact sur le **Compte de Résultat** (coût de financement)
- L'impact sur le **Bilan** (capital restant dû)

---

## 🗄️ Modèles de données

### 1. `LoanConfig` (Configurations de crédit)

**Table** : `loan_configs`

```python
class LoanConfig(Base):
    id: int
    property_id: int  # ForeignKey avec ON DELETE CASCADE
    name: str  # Ex: "Prêt principal", "Prêt construction"
    credit_amount: float  # Montant du crédit accordé (auto-calculé depuis LoanPayment)
    interest_rate: float  # Taux fixe hors assurance en %
    duration_years: int  # Durée de l'emprunt en années
    initial_deferral_months: int  # Décalage initial en mois (default: 0)
    loan_start_date: date  # Date d'emprunt (nullable)
    loan_end_date: date  # Date de fin prévisionnelle (nullable)
    monthly_insurance: float  # Assurance mensuelle en € (default: 0.0)
    simulation_months: str  # JSON array des mensualités personnalisées (nullable)
```

**Contraintes** :
- `name` unique par propriété (`idx_loan_config_property_name`)
- Un crédit appartient à **une seule propriété**

**Important** :
- `credit_amount` est **automatiquement mis à jour** lorsque des LoanPayments sont créés/modifiés
- Il représente la **somme de tous les LoanPayment.capital** pour ce crédit

### 2. `LoanPayment` (Mensualités)

**Table** : `loan_payments`

```python
class LoanPayment(Base):
    id: int
    property_id: int  # ForeignKey avec ON DELETE CASCADE
    date: date  # Date de la mensualité (généralement 01/01/année)
    capital: float  # Montant du capital remboursé
    interest: float  # Montant des intérêts
    insurance: float  # Montant de l'assurance crédit
    total: float  # Total = capital + interest + insurance
    loan_name: str  # Nom du prêt (référence à LoanConfig.name)
```

**Contraintes** :
- `(loan_name, date)` unique (`idx_loan_payment_loan_name_date`)
- Une mensualité appartient à **une seule propriété**

**Validation automatique** :
- Si `capital + interest + insurance ≠ total`, le système corrige automatiquement `total`

---

## 🔧 Fonctionnement Backend

### A. Création / Modification de LoanPayment

**Endpoint** : `POST /api/loan-payments`

**Workflow** :
1. Validation de `property_id`
2. Création du `LoanPayment`
3. **Mise à jour automatique de `LoanConfig.credit_amount`** :
   ```python
   # Somme de tous les LoanPayment.capital pour ce loan_name et property_id
   total_capital = sum(LoanPayment.capital)
   LoanConfig.credit_amount = total_capital
   ```
4. **Invalidation des comptes de résultat** pour l'année du payment
5. **Invalidation du bilan** pour l'année du payment

### B. Import d'échéancier Excel

**Endpoint** : `POST /api/loan-payments/import`

**Format attendu** :
```
| Année | Capital | Intérêts | Assurance | Total (optionnel) |
|-------|---------|----------|-----------|-------------------|
| 2025  | 7143.70 | 1455.03  | 216.00    | 8814.73          |
| 2026  | 7424.18 | 5523.26  | 612.00    | 13559.44         |
```

**Workflow** :
1. Lecture du fichier Excel (`.xlsx`)
2. Parsing des colonnes : Capital, Intérêts, Assurance, Total (optionnel), Année
3. Pour chaque ligne valide :
   - Création d'un `LoanPayment` avec `date = 01/01/année`
   - `total = Capital + Intérêts + Assurance` (calculé si non fourni)
4. **Mise à jour automatique de `LoanConfig.credit_amount`**
5. **Invalidation des comptes de résultat et bilans** pour toutes les années importées

### C. Calcul du coût de financement (Compte de Résultat)

**Service** : `get_cout_financement(db, year, property_id)`

**Logique** :
```python
# 1. Récupérer les crédits configurés pour la propriété
loan_configs = LoanConfig.filter(property_id=property_id)
loan_names = [config.name for config in loan_configs]

# 2. Récupérer les payments pour l'année
payments = LoanPayment.filter(
    property_id=property_id,
    date >= 01/01/year,
    date <= 31/12/year,
    loan_name IN loan_names
)

# 3. Sommer intérêts + assurance
total_cost = sum(payment.interest + payment.insurance for payment in payments)
```

**Résultat** : Montant total des intérêts + assurances pour l'année (positif, charge)

### D. Calcul du capital restant dû (Bilan)

**Service** : `calculate_capital_restant_du(db, year, property_id)`

**Logique** :
```python
# 1. Récupérer le montant du crédit depuis les TRANSACTIONS
#    (level_1 = "Dettes financières (emprunt bancaire)")
credit_amount = abs(sum(Transaction.quantite) WHERE 
    property_id=property_id AND
    level_1="Dettes financières (emprunt bancaire)" AND
    date <= 31/12/year
)

# Si aucune transaction trouvée, retourner 0
if credit_amount == 0:
    return 0.0

# 2. Récupérer les crédits actifs pour la propriété
active_loans = LoanConfig.filter(
    property_id=property_id,
    loan_start_date IS NULL OR loan_start_date <= 31/12/year
)
active_loan_names = [loan.name for loan in active_loans]

# 3. Calculer le capital remboursé
capital_paid = sum(LoanPayment.capital) WHERE
    property_id=property_id AND
    date <= 31/12/year AND
    loan_name IN active_loan_names

# 4. Capital restant dû = Crédit initial - Capital remboursé
remaining = credit_amount - capital_paid
return max(0.0, remaining)
```

**⚠️ IMPORTANT** :
- Le montant du crédit vient des **TRANSACTIONS**, pas de `LoanConfig.credit_amount`
- Nécessite une transaction avec `level_1 = "Dettes financières (emprunt bancaire)"`
- Si aucune transaction n'est trouvée, le capital restant dû est **0** (même si des LoanPayments existent)

---

## 🖥️ Fonctionnement Frontend

### Page principale

**Emplacement** : `frontend/app/dashboard/etats-financiers/page.tsx`

**Onglets** :
1. Compte de Résultat
2. Bilan
3. **Crédit** ← Notre sujet
4. Liasse fiscale

### Composants de l'onglet Crédit

#### 1. `LoanConfigCard` / `LoanConfigSingleCard`
- Affiche la configuration du crédit
- Permet de créer/modifier un `LoanConfig`
- Champs : nom, montant, taux, durée, dates, assurance mensuelle

#### 2. `LoanPaymentFileUpload`
- Upload d'un fichier Excel avec l'échéancier
- Format : Année, Capital, Intérêts, Assurance, Total

#### 3. `LoanPaymentTable`
- Affiche les mensualités enregistrées
- Colonnes : Date, Capital, Intérêts, Assurance, Total
- Permet de filtrer par crédit (`loan_name`)

### Workflow utilisateur

1. **Créer un LoanConfig** (configuration de crédit)
   - Renseigner : nom, taux, durée, dates, assurance
   - `credit_amount` est initialement à 0

2. **Importer l'échéancier Excel**
   - Upload du fichier avec les années/capital/intérêts/assurance
   - Le système crée automatiquement les `LoanPayment`
   - `LoanConfig.credit_amount` est mis à jour automatiquement

3. **Vérifier les données**
   - Consulter le tableau des mensualités
   - Vérifier que `credit_amount` correspond au total capital

---

## 🔍 Problèmes identifiés (cas "mars colloc")

### 1. **Décalage entre LoanConfig et Transactions**

**Situation actuelle** :
- `LoanConfig.credit_amount` = Somme des `LoanPayment.capital`
- **Capital restant dû (Bilan)** = `Transactions level_1="Dettes financières"` - `LoanPayment.capital`

**Problème** :
- Si les **transactions bancaires** (débit du crédit) ne sont pas mappées correctement, le capital restant dû sera **incorrect**
- Le système peut avoir des `LoanPayments` sans transactions correspondantes, ou vice-versa

**Exemple pour "mars colloc"** :
```
LoanConfig.credit_amount = 200 000 € (calculé depuis LoanPayments)
Transactions "Dettes financières" = 183 223 € (montant réel débité)
→ Décalage de 16 777 €
```

### 2. **Amortissements cumulés négatifs dans l'ACTIF**

**Observation** :
```
ACTIF:
  Amortissements cumulés: -3,440.97 €
  Immobilisations: 201,722.29 €
  → Actif net = 198,281.32 € (mais affiché séparément)
```

**Problème comptable** :
- Les "Amortissements cumulés" devraient :
  - Option A : Être **soustraits** des immobilisations (Actif net)
  - Option B : Être en **PASSIF** (compte de contrepartie)
- Actuellement, ils sont en ACTIF avec un montant négatif, ce qui crée un déséquilibre

### 3. **Compte de Résultat incomplet**

**Observation** :
```
Produits d'exploitation : 0.00 €
Charges d'exploitation : 0.00 €
Amortissements : -3,440.97 €
Coût de financement : 1,455.03 €
→ Résultat net : -22,206.91 €
```

**Problème** :
- Aucun **loyer** (produit) mappé
- Aucune **charge** (gestion, travaux, taxes) mappée
- Le résultat est uniquement composé d'amortissements + intérêts

---

## 💡 Recommandations

### 1. **Vérifier les mappings de transactions**

Pour "mars colloc", vérifier :
- [ ] Transactions avec `level_1 = "Dettes financières (emprunt bancaire)"` existent
- [ ] Transactions de **loyers** sont mappées vers `CompteResultatMapping` (produits)
- [ ] Transactions de **charges** sont mappées vers `CompteResultatMapping` (charges)

### 2. **Corriger la configuration du Bilan**

Pour les "Amortissements cumulés" :
- [ ] Option A : Les configurer pour être **soustraits** des immobilisations
- [ ] Option B : Les déplacer en **PASSIF** dans `BilanMapping`

### 3. **Valider la cohérence LoanConfig ↔ Transactions**

Créer un outil/script pour :
- [ ] Comparer `LoanConfig.credit_amount` vs Transactions "Dettes financières"
- [ ] Alerter si un écart > seuil (ex: 1%)
- [ ] Proposer une synchronisation

### 4. **Améliorer le calcul du capital restant dû**

Options :
- **Option A** : Continuer à utiliser les Transactions comme source de vérité
- **Option B** : Utiliser `LoanConfig.credit_amount` si aucune transaction n'est trouvée (fallback)
- **Option C** : Obliger l'utilisateur à créer une transaction "Dettes financières" pour chaque crédit

---

## 📊 Résumé des flux de données

```
┌─────────────────┐
│ LoanConfig      │
│ (Configuration) │
│                 │
│ credit_amount ← ┼──────────────┐
└─────────────────┘              │
                                 │ Auto-update
┌─────────────────┐              │
│ LoanPayment     │              │
│ (Mensualités)   │──────────────┘
│                 │
│ capital         │──────┐
│ interest        │      │
│ insurance       │      │
└─────────────────┘      │
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌─────────────────┐            ┌─────────────────┐
│ Compte Résultat │            │ Bilan           │
│                 │            │                 │
│ Coût financement│            │ Capital restant │
│ = interest +    │            │ = Transactions  │
│   insurance     │            │   - capital     │
└─────────────────┘            └─────────────────┘
                                        ▲
                                        │
                                        │ Source
                               ┌────────┴────────┐
                               │ Transaction     │
                               │ level_1="Dettes │
                               │ financières"    │
                               └─────────────────┘
```

---

## 🎯 Prochaines étapes

Pour résoudre le déséquilibre du bilan de "mars colloc" :

1. **Diagnostic précis** :
   - Lister les LoanConfigs pour la propriété
   - Lister les Transactions "Dettes financières"
   - Comparer les montants

2. **Correction des mappings** :
   - Configurer les BilanMappings (Amortissements cumulés)
   - Configurer les CompteResultatMappings (Produits/Charges)

3. **Validation** :
   - Re-calculer le bilan
   - Vérifier l'équilibre Actif/Passif

---

**Document créé pour faciliter la prise de décision sur les modifications à apporter au système de gestion des crédits.**
