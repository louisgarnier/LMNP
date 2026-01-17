"""
Script interactif pour gérer les mappings hardcodés.

⚠️ Before making changes, read: ../../docs/workflow/BEST_PRACTICES.md

Ce script offre 4 options :
1. Supprimer toutes les données hardcodées
2. Supprimer une/des données hardcodées (sélection par ID)
3. Ajouter depuis un fichier Excel
4. Ajouter une donnée hardcodée manuellement

Usage:
    python backend/scripts/manage_hardcoded_mappings.py
"""

import sys
from pathlib import Path
import pandas as pd

# Ajouter le chemin du projet au PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import SessionLocal, init_database
from backend.database.models import AllowedMapping
from backend.api.services.mapping_obligatoire_service import validate_level3_value, ALLOWED_LEVEL_3_VALUES


def print_separator():
    """Affiche un séparateur visuel."""
    print("=" * 60)


def print_menu():
    """Affiche le menu principal."""
    print_separator()
    print("GESTION DES MAPPINGS HARDCODÉS")
    print_separator()
    print("\nOptions disponibles :")
    print("  1. Supprimer toutes les données hardcodées")
    print("  2. Supprimer une/des données hardcodées (sélection par ID)")
    print("  3. Ajouter depuis un fichier Excel")
    print("   Ajouter depuis un fichier Excel (mise à jour complète)")
    print("  4. Ajouter une donnée hardcodée manuellement")
    print("  0. Quitter")
    print_separator()


def list_hardcoded_mappings(db, show_ids=True):
    """
    Liste tous les mappings hardcodés.
    
    Args:
        db: Session de base de données
        show_ids: Si True, affiche les IDs pour la sélection
    
    Returns:
        Liste des mappings hardcodés
    """
    mappings = db.query(AllowedMapping).filter(
        AllowedMapping.is_hardcoded == True
    ).order_by(AllowedMapping.level_1, AllowedMapping.level_2, AllowedMapping.level_3).all()
    
    if not mappings:
        print("\n⚠️  Aucun mapping hardcodé trouvé.")
        return []
    
    print(f"\n📋 Mappings hardcodés ({len(mappings)} trouvés) :\n")
    
    if show_ids:
        print(f"{'ID':<5} | {'Level 1':<40} | {'Level 2':<30} | {'Level 3':<25}")
        print("-" * 105)
    
    for mapping in mappings:
        level_3_display = mapping.level_3 if mapping.level_3 else "(vide)"
        if show_ids:
            print(f"{mapping.id:<5} | {mapping.level_1:<40} | {mapping.level_2:<30} | {level_3_display:<25}")
        else:
            print(f"  - {mapping.level_1} | {mapping.level_2} | {level_3_display}")
    
    return mappings


def option_1_delete_all(db):
    """Option 1 : Supprimer toutes les données hardcodées."""
    print_separator()
    print("OPTION 1 : Supprimer toutes les données hardcodées")
    print_separator()
    
    # Lister les mappings hardcodés
    mappings = list_hardcoded_mappings(db, show_ids=False)
    
    if not mappings:
        print("\n✅ Aucune donnée hardcodée à supprimer.")
        return
    
    count = len(mappings)
    print(f"\n⚠️  ATTENTION : Vous êtes sur le point de supprimer {count} mapping(s) hardcodé(s).")
    confirmation = input("\nÊtes-vous sûr ? (tapez 'OUI' pour confirmer) : ")
    
    if confirmation != "OUI":
        print("\n❌ Suppression annulée.")
        return
    
    try:
        for mapping in mappings:
            db.delete(mapping)
        
        db.commit()
        print(f"\n✅ {count} mapping(s) hardcodé(s) supprimé(s) avec succès.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR lors de la suppression : {str(e)}")
        import traceback
        traceback.print_exc()


