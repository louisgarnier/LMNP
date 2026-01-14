"""
API routes for loan payments.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional
from datetime import date, datetime
import io
import pandas as pd
import numpy as np

from backend.database import get_db
from backend.database.models import LoanPayment
from backend.api.models import (
    LoanPaymentCreate,
    LoanPaymentUpdate,
    LoanPaymentResponse,
    LoanPaymentListResponse
)

router = APIRouter()


@router.get("/loan-payments", response_model=LoanPaymentListResponse)
async def get_loan_payments(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    start_date: Optional[date] = Query(None, description="Date de début (filtre)"),
    end_date: Optional[date] = Query(None, description="Date de fin (filtre)"),
    loan_name: Optional[str] = Query(None, description="Filtre par nom de prêt"),
    sort_by: Optional[str] = Query("date", description="Colonne de tri (date, loan_name)"),
    sort_direction: Optional[str] = Query("desc", description="Direction du tri (asc, desc)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des mensualités de crédit.
    
    - **skip**: Nombre d'éléments à sauter (pagination)
    - **limit**: Nombre d'éléments à retourner (max 1000)
    - **start_date**: Filtrer par date de début (optionnel)
    - **end_date**: Filtrer par date de fin (optionnel)
    - **loan_name**: Filtrer par nom de prêt (optionnel)
    - **sort_by**: Colonne de tri (date, loan_name)
    - **sort_direction**: Direction du tri (asc, desc)
    """
    query = db.query(LoanPayment)
    
    # Filtres par date
    if start_date:
        query = query.filter(LoanPayment.date >= start_date)
    if end_date:
        query = query.filter(LoanPayment.date <= end_date)
    
    # Filtre par nom de prêt
    if loan_name:
        query = query.filter(LoanPayment.loan_name == loan_name)
    
    # Compter le total (avant tri)
    total = query.count()
    
    # Tri
    if sort_by:
        sort_dir = sort_direction.lower() if sort_direction else "desc"
        if sort_dir not in ["asc", "desc"]:
            sort_dir = "desc"
        
        if sort_by == "date":
            order_col = LoanPayment.date
        elif sort_by == "loan_name":
            order_col = LoanPayment.loan_name
        else:
            order_col = LoanPayment.date
            sort_dir = "desc"
        
        if sort_dir == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))
    else:
        query = query.order_by(desc(LoanPayment.date))
    
    # Pagination
    payments = query.offset(skip).limit(limit).all()
    
    # Convertir en réponse
    payment_responses = [
        LoanPaymentResponse(
            id=p.id,
            date=p.date,
            capital=p.capital,
            interest=p.interest,
            insurance=p.insurance,
            total=p.total,
            loan_name=p.loan_name,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in payments
    ]
    
    return LoanPaymentListResponse(
        items=payment_responses,
        total=total,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.post("/loan-payments", response_model=LoanPaymentResponse, status_code=201)
async def create_loan_payment(
    payment: LoanPaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Créer une nouvelle mensualité de crédit.
    """
    # Validation : vérifier que capital + interest + insurance = total
    calculated_total = payment.capital + payment.interest + payment.insurance
    if abs(calculated_total - payment.total) > 0.01:  # Tolérance de 1 centime
        # Corriger automatiquement
        payment.total = calculated_total
    
    db_payment = LoanPayment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    # Invalider les comptes de résultat pour l'année du payment
    try:
        from backend.api.services.compte_resultat_service import invalidate_compte_resultat_for_year
        invalidate_compte_resultat_for_year(db, db_payment.date.year)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [create_loan_payment] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
    
    return LoanPaymentResponse(
        id=db_payment.id,
        date=db_payment.date,
        capital=db_payment.capital,
        interest=db_payment.interest,
        insurance=db_payment.insurance,
        total=db_payment.total,
        loan_name=db_payment.loan_name,
        created_at=db_payment.created_at,
        updated_at=db_payment.updated_at
    )


@router.get("/loan-payments/{payment_id}", response_model=LoanPaymentResponse)
async def get_loan_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupérer une mensualité par son ID.
    """
    payment = db.query(LoanPayment).filter(LoanPayment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Mensualité non trouvée")
    
    return LoanPaymentResponse(
        id=payment.id,
        date=payment.date,
        capital=payment.capital,
        interest=payment.interest,
        insurance=payment.insurance,
        total=payment.total,
        loan_name=payment.loan_name,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )


@router.put("/loan-payments/{payment_id}", response_model=LoanPaymentResponse)
async def update_loan_payment(
    payment_id: int,
    payment_update: LoanPaymentUpdate,
    db: Session = Depends(get_db)
):
    """
    Mettre à jour une mensualité de crédit.
    """
    payment = db.query(LoanPayment).filter(LoanPayment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Mensualité non trouvée")
    
    # Mettre à jour les champs fournis
    update_data = payment_update.dict(exclude_unset=True)
    
    # Si capital, interest ou insurance sont mis à jour, recalculer total
    if 'capital' in update_data or 'interest' in update_data or 'insurance' in update_data:
        capital = update_data.get('capital', payment.capital)
        interest = update_data.get('interest', payment.interest)
        insurance = update_data.get('insurance', payment.insurance)
        update_data['total'] = capital + interest + insurance
    
    for field, value in update_data.items():
        setattr(payment, field, value)
    
    payment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    
    # Invalider les comptes de résultat pour l'année du payment
    try:
        from backend.api.services.compte_resultat_service import invalidate_compte_resultat_for_year
        invalidate_compte_resultat_for_year(db, payment.date.year)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [update_loan_payment] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
    
    return LoanPaymentResponse(
        id=payment.id,
        date=payment.date,
        capital=payment.capital,
        interest=payment.interest,
        insurance=payment.insurance,
        total=payment.total,
        loan_name=payment.loan_name,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )


@router.delete("/loan-payments/{payment_id}", status_code=204)
async def delete_loan_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):
    """
    Supprimer une mensualité de crédit.
    """
    payment = db.query(LoanPayment).filter(LoanPayment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Mensualité non trouvée")
    
    # Sauvegarder l'année avant suppression
    payment_year = payment.date.year
    
    db.delete(payment)
    db.commit()
    
    # Invalider les comptes de résultat pour l'année du payment
    try:
        from backend.api.services.compte_resultat_service import invalidate_compte_resultat_for_year
        invalidate_compte_resultat_for_year(db, payment_year)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"⚠️ [delete_loan_payment] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
    
    return None


@router.post("/loan-payments/preview")
async def preview_loan_payment_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Prévisualise un fichier Excel ou CSV de mensualités de crédit.
    
    Structure attendue :
    - Colonne "annee" : types ("capital", "interets", "assurance cred", "total")
    - Colonnes années : 2021, 2022, 2023, etc.
    - Chaque ligne = un type de montant pour toutes les années
    
    Retourne : Preview, colonnes détectées, années détectées, montants extraits
    """
    # Vérifier l'extension du fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls') or filename_lower.endswith('.csv')):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un fichier Excel (.xlsx, .xls) ou CSV (.csv)"
        )
    
    # Lire le fichier
    file_content = await file.read()
    
    try:
        # Lire le fichier selon son type
        if filename_lower.endswith('.csv'):
            # Lire CSV avec pandas - essayer plusieurs encodages et séparateurs
            try:
                df = pd.read_csv(
                    io.BytesIO(file_content),
                    encoding='utf-8-sig',  # Gérer BOM UTF-8
                    sep=',',
                    engine='python',
                    on_bad_lines='skip'
                )
            except:
                try:
                    df = pd.read_csv(
                        io.BytesIO(file_content),
                        encoding='latin-1',
                        sep=';',
                        engine='python',
                        on_bad_lines='skip'
                    )
                except:
                    df = pd.read_csv(
                        io.BytesIO(file_content),
                        encoding='utf-8',
                        sep=None,
                        engine='python',
                        on_bad_lines='skip'
                    )
        else:
            # Lire Excel avec pandas
            df = pd.read_excel(
                io.BytesIO(file_content),
                engine='openpyxl' if filename_lower.endswith('.xlsx') else None
            )
        
        if df.empty:
            file_type = "Excel" if not filename_lower.endswith('.csv') else "CSV"
            raise HTTPException(status_code=400, detail=f"Le fichier {file_type} est vide")
        
        # Normaliser les noms de colonnes (convertir en string et strip)
        df.columns = [str(col).strip() for col in df.columns]
        
        # Vérifier que la colonne "annee" existe (insensible à la casse)
        annee_col = None
        for col in df.columns:
            if col.lower() == 'annee':
                annee_col = col
                break
        
        if not annee_col:
            raise HTTPException(
                status_code=400,
                detail="Colonne 'annee' non trouvée. Le fichier doit contenir une colonne 'annee' avec les types (capital, interets, assurance cred, total)"
            )
        
        # Détecter les colonnes années (colonnes numériques sauf "annee")
        # Mapping: année (int) -> nom de colonne réel dans le DataFrame
        year_columns_map = {}  # {année: nom_colonne_réel}
        invalid_columns = []
        
        for col in df.columns:
            # Convertir en string pour éviter l'erreur si col est un int
            col_str = str(col).strip()
            if col_str.lower() == 'annee':
                continue
            try:
                # Essayer de convertir en int (peut être une string "2021" ou un int 2021)
                year = int(float(col_str)) if '.' in col_str else int(col_str)
                if 1900 <= year <= 2100:  # Années valides
                    year_columns_map[year] = col  # Garder le nom de colonne original
                else:
                    invalid_columns.append(col_str)
            except (ValueError, TypeError):
                invalid_columns.append(col_str)
        
        # Trier par année et créer une liste des années
        year_columns = sorted(year_columns_map.keys())
        
        # Extraire les données par type
        capital_row = None
        interest_row = None
        insurance_row = None
        total_row = None
        
        for idx, row in df.iterrows():
            annee_value = str(row[annee_col]).lower().strip()
            if 'capital' in annee_value:
                capital_row = row
            elif 'interet' in annee_value or 'intérêt' in annee_value:
                interest_row = row
            elif 'assurance' in annee_value:
                insurance_row = row
            elif 'total' in annee_value:
                total_row = row
        
        # Préparer les données extraites
        extracted_data = []
        for year in year_columns:
            year_col = year_columns_map[year]  # Nom de colonne réel dans le DataFrame
            capital = float(capital_row[year_col]) if capital_row is not None and pd.notna(capital_row[year_col]) else 0.0
            interest = float(interest_row[year_col]) if interest_row is not None and pd.notna(interest_row[year_col]) else 0.0
            insurance = float(insurance_row[year_col]) if insurance_row is not None and pd.notna(insurance_row[year_col]) else 0.0
            total = float(total_row[year_col]) if total_row is not None and pd.notna(total_row[year_col]) else 0.0
            
            # Si total est vide, calculer
            if total == 0.0 and (capital > 0 or interest > 0 or insurance > 0):
                total = capital + interest + insurance
            
            extracted_data.append({
                "year": year,
                "date": f"01/01/{year}",
                "capital": capital,
                "interest": interest,
                "insurance": insurance,
                "total": total
            })
        
        # Preview des premières lignes du fichier
        preview_rows = []
        num_preview = min(10, len(df))
        for idx in range(num_preview):
            row_dict = {}
            for col in df.columns:
                value = df.iloc[idx][col]
                if pd.isna(value):
                    row_dict[col] = None
                elif isinstance(value, (int, float)):
                    row_dict[col] = str(value)
                else:
                    row_dict[col] = str(value)
            preview_rows.append(row_dict)
        
        # Vérifier s'il existe déjà des données pour "Prêt principal"
        existing_count = db.query(LoanPayment).filter(
            LoanPayment.loan_name == "Prêt principal"
        ).count()
        
        warning = None
        if existing_count > 0:
            warning = f"⚠️ Il existe déjà {existing_count} mensualité(s) pour 'Prêt principal'. L'import les remplacera toutes."
        
        return {
            "filename": file.filename,
            "total_rows": len(df),
            "detected_columns": list(df.columns),
            "year_columns": year_columns,
            "invalid_columns": invalid_columns,
            "extracted_data": extracted_data,
            "preview": preview_rows,
            "warning": warning,
            "stats": {
                "years_detected": len(year_columns),
                "records_to_create": len(extracted_data),
                "existing_records": existing_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'analyse du fichier: {str(e)}")


@router.post("/loan-payments/import")
async def import_loan_payment_file(
    file: UploadFile = File(...),
    loan_name: str = Query("Prêt principal", description="Nom du prêt"),
    db: Session = Depends(get_db)
):
    """
    Importer un fichier Excel ou CSV de mensualités de crédit.
    
    Structure attendue :
    - Colonne "annee" : types ("capital", "interets", "assurance cred", "total")
    - Colonnes années : 2021, 2022, 2023, etc.
    - Chaque ligne = un type de montant pour toutes les années
    
    Avant l'import, supprime toutes les mensualités existantes pour le loan_name.
    Pour chaque année, crée 1 enregistrement avec date = 01/01/année.
    """
    # Vérifier l'extension du fichier
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")
    
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls') or filename_lower.endswith('.csv')):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un fichier Excel (.xlsx, .xls) ou CSV (.csv)"
        )
    
    # Lire le fichier
    file_content = await file.read()
    
    try:
        # Lire le fichier selon son type
        if filename_lower.endswith('.csv'):
            # Lire CSV avec pandas - essayer plusieurs encodages et séparateurs
            try:
                df = pd.read_csv(
                    io.BytesIO(file_content),
                    encoding='utf-8-sig',  # Gérer BOM UTF-8
                    sep=',',
                    engine='python',
                    on_bad_lines='skip'
                )
            except:
                try:
                    df = pd.read_csv(
                        io.BytesIO(file_content),
                        encoding='latin-1',
                        sep=';',
                        engine='python',
                        on_bad_lines='skip'
                    )
                except:
                    df = pd.read_csv(
                        io.BytesIO(file_content),
                        encoding='utf-8',
                        sep=None,
                        engine='python',
                        on_bad_lines='skip'
                    )
        else:
            # Lire Excel avec pandas
            df = pd.read_excel(
                io.BytesIO(file_content),
                engine='openpyxl' if filename_lower.endswith('.xlsx') else None
            )
        
        if df.empty:
            file_type = "Excel" if not filename_lower.endswith('.csv') else "CSV"
            raise HTTPException(status_code=400, detail=f"Le fichier {file_type} est vide")
        
        # Normaliser les noms de colonnes (convertir en string et strip)
        df.columns = [str(col).strip() for col in df.columns]
        
        # Vérifier que la colonne "annee" existe (insensible à la casse)
        annee_col = None
        for col in df.columns:
            if col.lower() == 'annee':
                annee_col = col
                break
        
        if not annee_col:
            raise HTTPException(
                status_code=400,
                detail="Colonne 'annee' non trouvée. Le fichier doit contenir une colonne 'annee' avec les types (capital, interets, assurance cred, total)"
            )
        
        # Détecter les colonnes années
        # Mapping: année (int) -> nom de colonne réel dans le DataFrame
        year_columns_map = {}  # {année: nom_colonne_réel}
        
        for col in df.columns:
            col_str = str(col).strip()
            if col_str.lower() == 'annee':
                continue
            try:
                # Essayer de convertir en int (peut être une string "2021" ou un int 2021)
                year = int(float(col_str)) if '.' in col_str else int(col_str)
                if 1900 <= year <= 2100:
                    year_columns_map[year] = col  # Garder le nom de colonne original
            except (ValueError, TypeError):
                pass
        
        # Trier par année et créer une liste des années
        year_columns = sorted(year_columns_map.keys())
        
        if not year_columns:
            raise HTTPException(status_code=400, detail="Aucune colonne année valide détectée")
        
        # Extraire les données par type
        capital_row = None
        interest_row = None
        insurance_row = None
        total_row = None
        
        for idx, row in df.iterrows():
            annee_value = str(row[annee_col]).lower().strip()
            if 'capital' in annee_value:
                capital_row = row
            elif 'interet' in annee_value or 'intérêt' in annee_value:
                interest_row = row
            elif 'assurance' in annee_value:
                insurance_row = row
            elif 'total' in annee_value:
                total_row = row
        
        # Supprimer toutes les mensualités existantes pour ce loan_name
        deleted_count = db.query(LoanPayment).filter(
            LoanPayment.loan_name == loan_name
        ).delete()
        db.commit()
        
        # Créer les enregistrements pour chaque année
        created_count = 0
        errors = []
        
        for year in year_columns:
            year_col = year_columns_map[year]  # Nom de colonne réel dans le DataFrame
            payment_date = date(year, 1, 1)  # 01/01/année
            
            # Extraire les valeurs
            capital = 0.0
            interest = 0.0
            insurance = 0.0
            total = 0.0
            
            if capital_row is not None and pd.notna(capital_row[year_col]):
                try:
                    capital = float(capital_row[year_col])
                except (ValueError, TypeError):
                    pass
            
            if interest_row is not None and pd.notna(interest_row[year_col]):
                try:
                    interest = float(interest_row[year_col])
                except (ValueError, TypeError):
                    pass
            
            if insurance_row is not None and pd.notna(insurance_row[year_col]):
                try:
                    insurance = float(insurance_row[year_col])
                except (ValueError, TypeError):
                    pass
            
            if total_row is not None and pd.notna(total_row[year_col]):
                try:
                    total = float(total_row[year_col])
                except (ValueError, TypeError):
                    pass
            
            # Si total est vide ou incorrect, calculer
            calculated_total = capital + interest + insurance
            if total == 0.0 or abs(total - calculated_total) > 0.01:
                total = calculated_total
            
            # Ne créer un enregistrement que si au moins une valeur est non nulle
            # (évite de créer des lignes vides pour les années sans données)
            if capital > 0 or interest > 0 or insurance > 0 or total > 0:
                try:
                    payment = LoanPayment(
                        date=payment_date,
                        capital=capital,
                        interest=interest,
                        insurance=insurance,
                        total=total,
                        loan_name=loan_name
                    )
                    db.add(payment)
                    created_count += 1
                except Exception as e:
                    errors.append(f"Erreur pour l'année {year}: {str(e)}")
        
        db.commit()
        
        # Invalider les comptes de résultat pour toutes les années des payments importés
        try:
            from backend.api.services.compte_resultat_service import invalidate_compte_resultat_for_year
            for year in year_columns:
                invalidate_compte_resultat_for_year(db, year)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"⚠️ [import_loan_payment_file] Erreur lors de l'invalidation des comptes de résultat: {error_details}")
        
        return {
            "message": "Import réussi",
            "deleted_count": deleted_count,
            "created_count": created_count,
            "total_years": len(year_columns),
            "loan_name": loan_name,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'import: {str(e)}")
