import pandas as pd
import os
from datetime import datetime, timedelta

def calculate_30_360_days(start_date, end_date):
    """
    Calculate number of days between two dates using 30/360 convention
    """
    y1, m1, d1 = start_date.year, start_date.month, start_date.day
    y2, m2, d2 = end_date.year, end_date.month, end_date.day
    
    if d1 == 31:
        d1 = 30
    if d2 == 31 and d1 >= 30:
        d2 = 30
        
    return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1))

def calculate_yearly_amounts(start_date, total_amount, duration):
    """
    Calculate the amortization amounts for each year ensuring the total equals the transaction amount
    """
    yearly_amounts = {}
    total_days = duration * 360
    end_date = start_date + timedelta(days=int(total_days))
    daily_amount = total_amount / total_days
    
    # Pour chaque année concernée
    current_date = start_date
    remaining_amount = total_amount
    
    while current_date.year <= end_date.year:
        year = current_date.year
        year_end = min(datetime(year, 12, 31), end_date)
        
        # Calculer le nombre de jours pour cette année
        if year not in yearly_amounts:
            yearly_amounts[year] = 0
            
        days_in_year = calculate_30_360_days(current_date, year_end)
        amount = days_in_year * daily_amount
        
        # Pour la dernière année, ajuster pour avoir exactement le total
        if year == end_date.year:
            amount = remaining_amount
        
        yearly_amounts[year] = amount
        remaining_amount -= amount
        
        # Passer à l'année suivante
        current_date = datetime(year + 1, 1, 1)
    
    return yearly_amounts

def map_category_to_param(category):
    """Map level 1 categories to parameter names"""
    mapping = {
        'meubles': 'ammortissement meubles',
        'travaux': 'ammortissement travaux',
        'pret banque - construction': 'ammortissement construction',
        'pret banque - terrain': 'ammortissement terrain'
    }
    return mapping.get(category)

def calculate_amortization():
    # Create the output directory if it doesn't exist
    output_dir = '../data/output/reports'
    os.makedirs(output_dir, exist_ok=True)
    
    # Read input files
    df = pd.read_csv('../data/output/all_trades_extra.csv', sep=';', encoding='utf-8')
    params_df = pd.read_excel('../data/input/app_data/parametres.xlsx')
    
    # Convert parameters to dictionary
    params_dict = {}
    for _, row in params_df.iterrows():
        param_name = row.iloc[0]
        param_value = row.iloc[1]
        if pd.notnull(param_value):
            try:
                params_dict[param_name] = float(param_value)
            except (ValueError, TypeError):
                print(f"Warning: Invalid value for parameter {param_name}")
    
    # Filter amortization transactions
    amort_df = df[df['level 2'] == 'ammortissements'].copy()
    amort_df['Date'] = pd.to_datetime(amort_df['Date'], format='%d/%m/%Y')
    
    # Initialize results
    results = {}
    
    # Process each category
    for category in ['meubles', 'travaux', 'pret banque - construction', 'pret banque - terrain']:
        category_df = amort_df[amort_df['level 1'] == category]
        
        if category_df.empty:
            continue
            
        param_name = map_category_to_param(category)
        if param_name not in params_dict:
            print(f"Warning: No amortization parameter found for {category}")
            continue
            
        duration = params_dict[param_name]
        if duration <= 0:
            print(f"Warning: Invalid duration ({duration}) for {category}")
            continue
        
        # Process each transaction
        for _, transaction in category_df.iterrows():
            start_date = transaction['Date']
            total_amount = abs(float(transaction['Quantité']))
            
            # Calculate yearly amounts for this transaction
            yearly_amounts = calculate_yearly_amounts(start_date, total_amount, duration)
            
            # Add to results
            for year, amount in yearly_amounts.items():
                if year not in results:
                    results[year] = {}
                if category not in results[year]:
                    results[year][category] = 0
                results[year][category] -= amount  # Negative as it's an expense
    
    # Convert results to DataFrame
    if results:
        amort_df = pd.DataFrame(results).fillna(0)
        
        # Add row with totals
        amort_df.loc['Total'] = amort_df.sum()
        
        # Sort columns chronologically
        amort_df = amort_df.reindex(sorted(amort_df.columns), axis=1)
        
        # Reset index to make categories a regular column
        amort_df = amort_df.reset_index()
        amort_df = amort_df.rename(columns={'index': 'Type'})
        
        # Round all numeric values to 2 decimals
        numeric_columns = amort_df.select_dtypes(include=['float64', 'int64']).columns
        amort_df[numeric_columns] = amort_df[numeric_columns].round(2)
        
        # Save to CSV
        output_file = os.path.join(output_dir, 'amortissement.csv')
        amort_df.to_csv(output_file, sep=';', index=False)
        
        print(f"Amortization file created successfully at {output_file}")
    else:
        print("No amortization data found")

if __name__ == "__main__":
    calculate_amortization()