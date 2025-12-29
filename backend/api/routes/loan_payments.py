"""
API routes for loan payments (mensualités de crédit).

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import pandas as pd
import io
from pathlib import Path

from backend.database import get_db
from backend.database.models import LoanPayment
from backend.api.models import (
    LoanPaymentCreate,
    LoanPaymentUpdate,
    LoanPaymentResponse,
    LoanPaymentListResponse,
    LoanPaymentPreviewResponse,
    LoanPaymentImportResponse
)

router = APIRouter()


@router.get("/loan-payments", response_model=LoanPaymentListResponse)
async def get_loan_payments(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    loan_name: Optional[str] = Query(None, description="Filtrer par nom de prêt"),
    start_date: Optional[date] = Query(None, description="Date de début (inclusive)"),
    end_date: Optional[date] = Query(None, description="Date de fin (inclusive)"),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des mensualités de crédit avec filtres optionnels.
    
    Args:
        skip: Nombre d'éléments à sauter (pagination)
        limit: Nombre d'éléments à retourner
        loan_name: Filtrer par nom de prêt
        start_date: Filtrer par date de début
        end_date: Filtrer par date de fin
        db: Session de base de données
    
    Returns:
        Liste des mensualités avec total
    """
    query = db.query(LoanPayment)
    
    # Appliquer les filtres
    if loan_name:
        query = query.filter(LoanPayment.loan_name == loan_name)
    if start_date:
        query = query.filter(LoanPayment.date >= start_date)
    if end_date:
        query = query.filter(LoanPayment.date <= end_date)
    
    # Compter le total
    total = query.count()
    
    # Pagination et tri
    payments = query.order_by(desc(LoanPayment.date)).offset(skip).limit(limit).all()
    
    return LoanPaymentListResponse(
        payments=[LoanPaymentResponse.model_validate(p) for p in payments],
        total=total
    )


