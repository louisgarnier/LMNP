import pandas as pd
import os
import logging
from datetime import datetime

def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'add_extra_columns_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def find_best_mapping(transaction_name, mapping_df):
    """
    Trouve le meilleur mapping pour un nom de transaction donné
    Retourne directement les valeurs de level 1, 2 et 3
    """
    best_match = None
    best_length = 0
    
    # Recherche du meilleur mapping
    for _, row in mapping_df.iterrows():
        mapping_name = row['nom']
        
        # Cas spécial pour PRLV SEPA
        if 'PRLV SEPA' in transaction_name and 'PRLV SEPA' in mapping_name:
            if (transaction_name.startswith(mapping_name) and 
                len(mapping_name) > best_length):
                best_match = row
                best_length = len(mapping_name)
                
        # Cas spécial pour VIR STRIPE
        elif 'VIR STRIPE' in transaction_name and mapping_name == 'VIR STRIPE':
            best_match = row
            break
            
        # Cas général
        elif (transaction_name.startswith(mapping_name) and 
              len(mapping_name) > best_length):
            best_match = row
            best_length = len(mapping_name)
    
    if best_match is not None:
        return best_match['level 1'], best_match['level 2'], best_match['level 3']
    return None, None, None

def apply_intelligent_mapping(df, mapping_df, logger):
    """
    Applique le mapping intelligent aux transactions
    """
    # Créer des colonnes vides pour les niveaux
    df['level 1'] = None
    df['level 2'] = None
    df['level 3'] = None
    
    # Pour chaque transaction unique
    unique_names = df['nom'].unique()
    mapped_count = 0
    unmapped = []
    
    for name in unique_names:
        level1, level2, level3 = find_best_mapping(name, mapping_df)
        if level1 is not None:
            mask = df['nom'] == name
            df.loc[mask, 'level 1'] = level1
            df.loc[mask, 'level 2'] = level2
            df.loc[mask, 'level 3'] = level3
            mapped_count += 1
            logger.info(f"Mapping trouvé pour '{name}': {level1} / {level2} / {level3}")
        else:
            unmapped.append(name)
            logger.warning(f"Pas de mapping trouvé pour: '{name}'")
    
    logger.info(f"Nombre de types de transactions mappées: {mapped_count}")
    logger.info(f"Nombre de types de transactions non mappées: {len(unmapped)}")
    
    return df, unmapped

def add_extra_columns():
    logger = setup_logging()
    
    try:
        # Définition des chemins
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, '..', 'data', 'output')
        mapping_dir = os.path.join(script_dir, '..', 'data', 'mapping')
        
        input_file = os.path.join(output_dir, 'all_trades.csv')
        output_file = os.path.join(output_dir, 'all_trades_extra.csv')
        mapping_file = os.path.join(mapping_dir, 'mapping.xlsx')
        
        logger.info(f"Lecture du fichier de transactions: {input_file}")
        
        # Lecture du fichier CSV des transactions
        df = pd.read_csv(input_file, sep=';')
        initial_count = len(df)
        logger.info(f"Nombre de transactions lues: {initial_count}")
        
        # Lecture du fichier de mapping
        logger.info(f"Lecture du fichier de mapping: {mapping_file}")
        mapping_df = pd.read_excel(mapping_file)
        logger.info(f"Colonnes trouvées dans le mapping: {list(mapping_df.columns)}")
        
        # Renommer les colonnes du mapping si nécessaire
        column_mapping = {
            mapping_df.columns[0]: 'nom',  # Première colonne -> nom
            'level 1': 'level 1',
            'level 2': 'level 2', 
            'level 3': 'level 3'
        }
        mapping_df = mapping_df.rename(columns=column_mapping)
        
        # Conversion de la colonne Date en datetime
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
        
        # Ajout des colonnes mois et année
        df['mois'] = df['Date'].dt.month
        df['annee'] = df['Date'].dt.year
        
        # Application du mapping intelligent
        logger.info("Application du mapping intelligent...")
        df_final, unmapped = apply_intelligent_mapping(df, mapping_df, logger)
        
        # Vérification du nombre de lignes
        final_count = len(df_final)
        if final_count != initial_count:
            raise ValueError(f"Erreur: le nombre de lignes a changé! Initial: {initial_count}, Final: {final_count}")
        
        # Sauvegarder la liste des transactions non mappées
        if unmapped:
            missing_file = os.path.join(output_dir, 'missing_mappings.csv')
            pd.DataFrame({'nom': sorted(unmapped)}).to_csv(missing_file, index=False, encoding='utf-8')
            logger.info(f"Liste des noms non mappés sauvegardée dans: {missing_file}")
        
        # Reconversion de la date au format original
        df_final['Date'] = df_final['Date'].dt.strftime('%d/%m/%Y')
        
        # Réorganisation des colonnes
        columns_order = ['Date', 'mois', 'annee', 'Quantité', 'nom', 'solde', 'level 1', 'level 2', 'level 3']
        df_final = df_final[columns_order]
        
        # Sauvegarde du fichier
        df_final.to_csv(output_file, sep=';', index=False, float_format='%.2f')
        logger.info(f"Fichier créé avec succès: {output_file}")
        
        # Statistiques
        logger.info("\nStatistiques:")
        logger.info(f"Nombre total de transactions: {len(df_final)}")
        logger.info(f"Transactions avec mapping: {len(df_final.dropna(subset=['level 1']))}")
        logger.info(f"Transactions sans mapping: {df_final['level 1'].isna().sum()}")
        logger.info(f"Taux de couverture: {(len(df_final.dropna(subset=['level 1'])) / len(df_final) * 100):.2f}%")
        
        logger.info("\nCatégories level 1 trouvées:")
        for cat in sorted(df_final['level 1'].dropna().unique()):
            count = len(df_final[df_final['level 1'] == cat])
            logger.info(f"- {cat}: {count} transactions")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}")
        logger.exception("Détails de l'erreur:")
        raise

if __name__ == "__main__":
    add_extra_columns()