def option_2_delete_selected(db):
    """Option 2 : Supprimer une/des données hardcodées (sélection par ID)."""
    print_separator()
    print("OPTION 2 : Supprimer une/des données hardcodées")
    print_separator()
    
    # Lister les mappings hardcodés avec IDs
    mappings = list_hardcoded_mappings(db, show_ids=True)
    
    if not mappings:
        print("\n✅ Aucune donnée hardcodée à supprimer.")
        return
    
    # Créer un dictionnaire ID -> mapping
    mappings_dict = {m.id: m for m in mappings}
    
    print("\n💡 Entrez les IDs des mappings à supprimer (séparés par des virgules)")
    print("   Exemple : 1,3,5 ou simplement 1")
    
    user_input = input("\nIDs à supprimer : ").strip()
    
    if not user_input:
        print("\n❌ Aucun ID fourni. Suppression annulée.")
        return
    
    # Parser les IDs
    try:
        ids_to_delete = [int(id_str.strip()) for id_str in user_input.split(",")]
    except ValueError:
        print("\n❌ Format invalide. Utilisez des nombres séparés par des virgules.")
        return
    
    # Vérifier que les IDs existent
    invalid_ids = [id_val for id_val in ids_to_delete if id_val not in mappings_dict]
    if invalid_ids:
        print(f"\n⚠️  IDs invalides (non trouvés) : {invalid_ids}")
        ids_to_delete = [id_val for id_val in ids_to_delete if id_val in mappings_dict]
    
    if not ids_to_delete:
        print("\n❌ Aucun ID valide. Suppression annulée.")
        return
    
    # Afficher les mappings qui seront supprimés
    print("\n📋 Mappings qui seront supprimés :")
    for id_val in ids_to_delete:
        m = mappings_dict[id_val]
        level_3_display = m.level_3 if m.level_3 else "(vide)"
        print(f"  - ID {id_val} : {m.level_1} | {m.level_2} | {level_3_display}")
    
    confirmation = input(f"\n⚠️  Supprimer {len(ids_to_delete)} mapping(s) ? (tapez 'OUI' pour confirmer) : ")
    
    if confirmation != "OUI":
        print("\n❌ Suppression annulée.")
        return
    
    try:
        deleted_count = 0
        for id_val in ids_to_delete:
            mapping = mappings_dict[id_val]
            db.delete(mapping)
            deleted_count += 1
        
        db.commit()
        print(f"\n✅ {deleted_count} mapping(s) supprimé(s) avec succès.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR lors de la suppression : {str(e)}")
        import traceback
        traceback.print_exc()


def load_mappings_from_excel(excel_path: Path) -> list:
    """
    Charge les mappings depuis le fichier Excel.
    
    Returns:
        Liste de tuples (level_1, level_2, level_3)
    """
    if not excel_path.exists():
        raise FileNotFoundError(f"Le fichier Excel n'existe pas : {excel_path}")
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Erreur lors de la lecture du fichier Excel : {str(e)}")
    
    # Vérifier les colonnes attendues
    expected_columns = ['Level 1', 'Level 2', 'Level 3']
    if not all(col in df.columns for col in expected_columns):
        raise ValueError(f"Le fichier Excel doit contenir les colonnes : {expected_columns}")
    
    mappings = []
    errors = []
    
    for idx, row in df.iterrows():
        level_1 = str(row['Level 1']).strip() if pd.notna(row['Level 1']) else None
        level_2 = str(row['Level 2']).strip() if pd.notna(row['Level 2']) else None
        level_3 = str(row['Level 3']).strip() if pd.notna(row['Level 3']) else None
        
        # Validation : level_1 et level_2 sont obligatoires
        if not level_1 or not level_2:
            errors.append(f"Ligne {idx + 2} : Level 1 ou Level 2 vide - ignorée")
            continue
        
        # Validation : level_3 doit être dans la liste fixe (si fourni)
        if level_3 and not validate_level3_value(level_3):
            errors.append(f"Ligne {idx + 2} : Level 3 invalide '{level_3}' - ignorée")
            continue
        
        # Normaliser level_3 : None si vide
        level_3 = level_3 if level_3 else None
        
        mappings.append((level_1, level_2, level_3))
    
    if errors:
        print("\n⚠️  Avertissements lors de la lecture du fichier :")
        for error in errors[:10]:  # Limiter à 10 erreurs
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... et {len(errors) - 10} autre(s) erreur(s)")
    
    return mappings


