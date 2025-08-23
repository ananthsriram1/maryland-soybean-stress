import pandas as pd
import os
from IPython.display import display

# 1. Set the folder where your current index CSVs are located.
data_folder = 'data/pdsi' 

# 2. Set the name for the final combined output file.
output_file = 'data/maryland_pdsi_combined_wide.csv'

# 3. Set the prefix for the new column names (e.g., 'PDSI_').
column_prefix = 'PDSI_'

# =================================================================
#      THE REST OF THE SCRIPT STAYS THE SAME
# =================================================================

# --- Get the list of CSV files ---
try:
    all_files = os.listdir(data_folder)
    csv_files = [f for f in all_files if f.endswith('.csv')]
    print(f"Found {len(csv_files)} files in '{data_folder}' to process.")
except FileNotFoundError:
    print(f"Error: The folder '{data_folder}' was not found.")
    csv_files = []

# --- Loop, Read, and Combine the Files ---
if csv_files:
    all_data_list = []

    for filename in csv_files:
        file_path = os.path.join(data_folder, filename)
        
        # Read the CSV, skipping the single header row.
        df = pd.read_csv(file_path, skiprows=1)
        
        # Feature Engineering
        county_name = filename.replace('.csv', '')
        df['County'] = county_name
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m').dt.strftime('%Y-%m')
        
        all_data_list.append(df)

    long_df = pd.concat(all_data_list, ignore_index=True)
    print("\nSuccessfully combined all files into a single long-format table.")

    # --- Pivot the long dataframe to the wide format ---
    print(f"Pivoting the {column_prefix.strip('_')} table to a wide format...")
    wide_df = long_df.pivot_table(index='County', columns='Date', values='Value', aggfunc='mean')
    
    # Rename columns with the specified prefix.
    wide_df.columns = [column_prefix + str(col) for col in wide_df.columns]

    print("Pivoting complete. Here is a preview of your combined table:")
    display(wide_df.head())

    # --- Save the final wide dataframe to a new CSV ---
    wide_df.to_csv(output_file)
    print(f"\n✅ Success! The combined data has been saved to: '{output_file}'")
