import pandas as pd
import os
from IPython.display import display

# --- 1. SETUP ---
# Define the path to the folder containing your 24 county precipitation CSVs.
precip_folder_path = 'data/precipitation'

# Define the name and path for the final combined output file.
output_file = 'data/maryland_precipitation_combined_wide.csv'

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

    for filename in csv_files:
        file_path = os.path.join(precip_folder_path, filename)
        
        # --- THIS IS THE FIX ---
        # Skip the first 3 rows (2 comment lines + 1 header line)
        # and manually assign the correct column names.
        df = pd.read_csv(file_path, skiprows=3, names=['Date', 'Value'])
        # --- END OF FIX ---
        
        # --- Feature Engineering ---
        county_name = filename.replace('.csv', '')
        df['County'] = county_name
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m').dt.strftime('%Y-%m')
        
        all_data_list.append(df)

    long_df = pd.concat(all_data_list, ignore_index=True)
    print("\nSuccessfully combined all files into a single long-format table.")

    # --- 4. PIVOT THE LONG DATAFRAME TO THE WIDE FORMAT ---
    print("Pivoting the precipitation table to a wide format...")
    wide_df = long_df.pivot_table(index='County', columns='Date', values='Value', aggfunc='mean')
    
    wide_df.columns = ['Precip_' + str(col) for col in wide_df.columns]
    print("Pivoting complete. Here is a preview of your combined table:")
    display(wide_df.head())

    # --- 5. SAVE THE FINAL WIDE DATAFRAME TO A NEW CSV ---
    wide_df.to_csv(output_file)
    print(f"\n✅ Success! The combined precipitation data has been saved to: '{output_file}'")