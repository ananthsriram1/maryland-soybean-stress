import pandas as pd
import os
from IPython.display import display

# --- 1. Define File Paths ---
data_folder = 'data'
irrigated_file = os.path.join(data_folder, 'SoybeanIrrigatedAcres.csv')
yield_file = os.path.join(data_folder, 'Soybean_Yield_BU:Acre_By_County.csv')
planted_file = os.path.join(data_folder, 'Soybean_Acres_Planted_By_County.csv')
harvested_file = os.path.join(data_folder, 'Soybean_Acres_Harvested_By_County.csv')
production_file = os.path.join(data_folder, 'Soybean_Production_BU_By_County.csv')


# --- 2. Create a Reusable Cleaning Function ---
# This function now only selects Year, County, and Value.
def clean_nass_csv(file_path, value_column_name):
    df = pd.read_csv(file_path)
    df = df[['Year', 'County', 'Value']]
    df['Value'] = df['Value'].astype(str).str.replace(',', '')
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df = df.dropna(subset=['Value'])
    df = df.rename(columns={'Value': value_column_name})
    return df

# --- 3. Create a County-to-District Lookup Table ---
print("Creating a County to Ag District lookup table...")
# We only need to read one file to get this information. We'll use the yield file.
df_for_lookup = pd.read_csv(yield_file)
county_to_district_map = df_for_lookup[['County', 'Ag District']].drop_duplicates().reset_index(drop=True)
print("Lookup table created successfully.")
display(county_to_district_map.head())


# --- 4. Process Each File ---
print("\nProcessing NASS files...")
df_yield = clean_nass_csv(yield_file, 'Yield_BuAcre')
df_planted = clean_nass_csv(planted_file, 'Acres_Planted')
df_harvested = clean_nass_csv(harvested_file, 'Acres_Harvested')
df_production = clean_nass_csv(production_file, 'Production_BU')
df_irrigated = clean_nass_csv(irrigated_file, 'Irrigated_Acres')
print("All files cleaned.")


# --- 5. Merge the DataFrames into a Master Table ---
print("\nMerging data into a master table...")
master_df = df_yield
master_df = pd.merge(master_df, df_planted, on=['Year', 'County'], how='outer')
master_df = pd.merge(master_df, df_harvested, on=['Year', 'County'], how='outer')
master_df = pd.merge(master_df, df_production, on=['Year', 'County'], how='outer')
master_df = pd.merge(master_df, df_irrigated, on=['Year', 'County'], how='outer')

# --- 6. Add the Ag District information using the lookup table ---
final_df = pd.merge(master_df, county_to_district_map, on='County', how='left')


# --- 7. Handle Sparse Data and Finalize ---
final_df = final_df.sort_values(by=['County', 'Year']).reset_index(drop=True)
final_df['Irrigated_Acres'] = final_df.groupby('County')['Irrigated_Acres'].transform(lambda x: x.ffill())

# Reorder columns for clarity
final_df = final_df[['Year', 'County', 'Ag District', 'Acres_Planted', 'Acres_Harvested', 'Production_BU', 'Yield_BuAcre', 'Irrigated_Acres']]
print("Merging and final processing complete.")


# --- 8. Save and Display the Final Cleaned Dataset ---
output_file = os.path.join(data_folder, 'maryland_nass_data_cleaned_with_district.csv')
final_df.to_csv(output_file, index=False)

print(f"\n✅ Success! The final, clean dataset has been saved to: '{output_file}'")
print("\nPreview of the final master table:")
display(final_df.head(10))