#!/usr/bin/env python3
"""
Combine NOAA NCEI county-level monthly precipitation CSVs into a single wide table.

Distinct from analysis/preprocessing/combine_palmer_index.py: precipitation is
delivered by NCEI as one CSV per county (24 files for Maryland) using a
different filename and column convention than the Palmer indices, so the
combining logic is independent and is not parameterized through INDEX_CONFIG.

Inputs:
  data/Precipitation_Data_NOAA_97-25/<County>.csv  (24 county files)
    NCEI Climate at a Glance "monthly precipitation" county exports.
    Filenames Anne_Arundel, Baltimore_County, Baltimore_City, St Mary's are
    re-mapped to the canonical Maryland county names used elsewhere in the
    repo.

Outputs:
  data/maryland_precipitation_combined_wide.csv
    Wide format: one row per County, one column per YYYY-MM monthly value,
    aligned to the NASS-district county list.

Paper figures:
  - Feeds Figure 3 (annual + Jul-Sep precipitation overlay by district;
    analysis/figures/figure03_district_precip_decade_overlay.py).
  - Feeds the supporting precipitation/climatology figures and tables under
    analysis/figures/supporting/ and analysis/stress_analysis/.
"""

import pandas as pd
import os

# --- 1. SETUP ---
# Define the path to the folder containing your 24 county precipitation CSVs.
precip_folder_path = 'data/Precipitation_Data_NOAA_97-25'

# Define the name and path for the final combined output file.
output_file = 'data/maryland_precipitation_combined_wide.csv'


def main() -> None:
    # --- 2. GET THE LIST OF CSV FILES ---
    try:
        all_files = os.listdir(precip_folder_path)
        csv_files = [f for f in all_files if f.endswith('.csv')]
        print(f"Found {len(csv_files)} precipitation CSV files to process.")
    except FileNotFoundError:
        print(f"Error: The folder '{precip_folder_path}' was not found.")
        csv_files = []

    # --- 3. LOOP, READ, AND COMBINE THE FILES INTO A LONG DATAFRAME ---
    if csv_files:
        all_data_list = []

        filename_to_county = {
            "Anne_Arundel": "Anne Arundel",
            "Baltimore_County": "Baltimore",
            "Baltimore_City": "Baltimore City",
            "St Mary's": "St. Mary's",
        }

        for filename in csv_files:
            file_path = os.path.join(precip_folder_path, filename)

            # --- THIS IS THE FIX ---
            # Skip the first 3 rows (2 comment lines + 1 header line)
            # and manually assign the correct column names.
            df = pd.read_csv(file_path, skiprows=3, names=['Date', 'Value'])
            # --- END OF FIX ---

            # --- Feature Engineering ---
            raw_name = filename.replace('.csv', '')
            county_name = filename_to_county.get(raw_name, raw_name.replace("_", " "))
            df['County'] = county_name
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m', errors='coerce').dt.strftime('%Y-%m')

            all_data_list.append(df)

        long_df = pd.concat(all_data_list, ignore_index=True)
        print("\nSuccessfully combined all files into a single long-format table.")

        # --- 4. PIVOT THE LONG DATAFRAME TO THE WIDE FORMAT ---
        print("Pivoting the precipitation table to a wide format...")
        wide_df = long_df.pivot_table(index='County', columns='Date', values='Value', aggfunc='mean')

        wide_df.columns = ['Precip_' + str(col) for col in wide_df.columns]
        print("Pivoting complete.")

        # --- 5. SAVE THE FINAL WIDE DATAFRAME TO A NEW CSV ---
        wide_df.to_csv(output_file)
        print(f"\n✅ Success! The combined precipitation data has been saved to: '{output_file}'")


if __name__ == "__main__":
    main()