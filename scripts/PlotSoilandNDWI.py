import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# --- 1. Load your datasets ---
print("Loading datasets...")
ndwi_file = 'data/maryland_ndwi_combined_wide.csv'
soil_file = 'data/maryland_only_soil_water_content_FINAL.csv'
nass_file = 'data/maryland_nass_data_cleaned_with_district.csv'

df_ndwi = pd.read_csv(ndwi_file, index_col='Name')
df_soil = pd.read_csv(soil_file)  # County is the first column, not index
df_nass = pd.read_csv(nass_file)
county_to_district = df_nass[['County', 'Ag District']].drop_duplicates()

print(f"NDWI data shape: {df_ndwi.shape}")
print(f"Soil data shape: {df_soil.shape}")
print(f"NASS data shape: {df_nass.shape}")

# --- 2. Standardize county names for merging ---
# Standardize county names in soil data
df_soil['County'] = df_soil['County'].str.title()
county_to_district['County'] = county_to_district['County'].str.title()

# --- 3. Calculate a growing season NDWI metric ---
print("Calculating growing season NDWI metrics...")
df_ndwi_long = df_ndwi.reset_index().melt(id_vars='Name', var_name='date', value_name='NDWI')
df_ndwi_long['date'] = pd.to_datetime(df_ndwi_long['date'].str.replace('NDWI_', ''))

# Calculate multiple growing season metrics
# Peak growing season (July-August)
gs_ndwi = df_ndwi_long[df_ndwi_long['date'].dt.month.isin([7, 8])]
avg_gs_ndwi = gs_ndwi.groupby('Name')['NDWI'].mean().reset_index()
avg_gs_ndwi = avg_gs_ndwi.rename(columns={'Name': 'County'})

# Full growing season (May-September)
full_gs_ndwi = df_ndwi_long[df_ndwi_long['date'].dt.month.isin([5, 6, 7, 8, 9])]
avg_full_gs_ndwi = full_gs_ndwi.groupby('Name')['NDWI'].mean().reset_index()
avg_full_gs_ndwi = avg_full_gs_ndwi.rename(columns={'Name': 'County'})

# Annual average
annual_ndwi = df_ndwi_long.groupby('Name')['NDWI'].mean().reset_index()
annual_ndwi = annual_ndwi.rename(columns={'Name': 'County'})

print(f"Peak growing season counties: {len(avg_gs_ndwi)}")
print(f"Full growing season counties: {len(avg_full_gs_ndwi)}")
print(f"Annual average counties: {len(annual_ndwi)}")

# --- 4. Universal color scheme for agricultural districts ---
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFEAA7'             # Yellow - Lowest development
}

# --- 5. Create multiple plots ---

# Plot 1: Peak Growing Season (July-August) NDWI vs Soil Water Content
print("\n--- Creating Plot 1: Peak Growing Season NDWI vs Soil Water Content ---")
plot_df1 = pd.merge(avg_gs_ndwi, df_soil, on='County', how='inner')
plot_df1 = pd.merge(plot_df1, county_to_district, on='County', how='inner')

plt.figure(figsize=(14, 10))
sns.scatterplot(data=plot_df1, x='avg_water_content', y='NDWI', 
                hue='Ag District', s=150, alpha=0.8, 
                palette=UNIVERSAL_DISTRICT_COLORS)
sns.regplot(data=plot_df1, x='avg_water_content', y='NDWI', 
            scatter=False, color='red', line_kws={'linewidth': 2})

# Calculate and display correlation
correlation = np.corrcoef(plot_df1['avg_water_content'], plot_df1['NDWI'])[0, 1]
plt.text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
         transform=plt.gca().transAxes, fontsize=12, 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.title('Soil Water Holding Capacity vs. Peak Growing Season NDWI\n(July-August)', fontsize=16)
plt.xlabel('Average Soil Water Holding Capacity', fontsize=12)
plt.ylabel('Average Peak Growing Season NDWI', fontsize=12)
plt.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()

# Plot 2: Full Growing Season (May-September) NDWI vs Soil Water Content
print("\n--- Creating Plot 2: Full Growing Season NDWI vs Soil Water Content ---")
plot_df2 = pd.merge(avg_full_gs_ndwi, df_soil, on='County', how='inner')
plot_df2 = pd.merge(plot_df2, county_to_district, on='County', how='inner')

plt.figure(figsize=(14, 10))
sns.scatterplot(data=plot_df2, x='avg_water_content', y='NDWI', 
                hue='Ag District', s=150, alpha=0.8, 
                palette=UNIVERSAL_DISTRICT_COLORS)
sns.regplot(data=plot_df2, x='avg_water_content', y='NDWI', 
            scatter=False, color='red', line_kws={'linewidth': 2})

# Calculate and display correlation
correlation2 = np.corrcoef(plot_df2['avg_water_content'], plot_df2['NDWI'])[0, 1]
plt.text(0.05, 0.95, f'Correlation: {correlation2:.3f}', 
         transform=plt.gca().transAxes, fontsize=12, 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.title('Soil Water Holding Capacity vs. Full Growing Season NDWI\n(May-September)', fontsize=16)
plt.xlabel('Average Soil Water Holding Capacity', fontsize=12)
plt.ylabel('Average Full Growing Season NDWI', fontsize=12)
plt.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()

# Plot 3: Annual Average NDWI vs Soil Water Content
print("\n--- Creating Plot 3: Annual Average NDWI vs Soil Water Content ---")
plot_df3 = pd.merge(annual_ndwi, df_soil, on='County', how='inner')
plot_df3 = pd.merge(plot_df3, county_to_district, on='County', how='inner')

plt.figure(figsize=(14, 10))
sns.scatterplot(data=plot_df3, x='avg_water_content', y='NDWI', 
                hue='Ag District', s=150, alpha=0.8, 
                palette=UNIVERSAL_DISTRICT_COLORS)
sns.regplot(data=plot_df3, x='avg_water_content', y='NDWI', 
            scatter=False, color='red', line_kws={'linewidth': 2})

# Calculate and display correlation
correlation3 = np.corrcoef(plot_df3['avg_water_content'], plot_df3['NDWI'])[0, 1]
plt.text(0.05, 0.95, f'Correlation: {correlation3:.3f}', 
         transform=plt.gca().transAxes, fontsize=12, 
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.title('Soil Water Holding Capacity vs. Annual Average NDWI', fontsize=16)
plt.xlabel('Average Soil Water Holding Capacity', fontsize=12)
plt.ylabel('Annual Average NDWI', fontsize=12)
plt.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()

# --- 6. Summary Statistics ---
print("\n--- Summary Statistics ---")
print(f"Peak Growing Season (Jul-Aug) Correlation: {correlation:.3f}")
print(f"Full Growing Season (May-Sep) Correlation: {correlation2:.3f}")
print(f"Annual Average Correlation: {correlation3:.3f}")

print(f"\nData points in each analysis:")
print(f"Peak Growing Season: {len(plot_df1)} counties")
print(f"Full Growing Season: {len(plot_df2)} counties")
print(f"Annual Average: {len(plot_df3)} counties")

# Show sample of merged data
print(f"\nSample of merged data (Peak Growing Season):")
print(plot_df1[['County', 'Ag District', 'avg_water_content', 'NDWI']].head(10))

print("\nSoil and NDWI analysis complete!")