@router.get("/loan-payments/{payment_id}", response_model=LoanPaymentResponse)
async def get_loan_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère une mensualité par son ID.
    
    Args:
        payment_id: ID de la mensualité
        db: Session de base de données
    
    Returns:
        Mensualité trouvée
    
    Raises:
        HTTPException: Si la mensualité n'existe pas
    """
    payment = db.query(LoanPayment).filter(LoanPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail=f"Mensualité avec ID {payment_id} non trouvée")
    
    return LoanPaymentResponse.model_validate(payment)


@router.post("/loan-payments", response_model=LoanPaymentResponse)
async def create_loan_payment(
    payment_data: LoanPaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle mensualité.
    
    Args:
        payment_data: Données de la mensualité
        db: Session de base de données
    
    Returns:
        Mensualité créée
    """
    # Valider que capital + interest + insurance = total
    calculated_total = payment_data.capital + payment_data.interest + payment_data.insurance
    if abs(calculated_total - payment_data.total) > 0.01:  # Tolérance de 0.01
        # Corriger automatiquement
        payment_data.total = calculated_total
    
    payment = LoanPayment(
        date=payment_data.date,
        capital=payment_data.capital,
        interest=payment_data.interest,
        insurance=payment_data.insurance,
        total=payment_data.total,
        loan_name=payment_data.loan_name
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return LoanPaymentResponse.model_validate(payment)


@router.put("/loan-payments/{payment_id}", response_model=LoanPaymentResponse)
async def update_loan_payment(
    payment_id: int,
    payment_data: LoanPaymentUpdate,
    db: Session = Depends(get_db)
):
    """
    Met à jour une mensualité existante.
    
    Args:
        payment_id: ID de la mensualité
        payment_data: Données à mettre à jour
        db: Session de base de données
    
    Returns:
        Mensualité mise à jour
    
    Raises:
        HTTPException: Si la mensualité n'existe pas
    """
    payment = db.query(LoanPayment).filter(LoanPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail=f"Mensualité avec ID {payment_id} non trouvée")
    
    # Mettre à jour les champs fournis
    if payment_data.date is not None:
        payment.date = payment_data.date
    if payment_data.capital is not None:
        payment.capital = payment_data.capital
    if payment_data.interest is not None:
        payment.interest = payment_data.interest
    if payment_data.insurance is not None:
        payment.insurance = payment_data.insurance
    if payment_data.loan_name is not None:
        payment.loan_name = payment_data.loan_name
    
    # Recalculer le total si nécessaire
    if payment_data.total is not None:
        payment.total = payment_data.total
    else:
        # Recalculer automatiquement si capital, interest ou insurance ont changé
        payment.total = payment.capital + payment.interest + payment.insurance
    
    # Valider que capital + interest + insurance = total
    calculated_total = payment.capital + payment.interest + payment.insurance
    if abs(calculated_total - payment.total) > 0.01:
        payment.total = calculated_total
    
    db.commit()
    db.refresh(payment)
    
    return LoanPaymentResponse.model_validate(payment)


@router.delete("/loan-payments/{payment_id}")
async def delete_loan_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprime une mensualité.
    
    Args:
        payment_id: ID de la mensualité
        db: Session de base de données
    
    Raises:
        HTTPException: Si la mensualité n'existe pas
    """
    payment = db.query(LoanPayment).filter(LoanPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail=f"Mensualité avec ID {payment_id} non trouvée")
    
    db.delete(payment)
    db.commit()
    
    return {"message": f"Mensualité {payment_id} supprimée avec succès"}


@router.post("/loan-payments/preview", response_model=LoanPaymentPreviewResponse)
async def preview_loan_payment_file(
    file: UploadFile = File(...),
    loan_name: str = Query("Prêt principal", description="Nom du prêt"),
    db: Session = Depends(get_db)
):
    """
    Prévisualise un fichier Excel de mensualités et détecte la structure.
    
    Structure attendue :
    - Colonne 'annee' : types ("capital", "interets", "assurance cred", "total")
    - Colonnes années : 2021, 2022, 2023, etc.
    
    Args:
        file: Fichier Excel (.xlsx ou .xls) à analyser
        loan_name: Nom du prêt (par défaut "Prêt principal")
        db: Session de base de données
    
    Returns:
        Preview avec années détectées, montants, avertissements
    """
    # Vérifier l'extension du fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls')):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un fichier Excel (.xlsx ou .xls)"
        )
    
    # Lire le fichier
    file_content = await file.read()
    
    try:
        # Lire Excel avec pandas
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl' if filename_lower.endswith('.xlsx') else None)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Le fichier Excel est vide")
        
        # Vérifier que la colonne 'annee' existe
        if 'annee' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Colonne 'annee' non trouvée. Le fichier doit contenir une colonne 'annee' avec les types (capital, interets, assurance cred, total)"
            )
        
        # Extraire les années depuis les colonnes (sauf 'annee')
        detected_years = []
        warnings = []
        validation_errors = []
        
        for col in df.columns:
            if col == 'annee':
                continue
            try:
                year = int(col)
                if 1900 <= year <= 2100:  # Plage raisonnable
                    detected_years.append(year)
                else:
                    warnings.append(f"Colonne '{col}' semble être une année invalide (hors plage 1900-2100)")
            except (ValueError, TypeError):
                warnings.append(f"Colonne '{col}' ne semble pas être une année valide (ignorée)")
        
        detected_years.sort()
        
        if not detected_years:
            raise HTTPException(
                status_code=400,
                detail="Aucune année valide détectée dans les colonnes du fichier"
            )
        
        # Vérifier que les types attendus sont présents
        expected_types = ['capital', 'interets', 'assurance cred', 'total']
        annee_values = df['annee'].astype(str).str.lower().str.strip().tolist()
        found_types = []
        for expected_type in expected_types:
            found = False
            for annee_val in annee_values:
                if expected_type.lower() in annee_val.lower():
                    found_types.append(annee_val)
                    found = True
                    break
            if not found:
                validation_errors.append(f"Type '{expected_type}' non trouvé dans la colonne 'annee'")
        
        # Parser les données pour le preview
        preview_data = []
        stats = {
            "detected_years_count": len(detected_years),
            "years_range": f"{min(detected_years)}-{max(detected_years)}" if detected_years else None,
            "types_found": found_types
        }
        
        # Pour chaque année, extraire les montants
        for year in detected_years[:10]:  # Limiter à 10 années pour le preview
            year_data = {
                "annee": year,
                "date": f"01/01/{year}",
                "capital": None,
                "interets": None,
                "assurance_cred": None,
                "total": None
            }
            
            # Chercher les valeurs pour cette année
            for idx, row in df.iterrows():
                annee_val = str(row['annee']).lower().strip()
                year_col_value = row.get(year, None)
                
                if pd.notna(year_col_value):
                    if 'capital' in annee_val:
                        year_data["capital"] = float(year_col_value) if pd.notna(year_col_value) else 0.0
                    elif 'interet' in annee_val:
                        year_data["interets"] = float(year_col_value) if pd.notna(year_col_value) else 0.0
                    elif 'assurance' in annee_val:
                        year_data["assurance_cred"] = float(year_col_value) if pd.notna(year_col_value) else 0.0
                    elif 'total' in annee_val:
                        year_data["total"] = float(year_col_value) if pd.notna(year_col_value) else 0.0
            
            preview_data.append(year_data)
        
        # Compter les mensualités existantes pour ce loan_name
        existing_payments_count = db.query(LoanPayment).filter(LoanPayment.loan_name == loan_name).count()
        
        if existing_payments_count > 0:
            warnings.append(f"⚠️ {existing_payments_count} mensualité(s) existante(s) pour '{loan_name}'. Elles seront supprimées lors de l'import.")
        
        return LoanPaymentPreviewResponse(
            filename=file.filename,
            total_rows=len(df),
            detected_years=detected_years,
            preview=preview_data,
            validation_errors=validation_errors,
            warnings=warnings,
            stats=stats,
            existing_payments_count=existing_payments_count
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Le fichier Excel est vide ou invalide")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de la lecture du fichier Excel: {str(e)}"
        )


@router.post("/loan-payments/import", response_model=LoanPaymentImportResponse)
async def import_loan_payment_file(
    file: UploadFile = File(...),
    loan_name: str = Query("Prêt principal", description="Nom du prêt"),
    confirm_replace: bool = Query(False, description="Confirmer le remplacement des données existantes"),
    db: Session = Depends(get_db)
):
    """
    Importe un fichier Excel de mensualités dans la base de données.
    
    Structure attendue :
    - Colonne 'annee' : types ("capital", "interets", "assurance cred", "total")
    - Colonnes années : 2021, 2022, 2023, etc.
    
    Pour chaque année, crée 1 enregistrement avec date = 01/01/année.
    
    Args:
        file: Fichier Excel (.xlsx ou .xls) à importer
        loan_name: Nom du prêt (par défaut "Prêt principal")
        confirm_replace: Confirmer le remplacement des données existantes
        db: Session de base de données
    
    Returns:
        Statistiques d'import
    """
    # Vérifier l'extension du fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls')):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un fichier Excel (.xlsx ou .xls)"
        )
    
    # Vérifier s'il y a des données existantes
    existing_payments = db.query(LoanPayment).filter(LoanPayment.loan_name == loan_name).all()
    if existing_payments and not confirm_replace:
        raise HTTPException(
            status_code=400,
            detail=f"⚠️ {len(existing_payments)} mensualité(s) existante(s) pour '{loan_name}'. Utilisez confirm_replace=true pour les remplacer."
        )
    
    # Lire le fichier
    file_content = await file.read()
    
    try:
        # Sauvegarder le fichier dans data/input/trades/ (archive)
        trades_dir = Path(__file__).parent.parent.parent / "data" / "input" / "trades"
        trades_dir.mkdir(parents=True, exist_ok=True)
        file_path = trades_dir / file.filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Lire Excel avec pandas
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl' if filename_lower.endswith('.xlsx') else None)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Le fichier Excel est vide")
        
        # Vérifier que la colonne 'annee' existe
        if 'annee' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Colonne 'annee' non trouvée"
            )
        
        # Supprimer les mensualités existantes si confirmé
        if existing_payments and confirm_replace:
            db.query(LoanPayment).filter(LoanPayment.loan_name == loan_name).delete()
            db.commit()
        
        # Extraire les années depuis les colonnes
        detected_years = []
        for col in df.columns:
            if col == 'annee':
                continue
            try:
                year = int(col)
                if 1900 <= year <= 2100:
                    detected_years.append(year)
            except (ValueError, TypeError):
                pass
        
        detected_years.sort()
        
        if not detected_years:
            raise HTTPException(
                status_code=400,
                detail="Aucune année valide détectée dans les colonnes du fichier"
            )
        
        # Parser et créer les enregistrements
        imported_count = 0
        errors = []
        warnings = []
        
        for year in detected_years:
            try:
                capital = 0.0
                interest = 0.0
                insurance = 0.0
                total = 0.0
                
                # Chercher les valeurs pour cette année
                for idx, row in df.iterrows():
                    annee_val = str(row['annee']).lower().strip()
                    year_col_value = row.get(year, None)
                    
                    if pd.notna(year_col_value):
                        value = float(year_col_value)
                        if 'capital' in annee_val:
                            capital = value
                        elif 'interet' in annee_val:
                            interest = value
                        elif 'assurance' in annee_val:
                            insurance = value
                        elif 'total' in annee_val:
                            total = value
                
                # Si toutes les valeurs sont à 0, créer quand même l'enregistrement (année sans données)
                # Valider que capital + interest + insurance = total
                calculated_total = capital + interest + insurance
                if abs(calculated_total - total) > 0.01:
                    # Corriger automatiquement
                    total = calculated_total
                    warnings.append(f"Année {year}: Total corrigé automatiquement ({calculated_total:.2f})")
                
                # Créer l'enregistrement
                payment = LoanPayment(
                    date=date(year, 1, 1),  # 01/01/année
                    capital=capital,
                    interest=interest,
                    insurance=insurance,
                    total=total,
                    loan_name=loan_name
                )
                
                db.add(payment)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Erreur pour l'année {year}: {str(e)}")
        
        db.commit()
        
        return LoanPaymentImportResponse(
            message=f"Import réussi: {imported_count} mensualité(s) importée(s)",
            imported_count=imported_count,
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de l'import: {str(e)}"
        )

