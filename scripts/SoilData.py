# This script is used to filter the soil data to only include the counties in Maryland      

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. Load Your Datasets ---
soil_file = 'data/md_county_soil_water_content.csv'
soil_df = pd.read_csv(soil_file)

nass_file = 'data/maryland_nass_data_cleaned_with_district.csv'
district_map_df = pd.read_csv(nass_file)
county_to_district = district_map_df[['County', 'Ag District']].drop_duplicates()

# --- 2. Standardize and Merge ---
soil_df = soil_df.rename(columns={'NAME': 'County'})
soil_df['County'] = soil_df['County'].str.upper().str.strip()
county_to_district['County'] = county_to_district['County'].str.upper().str.strip()

soil_with_districts = pd.merge(soil_df, county_to_district, on='County', how='left')

# --- 3. Calculate Average Water Content per District ---
district_avg_soil = soil_with_districts.groupby('Ag District')['avg_water_content'].mean().sort_values()

# --- 4. Create the Bar Chart ---
plt.figure(figsize=(10, 6))
district_avg_soil.plot(kind='barh', color=sns.color_palette("viridis", len(district_avg_soil)))
plt.title('Average Soil Water Holding Capacity by Ag District', fontsize=16)
plt.xlabel('Average Water Content (10^-3 cm³/cm³)', fontsize=12)
plt.ylabel('Agricultural District', fontsize=12)
plt.grid(True, axis='x', linestyle='--', linewidth=0.5)
plt.show()