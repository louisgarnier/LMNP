"""
CSV utilities for reading, detecting columns, and validating transaction data.

⚠️ Before making changes, read: ../../../docs/workflow/BEST_PRACTICES.md
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import io


def _has_header(lines: List[str], separator: str) -> bool:
    """
    Détecte si la première ligne est un en-tête ou des données en analysant plusieurs lignes.
    
    Args:
        lines: Liste des premières lignes du fichier (au moins 2-3 lignes)
        separator: Séparateur utilisé
    
    Returns:
        bool: True si la première ligne ressemble à un en-tête
    """
    if len(lines) < 1:
        return False
    
    first_line = lines[0].strip()
    if not first_line:
        return False
    
    parts = first_line.split(separator)
    
    # Si moins de 2 colonnes, probablement pas un en-tête
    if len(parts) < 2:
        return False
    
    # 1. Vérifier si la première colonne de la première ligne ressemble à une date (format DD/MM/YYYY)
    first_col = parts[0].strip()
    try:
        datetime.strptime(first_col, '%d/%m/%Y')
        # Si c'est une date, ce n'est PAS un en-tête, c'est une donnée
        return False
    except:
        pass
    
    # 2. Vérifier si les colonnes contiennent des mots-clés d'en-tête
    header_keywords = ['date', 'dates', 'montant', 'amount', 'quantité', 'quantite', 'qty',
                       'libellé', 'libelle', 'nom', 'name', 'description', 'desc', 'label',
                       'solde', 'balance', 'col', 'colonne', 'column']
    first_line_lower = first_line.lower()
    has_keywords = any(keyword in first_line_lower for keyword in header_keywords)
    
    # 3. Analyser la deuxième ligne (si disponible) pour comparer
    if len(lines) >= 2:
        second_line = lines[1].strip()
        if second_line:
            second_parts = second_line.split(separator)
            if len(second_parts) >= 1:
                second_first_col = second_parts[0].strip()
                
                # Si la première colonne de la 2ème ligne est une date, alors la 1ère ligne est probablement un en-tête
                try:
                    datetime.strptime(second_first_col, '%d/%m/%Y')
                    # La 2ème ligne commence par une date, donc la 1ère ligne est probablement un en-tête
                    if has_keywords:
                        return True  # Confirmation : mots-clés + 2ème ligne avec date
                except:
                    pass
                
                # Si la 2ème ligne commence par un nombre, la 1ère ligne est probablement un en-tête
                try:
                    float(second_first_col.replace(',', '.').replace(' ', ''))
                    if has_keywords:
                        return True  # Confirmation : mots-clés + 2ème ligne avec nombre
                except:
                    pass
    
    # 4. Si contient des mots-clés d'en-tête, probablement un en-tête
    if has_keywords:
        return True
    
    # 5. Si la première colonne est numérique, probablement pas un en-tête
    try:
        float(first_col.replace(',', '.').replace(' ', ''))
        return False  # Commence par un nombre, donc c'est une donnée
    except:
        pass
    
    # 6. Si toutes les colonnes sont des chaînes courtes sans chiffres, probablement un en-tête
    all_text = all(
        not part.strip().replace(',', '.').replace(' ', '').replace('-', '').isdigit()
        and len(part.strip()) < 50  # Colonnes d'en-tête sont généralement courtes
        for part in parts[:3]  # Vérifier les 3 premières colonnes
    )
    if all_text and len(parts) >= 2:
        return True
    
    # Par défaut, si on ne peut pas déterminer, considérer comme DONNÉES (pas d'en-tête)
    # pour éviter de perdre la première ligne
    return False


def read_csv_safely(file_content: bytes, filename: str = "") -> Tuple[pd.DataFrame, str, str]:
    """
    Lit un fichier CSV de manière sécurisée en essayant différents séparateurs et encodages.
    Gère les fichiers avec ou sans en-tête.
    
    Args:
        file_content: Contenu du fichier en bytes
        filename: Nom du fichier (pour logging)
    
    Returns:
        Tuple[DataFrame, encoding, separator]: DataFrame lu, encodage utilisé, séparateur utilisé
    
    Raises:
        ValueError: Si le fichier ne peut pas être lu avec les encodages/séparateurs disponibles
    """
    separators = [';', ',', '\t']
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for enc in encodings:
        for sep_char in separators:
            try:
                # Convertir bytes en string
                file_string = file_content.decode(enc)
                
                # Supprimer le BOM UTF-8 si présent
                if file_string.startswith('\ufeff'):
                    file_string = file_string[1:]
                
                lines = file_string.split('\n')
                
                if not lines:
                    continue
                
                # Nettoyer les lignes vides
                lines = [line.strip() for line in lines if line.strip()]
                
                if len(lines) < 1:
                    continue
                
                # Détecter si le fichier a un en-tête en analysant les premières lignes
                # Prendre au moins 3 lignes pour une meilleure détection
                lines_to_analyze = lines[:min(5, len(lines))]
                has_header = _has_header(lines_to_analyze, sep_char)
                
                # Reconstruire le fichier à partir des lignes nettoyées pour éviter les problèmes
                # avec les lignes vides qui pourraient perturber la lecture
                cleaned_file_string = '\n'.join(lines)
                file_io = io.StringIO(cleaned_file_string)
                
                # Lire avec ou sans en-tête
                if has_header:
                    df = pd.read_csv(
                        file_io,
                        sep=sep_char,
                        engine='python',
                        on_bad_lines='skip',
                        keep_default_na=False  # Ne pas convertir les chaînes vides en NaN
                    )
                else:
                    # Pas d'en-tête, lire sans header et créer des noms de colonnes génériques
                    # D'abord, déterminer le nombre max de colonnes en analysant les lignes nettoyées
                    max_cols = max(len(line.split(sep_char)) for line in lines if line.strip())
                    
                    file_io.seek(0)
                    df = pd.read_csv(
                        file_io,
                        sep=sep_char,
                        engine='python',
                        on_bad_lines='skip',
                        header=None,
                        names=[f'Col{i+1}' for i in range(max_cols)],  # Forcer le nombre de colonnes
                        keep_default_na=False  # Ne pas convertir les chaînes vides en NaN
                    )
                
                # Nettoyer les colonnes complètement vides (toutes NaN ou vides)
                # Mais garder les colonnes qui ont au moins quelques valeurs
                df = df.dropna(axis=1, how='all')
                # Nettoyer aussi les colonnes qui ne contiennent que des chaînes vides
                cols_to_drop = []
                for col in df.columns:
                    # Vérifier si la colonne est vide (NaN ou chaînes vides)
                    if df[col].isna().all() or df[col].astype(str).str.strip().eq('').all():
                        cols_to_drop.append(col)
                df = df.drop(columns=cols_to_drop)
                
                # Vérifier que nous avons bien lu plusieurs colonnes
                if len(df.columns) > 1:
                    return df, enc, sep_char
            except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as e:
                continue
    
    raise ValueError(f"Impossible de lire le fichier {filename} avec les encodages et séparateurs disponibles")


def _detect_column_by_content(df: pd.DataFrame, col_name: str, target_type: str) -> bool:
    """
    Détecte le type d'une colonne en analysant son contenu.
    
    Args:
        df: DataFrame
        col_name: Nom de la colonne
        target_type: Type cible ('date', 'quantite', 'nom', 'solde')
    
    Returns:
        bool: True si la colonne correspond au type cible
    """
    if col_name not in df.columns or len(df) == 0:
        return False
    
    col_data = df[col_name].dropna().head(10)  # Analyser les 10 premières valeurs non-nulles
    
    if len(col_data) == 0:
        return False
    
    if target_type == 'date':
        # Vérifier si les valeurs ressemblent à des dates DD/MM/YYYY
        date_count = 0
        for val in col_data:
            val_str = str(val).strip()
            try:
                datetime.strptime(val_str, '%d/%m/%Y')
                date_count += 1
            except:
                pass
        return date_count >= len(col_data) * 0.7  # Au moins 70% de dates
    
    elif target_type == 'quantite':
        # Vérifier si les valeurs sont numériques (avec virgule ou point)
        numeric_count = 0
        for val in col_data:
            val_str = str(val).strip().replace(',', '.').replace(' ', '')
            try:
                float(val_str)
                numeric_count += 1
            except:
                pass
        return numeric_count >= len(col_data) * 0.7  # Au moins 70% de nombres
    
    elif target_type == 'nom':
        # Vérifier si les valeurs sont des chaînes de caractères (pas des dates, pas des nombres purs)
        text_count = 0
        total_length = 0
        for val in col_data:
            val_str = str(val).strip()
            # Ignorer les valeurs vides
            if len(val_str) == 0:
                continue
            # Ne pas être une date
            try:
                datetime.strptime(val_str, '%d/%m/%Y')
                continue
            except:
                pass
            # Ne pas être un nombre pur
            try:
                float(val_str.replace(',', '.').replace(' ', ''))
                continue
            except:
                pass
            # Si c'est une chaîne non vide avec une certaine longueur, probablement un nom
            if len(val_str) > 2:  # Au moins 3 caractères
                text_count += 1
                total_length += len(val_str)
        # Retourner True si au moins 50% de texte ET longueur moyenne > 5 caractères
        avg_length = total_length / text_count if text_count > 0 else 0
        return text_count >= len(col_data) * 0.3 and avg_length > 5  # Au moins 30% de texte avec longueur moyenne > 5
    
    return False


def detect_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """
    Détecte intelligemment le mapping entre les colonnes du fichier CSV et les colonnes de la BDD.
    Fonctionne avec ou sans en-tête en analysant le contenu des colonnes.
    
    Mapping attendu:
    - Date (fichier) → date (BDD)
    - amount, Montant, Quantité (fichier) → quantite (BDD)
    - name, nom, Libellé (fichier) → nom (BDD)
    
    NOTE: Le solde n'est plus mappé depuis les fichiers CSV, il sera calculé automatiquement.
    
    Args:
        df: DataFrame avec les colonnes du fichier CSV
    
    Returns:
        Dict[str, str]: Mapping {colonne_fichier: colonne_bdd}
    """
    mapping = {}
    columns_lower = [col.lower().strip() for col in df.columns]
    
    # Étape 1: Mapping par nom de colonne (si en-tête présent)
    # Mapping pour date
    date_variants = ['date', 'dates']
    for col in df.columns:
        if col.lower().strip() in date_variants:
            mapping[col] = 'date'
            break
    
    # Mapping pour quantite (montant)
    quantite_variants = ['amount', 'montant', 'quantité', 'quantite', 'qty']
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in quantite_variants or 'montant' in col_lower:
            mapping[col] = 'quantite'
            break
    
    # Mapping pour nom (libellé)
    nom_variants = ['name', 'nom', 'libellé', 'libelle', 'description', 'desc', 'label']
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in nom_variants or 'libellé' in col_lower or 'libelle' in col_lower:
            mapping[col] = 'nom'
            break
    
    # NOTE: Solde n'est plus mappé depuis les fichiers CSV
    # Le solde sera calculé automatiquement lors de l'insertion en BDD
    
    # Étape 2: Si mapping incomplet, analyser le contenu des colonnes
    # NOTE: Solde n'est plus requis, il sera calculé automatiquement
    required_mappings = {
        'date': None,
        'quantite': None,
        'nom': None
    }
    
    # Remplir les mappings déjà trouvés
    for col, db_col in mapping.items():
        if db_col in required_mappings:
            required_mappings[db_col] = col
    
    # Chercher les colonnes manquantes en analysant le contenu
    for col in df.columns:
        if col in mapping.keys():
            continue  # Déjà mappée
        
        # Chercher date
        if not required_mappings['date'] and _detect_column_by_content(df, col, 'date'):
            required_mappings['date'] = col
            mapping[col] = 'date'
            continue
        
        # Chercher quantite
        if not required_mappings['quantite'] and _detect_column_by_content(df, col, 'quantite'):
            required_mappings['quantite'] = col
            mapping[col] = 'quantite'
            continue
        
        # Chercher nom (on va le faire après pour trouver la meilleure colonne)
        pass
    
    # Chercher nom : trouver la colonne avec le plus de texte significatif
    # Pour les fichiers sans en-tête, le libellé peut être dans différentes colonnes
    if not required_mappings['nom']:
        best_nom_col = None
        best_score = 0
        for col in df.columns:
            if col in mapping.keys():
                continue
            # Calculer un score basé sur le nombre de valeurs non vides et leur longueur
            col_data = df[col].astype(str)
            non_empty = col_data[col_data.str.strip() != '']
            if len(non_empty) > 0:
                avg_length = non_empty.str.len().mean()
                # Score = nombre de valeurs non vides * longueur moyenne
                score = len(non_empty) * avg_length
                # Bonus si la colonne contient du texte (pas des dates, pas des nombres)
                text_count = 0
                sample_size = min(10, len(non_empty))
                for val in non_empty.head(sample_size):
                    val_str = str(val).strip()
                    if len(val_str) > 2:
                        try:
                            datetime.strptime(val_str, '%d/%m/%Y')
                            continue
                        except:
                            pass
                        try:
                            float(val_str.replace(',', '.').replace(' ', ''))
                            continue
                        except:
                            pass
                        text_count += 1
                # Bonus si au moins 50% de texte significatif
                if sample_size > 0 and text_count >= sample_size * 0.5:
                    score *= 2  # Bonus pour colonnes avec beaucoup de texte
                
                if score > best_score:
                    best_score = score
                    best_nom_col = col
        
        if best_nom_col:
            required_mappings['nom'] = best_nom_col
            mapping[best_nom_col] = 'nom'
            
            # Si le libellé peut être dans plusieurs colonnes, chercher la colonne avec le texte le plus long
            # et créer une colonne combinée si nécessaire
            other_text_cols = []
            for col in df.columns:
                if col in mapping.keys() or col == best_nom_col:
                    continue
                col_data = df[col].astype(str)
                non_empty = col_data[col_data.str.strip() != '']
                if len(non_empty) > len(df) * 0.1:  # Au moins 10% de valeurs non vides
                    # Vérifier si c'est du texte (pas date, pas nombre)
                    text_count = 0
                    avg_length = 0
                    for val in non_empty.head(10):
                        val_str = str(val).strip()
                        if len(val_str) > 2:
                            try:
                                datetime.strptime(val_str, '%d/%m/%Y')
                                continue
                            except:
                                pass
                            try:
                                float(val_str.replace(',', '.').replace(' ', ''))
                                continue
                            except:
                                pass
                            text_count += 1
                            avg_length += len(val_str)
                    if text_count >= 2:  # Au moins 2 valeurs de texte
                        avg_length = avg_length / text_count if text_count > 0 else 0
                        other_text_cols.append((col, avg_length))
            
            # Trier par longueur moyenne décroissante et prendre la meilleure
            other_text_cols.sort(key=lambda x: x[1], reverse=True)
            
            # Si on trouve une autre colonne avec du texte long, combiner avec la colonne nom principale
            if other_text_cols and other_text_cols[0][1] > 10:  # Longueur moyenne > 10 caractères
                best_other_col = other_text_cols[0][0]
                # Créer une colonne combinée pour le nom
                combined_col_name = f"{best_nom_col}_combined"
                # Combiner les deux colonnes (prendre la valeur non vide)
                def combine_cols(row):
                    val1 = str(row[best_nom_col]) if pd.notna(row[best_nom_col]) else ''
                    val2 = str(row[best_other_col]) if pd.notna(row[best_other_col]) else ''
                    val1 = val1.strip()
                    val2 = val2.strip()
                    # Éviter "None" comme string
                    if val1.lower() == 'none':
                        val1 = ''
                    if val2.lower() == 'none':
                        val2 = ''
                    if val1 and val2:
                        return (val1 + ' ' + val2).strip()
                    return val1 or val2
                
                df[combined_col_name] = df.apply(combine_cols, axis=1)
                # Remplacer le mapping
                mapping.pop(best_nom_col, None)
                mapping[combined_col_name] = 'nom'
                required_mappings['nom'] = combined_col_name
        else:
            # Si aucune colonne n'est trouvée, utiliser la première colonne non mappée avec du texte
            for col in df.columns:
                if col not in mapping.keys():
                    col_data = df[col].astype(str)
                    non_empty = col_data[col_data.str.strip() != '']
                    if len(non_empty) > len(df) * 0.1:  # Au moins 10% de valeurs non vides
                        required_mappings['nom'] = col
                        mapping[col] = 'nom'
                        break
    
    # NOTE: Solde n'est plus mappé depuis les fichiers CSV
    # Le solde sera calculé automatiquement lors de l'insertion en BDD
    
    return mapping


def validate_transactions(df: pd.DataFrame, column_mapping: Dict[str, str]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Valide les transactions du DataFrame.
    
    - Dates: format DD/MM/YYYY
    - Montants: numériques (virgule ou point acceptés)
    - Noms: non vides
    
    Args:
        df: DataFrame avec les transactions
        column_mapping: Mapping des colonnes fichier → BDD
    
    Returns:
        Tuple[DataFrame nettoyé, Liste des erreurs]
    """
    errors = []
    df_clean = df.copy()
    
    # Valider et nettoyer la colonne date
    date_col = None
    for col, bdd_col in column_mapping.items():
        if bdd_col == 'date':
            date_col = col
            break
    
    if date_col:
        try:
            # Essayer de parser les dates au format DD/MM/YYYY
            df_clean[date_col] = pd.to_datetime(df_clean[date_col], format='%d/%m/%Y', errors='coerce')
            invalid_dates = df_clean[date_col].isna().sum()
            if invalid_dates > 0:
                errors.append(f"{invalid_dates} dates invalides détectées")
                # Supprimer les lignes avec dates invalides
                df_clean = df_clean.dropna(subset=[date_col])
        except Exception as e:
            errors.append(f"Erreur lors de la validation des dates: {str(e)}")
    
    # Valider et nettoyer les colonnes numériques (quantite uniquement, solde calculé automatiquement)
    for col, bdd_col in column_mapping.items():
        if bdd_col == 'quantite':
            try:
                # Convertir en string, remplacer virgule par point, puis en numérique
                df_clean[col] = df_clean[col].astype(str).str.replace(' ', '').str.replace(',', '.')
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                invalid_nums = df_clean[col].isna().sum()
                if invalid_nums > 0:
                    errors.append(f"{invalid_nums} valeurs numériques invalides dans {col}")
            except Exception as e:
                errors.append(f"Erreur lors de la validation de {col}: {str(e)}")
    
    # Valider les noms (non vides)
    nom_col = None
    for col, bdd_col in column_mapping.items():
        if bdd_col == 'nom':
            nom_col = col
            break
    
    if nom_col:
        try:
            df_clean[nom_col] = df_clean[nom_col].astype(str).str.strip()
            empty_names = (df_clean[nom_col] == '').sum()
            if empty_names > 0:
                errors.append(f"{empty_names} noms vides détectés")
                # NOTE: On ne supprime PAS les lignes avec noms vides pour l'aperçu
                # Elles seront filtrées lors de l'import final si nécessaire
        except Exception as e:
            errors.append(f"Erreur lors de la validation des noms: {str(e)}")
    
    return df_clean, errors


