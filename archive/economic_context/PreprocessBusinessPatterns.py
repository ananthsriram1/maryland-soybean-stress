import pandas as pd
import os
from IPython.display import display

# --- 1. SETUP ---
data_folder = 'data/business_patterns'
output_file = 'data/maryland_economic_sectors_cleaned.csv'

# --- 2. GET THE LIST OF CSV FILES ---
try:
    all_files = os.listdir(data_folder)
    csv_files = [f for f in all_files if 'Business Patterns' in f and f.endswith('.csv')]
    print(f"Found {len(csv_files)} Business Patterns CSV files to process.")
except FileNotFoundError:
    print(f"Error: The folder '{data_folder}' was not found.")
    csv_files = []

# --- 3. LOOP, READ, AND COMBINE THE FILES ---
if csv_files:
    all_data_list = []
    for filename in csv_files:
        file_path = os.path.join(data_folder, filename)
        df = pd.read_csv(file_path)
        df['County'] = df['Geographic Area Name (NAME)'].str.replace(', Maryland', '')
        all_data_list.append(df)

    combined_df = pd.concat(all_data_list, ignore_index=True)

    # --- 4. FILTER AND SELECT DATA ---
    # Keep only the rows for the TOTALS of each industry
    df_totals = combined_df[combined_df['Meaning of Employment size of establishments code (EMPSZES_LABEL)'] == 'All establishments'].copy()

    # Define our expanded list of relevant sectors
    sectors_to_keep = [
        'Agriculture, forestry, fishing and hunting', 
        'Manufacturing',
        'Construction',
        'Transportation and warehousing',
        'Real estate and rental and leasing'
    ]
    df_filtered = df_totals[df_totals['Meaning of NAICS code (NAICS2017_LABEL)'].isin(sectors_to_keep)]

    # Select and rename the columns we need
    df_cleaned = df_filtered[['Year (YEAR)', 'County', 'Meaning of NAICS code (NAICS2017_LABEL)', 'Number of establishments (ESTAB)']]
    df_cleaned.columns = ['Year', 'County', 'Sector', 'Establishments']
    
    df_cleaned['Establishments'] = pd.to_numeric(df_cleaned['Establishments'], errors='coerce')

    # --- 5. PIVOT TO WIDE FORMAT ---
    final_df = df_cleaned.pivot_table(
        index=['Year', 'County'], 
        columns='Sector', 
        values='Establishments'
    ).reset_index()

    # Clean up the column names
    final_df.columns = [col.replace(', ', '_').replace(' ', '_') for col in final_df.columns]
    
    # --- 6. SAVE AND DISPLAY ---
    final_df.to_csv(output_file, index=False)
    print(f"\n✅ Success! The final, clean economic data has been saved to: '{output_file}'")
    print("\nPreview of the final master table:")
    display(final_df.head(10))