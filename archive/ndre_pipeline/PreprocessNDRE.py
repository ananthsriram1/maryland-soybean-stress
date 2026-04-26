import pandas as pd
from IPython.display import display

# --- 1. DEFINE THE MASTER LIST OF MARYLAND COUNTIES ---
# This list contains the 23 counties plus Baltimore City.
maryland_counties_list = [
    'Allegany', 'Anne Arundel', 'Baltimore', 'Baltimore City', 'Calvert', 
    'Caroline', 'Carroll', 'Cecil', 'Charles', 'Dorchester', 'Frederick', 
    'Garrett', 'Harford', 'Howard', 'Kent', 'Montgomery', "Prince George's", 
    "Queen Anne's", 'Somerset', "St. Mary's", 'Talbot', 'Washington', 
    'Wicomico', 'Worcester'
]

# --- 2. DEFINE FILE PATHS ---
# Input file: your combined NDRE data
input_file = 'data/maryland_soybean_ndre_timeseries_combined_wide.csv'
# Output file: the new, clean file that will be created
output_file = 'data/maryland_only_ndre_timeseries_FINAL.csv'

# --- 3. LOAD THE WIDE-FORMAT DATA ---
try:
    wide_df = pd.read_csv(input_file, index_col='NAME')
    print(f"Successfully loaded the combined NDRE data. Original shape: {wide_df.shape}")
except FileNotFoundError:
    print(f"Error: The input file was not found at: {input_file}")
    wide_df = None

# --- 4. FILTER THE DATAFRAME ---
if wide_df is not None:
    # Keep only the rows where the index (county name) is in our master list.
    final_df = wide_df[wide_df.index.isin(maryland_counties_list)]
    
    print(f"Filtered down to Maryland counties. Final shape: {final_df.shape}")

    # --- 5. SAVE THE FINAL, CLEAN CSV ---
    final_df.to_csv(output_file)
    print(f"\n✅ Success! The final, clean NDRE dataset has been saved to: '{output_file}'")

    # Display a preview of the final, clean table.
    print("\nPreview of the final, Maryland-only NDRE data:")
    display(final_df.head())