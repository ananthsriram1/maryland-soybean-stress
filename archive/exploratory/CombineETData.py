import pandas as pd
import os
import re
from IPython.display import display


# =================================================================
#      PART 1: Combine the 48 Monthly ET Files
# =================================================================

# --- Setup ---
# Set the folder where your ET CSVs are located.
data_folder = 'data/et' 

# Set the name for the intermediate combined file.
output_file_combined = 'data/maryland_et_timeseries_combined_wide.csv'

# --- Get the list of CSV files ---
try:
    all_files = os.listdir(data_folder)
    csv_files = [f for f in all_files if f.startswith('md_county_soybean_') and f.endswith('.csv')]
    print(f"Found {len(csv_files)} ET CSV files to process.")
except FileNotFoundError:
    print(f"Error: The folder '{data_folder}' was not found.")
    csv_files = []

# --- Loop, Read, and Combine ---
if csv_files:
    all_data_list = []
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }

    for filename in csv_files:
        file_path = os.path.join(data_folder, filename)
        df = pd.read_csv(file_path)
        
        match = re.search(r'([a-zA-Z]{3,4})_?(\d{4})', filename)
        if match:
            month_abbr = match.group(1).lower()
            year = match.group(2)
            if month_abbr in month_map:
                date_str = f"{year}-{month_map[month_abbr]}"
                df['date'] = date_str
                all_data_list.append(df)

    if not all_data_list:
        print("\nERROR: No data was collected.")
    else:
        long_df = pd.concat(all_data_list, ignore_index=True)
        
        wide_df = long_df.pivot_table(index='NAME', columns='date', values='meanET', aggfunc='mean')
        wide_df = wide_df.sort_index(axis=1)
        wide_df.columns = ['ET_' + str(col) for col in wide_df.columns]
        
        wide_df.to_csv(output_file_combined)
        print(f"\n✅ Step 1 Complete: Combined ET data saved to '{output_file_combined}'")

# =================================================================
#      PART 2: Filter for Maryland-Only Counties
# =================================================================

# --- Define the master list of Maryland counties ---
maryland_counties_list = [
    'Allegany', 'Anne Arundel', 'Baltimore', 'Baltimore City', 'Calvert', 
    'Caroline', 'Carroll', 'Cecil', 'Charles', 'Dorchester', 'Frederick', 
    'Garrett', 'Harford', 'Howard', 'Kent', 'Montgomery', "Prince George's", 
    "Queen Anne's", 'Somerset', "St. Mary's", 'Talbot', 'Washington', 
    'Wicomico', 'Worcester'
]

# --- Define file paths ---
input_file_combined = output_file_combined
output_file_final = 'data/maryland_only_et_timeseries_FINAL.csv'

# --- Load and filter the combined data ---
try:
    combined_df = pd.read_csv(input_file_combined, index_col='NAME')
    print(f"\nSuccessfully loaded the combined ET data. Original shape: {combined_df.shape}")
    
    final_df = combined_df[combined_df.index.isin(maryland_counties_list)]
    print(f"Filtered down to Maryland counties. Final shape: {final_df.shape}")
    
    final_df.to_csv(output_file_final)
    print(f"\n✅ Step 2 Complete: Final, clean ET dataset saved to: '{output_file_final}'")
    
    print("\nPreview of the final, Maryland-only ET data:")
    display(final_df.head())
    
except FileNotFoundError:
    print(f"Error: The combined file was not found. Make sure Part 1 ran successfully.")