def option_3_add_from_excel(db):
    """Option 3 : Ajouter depuis un fichier Excel."""
    print_separator()
    print("OPTION 3 : Ajouter depuis un fichier Excel")
    print_separator()
    
    # Demander le chemin du fichier
    default_path = project_root / "scripts" / "mappings_obligatoires.xlsx"
    print(f"\n💡 Chemin par défaut : {default_path}")
    user_path = input("Chemin du fichier Excel (appuyez sur Entrée pour utiliser le défaut) : ").strip()
    
    if not user_path:
        excel_path = default_path
    else:
        excel_path = Path(user_path)
        if not excel_path.is_absolute():
            excel_path = project_root / excel_path
    
    if not excel_path.exists():
        print(f"\n❌ ERREUR : Le fichier n'existe pas : {excel_path}")
        return
    
    print(f"\n📖 Lecture du fichier : {excel_path}")
    
    try:
        excel_mappings = load_mappings_from_excel(excel_path)
        print(f"✅ {len(excel_mappings)} combinaison(s) valide(s) trouvée(s) dans le fichier Excel")
    except Exception as e:
        print(f"\n❌ ERREUR lors de la lecture du fichier Excel : {e}")
        return
    
    if not excel_mappings:
        print("\n⚠️  Aucune combinaison valide trouvée dans le fichier Excel.")
        return
    
    # Afficher un aperçu
    print("\n📋 Aperçu des combinaisons (10 premières) :")
    for i, (l1, l2, l3) in enumerate(excel_mappings[:10], 1):
        l3_display = l3 if l3 else "(vide)"
        print(f"  {i}. {l1} | {l2} | {l3_display}")
    if len(excel_mappings) > 10:
        print(f"  ... et {len(excel_mappings) - 10} autre(s) combinaison(s)")
    
    print("\n⚠️  Cette opération va :")
    print("  - Supprimer tous les mappings hardcodés actuels qui ne sont pas dans le fichier Excel")
    print("  - Ajouter/marquer comme hardcodés les mappings du fichier Excel")
    print("  - Conserver les mappings manuels (is_hardcoded = False)")
    
    confirmation = input("\nContinuer ? (tapez 'OUI' pour confirmer) : ")
    
    if confirmation != "OUI":
        print("\n❌ Opération annulée.")
        return
    
    # Créer un set pour faciliter les recherches
    excel_mappings_set = set(excel_mappings)
    
    # 1. Récupérer tous les mappings hardcodés actuels
    hardcoded_mappings = db.query(AllowedMapping).filter(
        AllowedMapping.is_hardcoded == True
    ).all()
    
    deleted_count = 0
    added_count = 0
    updated_count = 0
    
    # 2. Supprimer les mappings hardcodés qui ne sont plus dans le fichier Excel
    for mapping in hardcoded_mappings:
        mapping_tuple = (mapping.level_1, mapping.level_2, mapping.level_3)
        if mapping_tuple not in excel_mappings_set:
            db.delete(mapping)
            deleted_count += 1
    
    # 3. Ajouter/mettre à jour les mappings du fichier Excel
    for level_1, level_2, level_3 in excel_mappings:
        # Chercher si le mapping existe déjà
        query = db.query(AllowedMapping).filter(
            AllowedMapping.level_1 == level_1,
            AllowedMapping.level_2 == level_2
        )
        if level_3:
            query = query.filter(AllowedMapping.level_3 == level_3)
        else:
            query = query.filter(AllowedMapping.level_3.is_(None))
        
        existing = query.first()
        
        if existing:
            # Mettre à jour is_hardcoded si nécessaire
            if not existing.is_hardcoded:
                existing.is_hardcoded = True
                updated_count += 1
        else:
            # Créer le nouveau mapping
            try:
                new_mapping = AllowedMapping(
                    level_1=level_1,
                    level_2=level_2,
                    level_3=level_3,
                    is_hardcoded=True
                )
                db.add(new_mapping)
                added_count += 1
            except Exception as e:
                # Ignorer les doublons (contrainte unique)
                db.rollback()
                continue
    
    try:
        db.commit()
        print("\n✅ Mise à jour réussie :")
        print(f"   - {deleted_count} mapping(s) hardcodé(s) supprimé(s)")
        print(f"   - {added_count} nouveau(x) mapping(s) hardcodé(s) ajouté(s)")
        print(f"   - {updated_count} mapping(s) existant(s) marqué(s) comme hardcodé(s)")
        
        # Compter les mappings manuels
        manual_count = db.query(AllowedMapping).filter(
            AllowedMapping.is_hardcoded == False
        ).count()
        print(f"   - {manual_count} mapping(s) manuel(s) conservé(s)")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR lors de la mise à jour : {str(e)}")
        import traceback
        traceback.print_exc()


