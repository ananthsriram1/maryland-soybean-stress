import pandas as pd
import os
import re

# =================================================================
#      SETUP: Update these variables if your folder names are different
# =================================================================
# 1. Set the folder where your NDRE CSVs are located.
data_folder = 'data/ndre' 

# 2. Set the name for the final combined output file.
output_file = 'data/maryland_soybean_ndre_timeseries_combined_wide.csv'

# 3. Set the prefix for the new column names
column_prefix = 'NDRE_'

# =================================================================
#      The rest of the script handles the processing
# =================================================================

# --- Get the list of CSV files ---
try:
    all_files = os.listdir(data_folder)
    # MODIFIED: Looks for your new NDRE filenames
    csv_files = [f for f in all_files if f.startswith('md_county_soybean_ndre_') and f.endswith('.csv')]
    print(f"Found {len(csv_files)} NDRE CSV files to process.")
except FileNotFoundError:
    print(f"Error: The folder '{data_folder}' was not found.")
    csv_files = []

# --- Loop, Read, and Combine the Files ---
if csv_files:
    all_data_list = []

    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }

    for filename in csv_files:
        file_path = os.path.join(data_folder, filename)
        df = pd.read_csv(file_path)
        
        # Robustly find the month and year in the filename
        match = re.search(r'([a-zA-Z]{3,4})_?(\d{4})', filename)
        if match:
            month_abbr = match.group(1).lower()
            year = match.group(2)
            if month_abbr in month_map:
                date_str = f"{year}-{month_map[month_abbr]}"
                df['date'] = date_str
                all_data_list.append(df)

    # --- Combine, Pivot, and Save ---
    if not all_data_list:
        print("\nERROR: No data was collected. Please check filenames.")
    else:
        long_df = pd.concat(all_data_list, ignore_index=True)
        print(f"\nSuccessfully created long_df. Shape: {long_df.shape}")

        print("Pivoting the NDRE table to a wide format...")
        # MODIFIED: Uses the 'meanSoybeanNDRE' column
        wide_df = long_df.pivot_table(index='NAME', columns='date', values='meanSoybeanNDRE', aggfunc='mean')
        
        wide_df = wide_df.sort_index(axis=1)
        wide_df.columns = [column_prefix + str(col) for col in wide_df.columns]

        print("Pivoting complete. Final table shape:", wide_df.shape)
        
        wide_df.to_csv(output_file)
        print(f"\n✅ Success! The combined NDRE data has been saved to: '{output_file}'")