def preview_transactions(df: pd.DataFrame, column_mapping: Dict[str, str], num_rows: int = 10) -> List[Dict[str, Any]]:
    """
    Retourne les premières lignes du DataFrame pour aperçu.
    
    Args:
        df: DataFrame avec les transactions
        column_mapping: Mapping des colonnes fichier → BDD
        num_rows: Nombre de lignes à retourner (défaut: 10)
    
    Returns:
        List[Dict]: Liste des premières lignes avec les colonnes mappées
    """
    preview_rows = []
    
    # Prendre les premières lignes
    df_preview = df.head(num_rows)
    
    for _, row in df_preview.iterrows():
        preview_row = {}
        for col, bdd_col in column_mapping.items():
            value = row[col]
            # Formater les dates
            if bdd_col == 'date' and pd.notna(value):
                if isinstance(value, pd.Timestamp):
                    preview_row[bdd_col] = value.strftime('%d/%m/%Y')
                else:
                    preview_row[bdd_col] = str(value)
            # Formater les nombres (gérer les virgules)
            elif bdd_col == 'quantite' and pd.notna(value):
                try:
                    # Convertir en string, remplacer virgule par point, puis en float
                    value_str = str(value).replace(' ', '').replace(',', '.')
                    preview_row[bdd_col] = float(value_str)
                except (ValueError, TypeError):
                    preview_row[bdd_col] = None
            else:
                preview_row[bdd_col] = str(value) if pd.notna(value) else None
        preview_rows.append(preview_row)
    
    return preview_rows