def option_4_add_manual(db):
    """Option 4 : Ajouter une donnée hardcodée manuellement."""
    print_separator()
    print("OPTION 4 : Ajouter une donnée hardcodée manuellement")
    print_separator()
    
    print("\n📝 Règles à respecter :")
    print("  - Level 1 : Obligatoire")
    print("  - Level 2 : Obligatoire")
    print("  - Level 3 : Optionnel (peut être vide)")
    print(f"  - Si Level 3 est renseigné, doit être dans : {', '.join(ALLOWED_LEVEL_3_VALUES)}")
    
    # Demander Level 1
    level_1 = input("\nLevel 1 : ").strip()
    if not level_1:
        print("\n❌ Level 1 est obligatoire. Opération annulée.")
        return
    
    # Demander Level 2
    level_2 = input("Level 2 : ").strip()
    if not level_2:
        print("\n❌ Level 2 est obligatoire. Opération annulée.")
        return
    
    # Demander Level 3
    print(f"\nLevel 3 (optionnel - valeurs autorisées : {', '.join(ALLOWED_LEVEL_3_VALUES)})")
    level_3 = input("Level 3 (appuyez sur Entrée pour laisser vide) : ").strip()
    
    # Normaliser level_3
    if not level_3:
        level_3 = None
    else:
        # Validation
        if not validate_level3_value(level_3):
            print(f"\n❌ ERREUR : Level 3 '{level_3}' n'est pas dans la liste autorisée.")
            print(f"   Valeurs autorisées : {', '.join(ALLOWED_LEVEL_3_VALUES)}")
            return
    
    # Afficher un résumé
    level_3_display = level_3 if level_3 else "(vide)"
    print(f"\n📋 Résumé :")
    print(f"   Level 1 : {level_1}")
    print(f"   Level 2 : {level_2}")
    print(f"   Level 3 : {level_3_display}")
    
    # Vérifier si le mapping existe déjà
    query = db.query(AllowedMapping).filter(
        AllowedMapping.level_1 == level_1,
        AllowedMapping.level_2 == level_2
    )
    if level_3:
        query = query.filter(AllowedMapping.level_3 == level_3)
    else:
        query = query.filter(AllowedMapping.level_3.is_(None))
    
    existing = query.first()
    
    if existing:
        if existing.is_hardcoded:
            print(f"\n⚠️  Ce mapping existe déjà comme hardcodé (ID: {existing.id}).")
            response = input("Voulez-vous le conserver tel quel ? (O/N) : ").strip().upper()
            if response == "O":
                print("\n✅ Mapping conservé tel quel.")
                return
        else:
            print(f"\n⚠️  Ce mapping existe déjà comme manuel (ID: {existing.id}).")
            response = input("Voulez-vous le marquer comme hardcodé ? (O/N) : ").strip().upper()
            if response == "O":
                try:
                    existing.is_hardcoded = True
                    db.commit()
                    print("\n✅ Mapping marqué comme hardcodé avec succès.")
                    return
                except Exception as e:
                    db.rollback()
                    print(f"\n❌ ERREUR : {str(e)}")
                    return
    
    # Créer le nouveau mapping
    confirmation = input("\nAjouter ce mapping ? (O/N) : ").strip().upper()
    
    if confirmation != "O":
        print("\n❌ Opération annulée.")
        return
    
    try:
        new_mapping = AllowedMapping(
            level_1=level_1,
            level_2=level_2,
            level_3=level_3,
            is_hardcoded=True
        )
        db.add(new_mapping)
        db.commit()
        print("\n✅ Mapping hardcodé ajouté avec succès.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR lors de l'ajout : {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Fonction principale du script interactif."""
    # Initialiser la base de données
    init_database()
    
    # Créer une session
    db = SessionLocal()
    
    try:
        while True:
            print_menu()
            
            choice = input("Votre choix : ").strip()
            
            if choice == "0":
                print("\n👋 Au revoir !")
                break
            elif choice == "1":
                option_1_delete_all(db)
            elif choice == "2":
                option_2_delete_selected(db)
            elif choice == "3":
                option_3_add_from_excel(db)
            elif choice == "4":
                option_4_add_manual(db)
            else:
                print("\n❌ Option invalide. Veuillez choisir entre 0 et 4.")
            
            if choice != "0":
                input("\nAppuyez sur Entrée pour continuer...")
                print("\n" * 2)
    
    except KeyboardInterrupt:
        print("\n\n👋 Interruption utilisateur. Au revoir !")
    except Exception as e:
        print(f"\n❌ ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
