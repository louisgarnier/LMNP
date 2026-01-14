"""
Script de test pour vérifier les calculs de simulation de crédit.

⚠️ Ce script teste les calculs PMT/IPMT/PPMT pour identifier les bugs.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import date

# Database path
DB_DIR = Path(__file__).parent.parent / "database"
DB_FILE = DB_DIR / "lmnp.db"

def yearfrac(date1_str, date2_str):
    """Équivalent YEARFRAC Excel (base 3 = année réelle/365)"""
    if not date1_str or not date2_str:
        return None
    
    d1 = date.fromisoformat(date1_str)
    d2 = date.fromisoformat(date2_str)
    
    diff_days = (d2 - d1).days
    return diff_days / 365

def PMT(rate, nper, pv, fv=0, type=0):
    """Calcul PMT équivalent Excel"""
    if rate == 0:
        return -(pv + fv) / nper
    
    pvif = (1 + rate) ** nper
    pmt = (pv * rate * pvif + fv * rate) / (pvif - 1)
    
    if type == 1:
        return pmt / (1 + rate)
    
    return pmt

def IPMT(rate, per, nper, pv, fv=0, type=0):
    """Calcul IPMT équivalent Excel (corrigé)"""
    if per < 1 or per > nper:
        return None
    
    pmt = PMT(rate, nper, pv, fv, type)
    
    # Calculer le solde restant dû au début de la période per
    # Le solde est toujours positif (on doit de l'argent)
    balance = abs(pv)
    
    if type == 1:
        # Ajuster pour paiement en début de période
        balance = balance * (1 + rate)
        # Soustraire le paiement immédiatement
        balance = balance - abs(pmt)
    
    # Calculer le solde jusqu'à la période per-1
    # À chaque période : solde augmente avec les intérêts, puis diminue avec le paiement
    for i in range(1, per):
        # Ajouter les intérêts
        balance = balance * (1 + rate)
        # Soustraire le paiement (pmt est négatif, donc on soustrait sa valeur absolue)
        balance = balance - abs(pmt)
        
        # Le solde ne peut pas être négatif
        if balance < 0:
            balance = 0
    
    # La part d'intérêt = solde au début de la période * taux
    balance_at_start = balance
    interest = balance_at_start * rate
    
    # Retourner avec le signe opposé à pv pour cohérence avec Excel
    return -interest if pv < 0 else interest

def PPMT(rate, per, nper, pv, fv=0, type=0):
    """Calcul PPMT équivalent Excel"""
    pmt = PMT(rate, nper, pv, fv, type)
    ipmt = IPMT(rate, per, nper, pv, fv, type)
    
    return pmt - ipmt

def main():
    """Affiche les données du crédit 'mois' et teste les calculs"""
    if not DB_FILE.exists():
        print(f"❌ Database file not found: {DB_FILE}")
        return
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("  TEST CALCULS SIMULATION CRÉDIT - CRÉDIT 'MOIS'")
    print("=" * 80)
    
    # Récupérer le crédit "mois"
    cursor.execute("""
        SELECT * FROM loan_configs 
        WHERE name LIKE '%mois%' OR name LIKE '%credit mois%'
        ORDER BY id DESC
        LIMIT 1
    """)
    
    config = cursor.fetchone()
    
    if not config:
        print("\n❌ Aucun crédit 'mois' trouvé")
        cursor.execute("SELECT name FROM loan_configs")
        all_configs = cursor.fetchall()
        print("\nCrédits disponibles:")
        for c in all_configs:
            print(f"  - {c['name']}")
        conn.close()
        return
    
    print("\n📊 DONNÉES DU CRÉDIT EN BASE:")
    print("-" * 80)
    print(f"  ID: {config['id']}")
    print(f"  Nom: {config['name']}")
    print(f"  Crédit accordé (€): {config['credit_amount']:,.2f}")
    print(f"  Taux fixe (%): {config['interest_rate']}")
    print(f"  Durée emprunt (années): {config['duration_years']}")
    print(f"  Décalage initial (mois): {config['initial_deferral_months']}")
    print(f"  Date d'emprunt: {config['loan_start_date']}")
    print(f"  Date de fin prévisionnelle: {config['loan_end_date']}")
    print(f"  Assurance mensuelle (€): {config['monthly_insurance'] or 0}")
    
    # Calculer la durée crédit (années) incluant différé
    print("\n📐 CALCULS DE DURÉE:")
    print("-" * 80)
    
    duration_years_including_deferral = None
    
    if config['loan_start_date'] and config['loan_end_date']:
        yearfrac_value = yearfrac(config['loan_start_date'], config['loan_end_date'])
        if yearfrac_value:
            duration_years_including_deferral = yearfrac_value - (config['initial_deferral_months'] / 12)
            print(f"  YEARFRAC(date_start, date_end): {yearfrac_value:.4f} ans")
            print(f"  Durée crédit (années) incluant différé: {duration_years_including_deferral:.4f} ans")
        else:
            print("  ⚠️ Impossible de calculer YEARFRAC")
    else:
        duration_years_including_deferral = config['duration_years'] + (config['initial_deferral_months'] / 12)
        print(f"  Durée crédit (années) incluant différé (sans dates): {duration_years_including_deferral:.4f} ans")
    
    if duration_years_including_deferral is None or duration_years_including_deferral <= 0:
        print("  ❌ Durée invalide!")
        conn.close()
        return
    
    # Paramètres pour les calculs
    monthly_rate = (config['interest_rate'] / 100) / 12
    total_months = duration_years_including_deferral * 12
    loan_amount = -config['credit_amount']  # Négatif pour PMT
    insurance = config['monthly_insurance'] or 0
    
    print("\n🔢 PARAMÈTRES POUR LES CALCULS:")
    print("-" * 80)
    print(f"  Taux mensuel: {monthly_rate:.8f} ({config['interest_rate']}% / 12)")
    print(f"  Durée totale (mois): {total_months:.0f}")
    print(f"  Montant pour PMT (négatif): {loan_amount:,.2f}")
    print(f"  Assurance mensuelle: {insurance:,.2f} €")
    
    # Tester les calculs pour les mensualités 1, 50, 100, 150, 200
    print("\n📊 RÉSULTATS DES CALCULS:")
    print("-" * 80)
    print(f"{'Mens.':<8} {'PMT':<12} {'IPMT':<12} {'PPMT':<12} {'Assur.':<10} {'Total/mois':<12} {'Total/an':<12} {'⚠️':<5}")
    print("-" * 80)
    
    months_to_test = [1, 50, 100, 150, 200]
    
    for month in months_to_test:
        if month > total_months:
            print(f"{month:<8} {'N/A (hors durée)':<60}")
            continue
        
        try:
            pmt = abs(PMT(monthly_rate, total_months, loan_amount))
            ipmt = abs(IPMT(monthly_rate, month, total_months, loan_amount))
            ppmt = abs(PPMT(monthly_rate, month, total_months, loan_amount))
            total_per_month = insurance + ipmt + ppmt
            total_per_year = total_per_month * 12
            
            # Vérifier les incohérences
            warnings = []
            if ipmt > pmt:
                warnings.append("IPMT>PMT")
            if ipmt + ppmt > pmt * 1.01:  # Tolérance 1%
                warnings.append("IPMT+PPMT≠PMT")
            if total_per_month < 0:
                warnings.append("Total<0")
            
            warning_str = " ⚠️" if warnings else ""
            
            print(f"{month:<8} {pmt:>11,.2f} {ipmt:>11,.2f} {ppmt:>11,.2f} {insurance:>9,.2f} {total_per_month:>11,.2f} {total_per_year:>11,.2f} {warning_str}")
            
            if warnings:
                print(f"         ⚠️ ALERTES: {', '.join(warnings)}")
                print(f"         Détails: PMT={pmt:.2f}, IPMT={ipmt:.2f}, PPMT={ppmt:.2f}, IPMT+PPMT={ipmt+ppmt:.2f}")
        
        except Exception as e:
            print(f"{month:<8} ❌ ERREUR: {e}")
    
    # Test détaillé pour la mensualité 100
    print("\n🔍 ANALYSE DÉTAILLÉE - MENSUALITÉ 100:")
    print("-" * 80)
    month = 100
    if month <= total_months:
        try:
            pmt = PMT(monthly_rate, total_months, loan_amount)
            ipmt = IPMT(monthly_rate, month, total_months, loan_amount)
            ppmt = PPMT(monthly_rate, month, total_months, loan_amount)
            
            print(f"  PMT(rate={monthly_rate:.8f}, nper={total_months:.0f}, pv={loan_amount:,.2f})")
            print(f"    = {pmt:,.2f} (abs: {abs(pmt):,.2f})")
            print(f"\n  IPMT(rate={monthly_rate:.8f}, per={month}, nper={total_months:.0f}, pv={loan_amount:,.2f})")
            print(f"    = {ipmt:,.2f} (abs: {abs(ipmt):,.2f})")
            print(f"\n  PPMT(rate={monthly_rate:.8f}, per={month}, nper={total_months:.0f}, pv={loan_amount:,.2f})")
            print(f"    = {ppmt:,.2f} (abs: {abs(ppmt):,.2f})")
            print(f"\n  Vérification: IPMT + PPMT = {ipmt + ppmt:,.2f} (devrait être ≈ {pmt:,.2f})")
            print(f"  Différence: {abs((ipmt + ppmt) - pmt):,.2f}")
            
            # Calculer le solde restant dû manuellement (corrigé)
            print(f"\n  Calcul manuel du solde restant dû (corrigé):")
            balance = abs(loan_amount)
            for i in range(1, month):
                balance = balance * (1 + monthly_rate) - abs(pmt)
                if balance < 0:
                    balance = 0
            print(f"    Solde au début période {month}: {balance:,.2f}")
            print(f"    Intérêt période {month}: {balance * monthly_rate:,.2f}")
            print(f"    Capital période {month}: {abs(pmt) - (balance * monthly_rate):,.2f}")
            
        except Exception as e:
            print(f"  ❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ⚠️ Mensualité {month} hors durée (durée totale: {total_months:.0f} mois)")
    
    conn.close()
    print("\n" + "=" * 80)
    print("  FIN DU TEST")
    print("=" * 80)

if __name__ == "__main__":
    main()
