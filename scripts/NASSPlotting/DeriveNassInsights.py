import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display

# =================================================================
#      SETUP: Load and Prepare the Master NASS Dataset
# =================================================================
# This script assumes you have already run the preprocessing script to create this file.
file_path = 'data/maryland_nass_data_cleaned_with_district.csv'
df = pd.read_csv(file_path)

print("--- NASS Data Visualization Suite ---")
display(df.head())

# =================================================================
#      PLOT 1: Total Acres Planted vs. Harvested Over Time
# =================================================================
# Insight: This shows the overall trend in soybean farming and highlights years
# where a significant number of planted acres were not harvested (a sign of widespread issues).

print("\n--- Generating Plot 1: Acres Planted vs. Harvested ---")
statewide_acres = df.groupby('Year')[['Acres_Planted', 'Acres_Harvested']].sum()

plt.figure(figsize=(12, 7))
plt.plot(statewide_acres.index, statewide_acres['Acres_Planted'], marker='o', linestyle='-', label='Acres Planted')
plt.plot(statewide_acres.index, statewide_acres['Acres_Harvested'], marker='s', linestyle='--', label='Acres Harvested')
plt.title('Total Soybean Acres Planted vs. Harvested in Maryland (2014-2024)', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Total Acres', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.xticks(statewide_acres.index, rotation=45)
plt.tight_layout()
plt.show()


# =================================================================
#      PLOT 2: Yield (Bu/Acre) by Agricultural District
# =================================================================
# Insight: This is a key plot to visualize the productivity differences
# between the agricultural districts over time.

print("\n--- Generating Plot 2: Yield by Agricultural District ---")
yield_by_district = df.groupby(['Year', 'Ag District'])['Yield_BuAcre'].mean().unstack()

plt.figure(figsize=(12, 7))
for district in yield_by_district.columns:
    plt.plot(yield_by_district.index, yield_by_district[district], marker='o', linestyle='-', label=district)
plt.title('Average Soybean Yield by Agricultural District (2014-2024)', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Yield (Bushels / Acre)', fontsize=12)
plt.legend(title='Ag District', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.xticks(yield_by_district.index, rotation=45)
plt.tight_layout()
plt.show()


# =================================================================
#      PLOT 3: Total Production vs. Average Yield (Statewide)
# =================================================================
# Insight: This helps to understand if total production is driven more by
# increases in yield (better farming) or increases in acreage (more farming).

print("\n--- Generating Plot 3: Total Production vs. Average Yield ---")
statewide_summary = df.groupby('Year').agg({
    'Production_BU': 'sum',
    'Yield_BuAcre': 'mean'
})

fig, ax1 = plt.subplots(figsize=(12, 7))

# Plot Production on the left Y-axis
color = 'tab:blue'
ax1.set_xlabel('Year')
ax1.set_ylabel('Total Production (Bushels)', color=color, fontsize=12)
ax1.bar(statewide_summary.index, statewide_summary['Production_BU'], color=color, alpha=0.6, label='Total Production')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_xticks(statewide_summary.index)
ax1.tick_params(axis='x', rotation=45)

# Create a second Y-axis for Yield
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Average Yield (Bushels / Acre)', color=color, fontsize=12)
ax2.plot(statewide_summary.index, statewide_summary['Yield_BuAcre'], color=color, marker='o', linestyle='--', label='Average Yield')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
plt.title('Statewide Soybean Production vs. Average Yield', fontsize=16)
plt.show()


# =================================================================
#      PLOT 4: Irrigation Trends (Census Years)
# =================================================================
# Insight: This directly visualizes the key variable for your hypothesis,
# showing which districts rely most heavily on irrigation.

print("\n--- Generating Plot 4: Irrigation Trends by District ---")
# Filter for only the census years where irrigation data is available
irrigation_data = df[df['Year'].isin([2012, 2017, 2022])].copy()

# Calculate the percentage of harvested acres that are irrigated
irrigation_data['Pct_Irrigated'] = (irrigation_data['Irrigated_Acres'] / irrigation_data['Acres_Harvested']) * 100

# Group by year and district
irrigation_summary = irrigation_data.groupby(['Year', 'Ag District'])['Pct_Irrigated'].mean().unstack()

# Create a grouped bar chart
irrigation_summary.plot(kind='bar', figsize=(14, 8), width=0.8)
plt.title('Percentage of Harvested Soybean Acres that are Irrigated (Census Years)', fontsize=16)
plt.xlabel('Census Year', fontsize=12)
plt.ylabel('Percent of Acres Irrigated (%)', fontsize=12)
plt.xticks(rotation=0)
plt.legend(title='Ag District')
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()