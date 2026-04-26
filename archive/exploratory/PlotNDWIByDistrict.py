import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- 1. Load your final, clean NDWI dataset ---
ndwi_file = 'data/maryland_ndwi_combined_wide.csv' # Make sure you've created this file
df_ndwi = pd.read_csv(ndwi_file, index_col='Name')

# --- 2. Define the counties for each agricultural district ---
district_counties = {
    'WESTERN': {'Allegany', 'Garrett'},
    'UPPER EASTERN SHORE': {'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'},
    'SOUTHERN': {'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"},
    'NORTH CENTRAL': {'Baltimore', 'Baltimore City', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 'Washington'},
    'LOWER EASTERN SHORE': {'Dorchester', 'Somerset', 'Wicomico', 'Worcester'}
}

# Universal color scheme for all plots - consistent across the entire analysis
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFEAA7'             # Yellow - Lowest development
}

# --- 3. Calculate the average NDWI for each agricultural district ---
district_averages = {}
for district, counties in district_counties.items():
    # Find counties that exist in the dataset
    available_counties = [county for county in counties if county in df_ndwi.index]
    if available_counties:
        district_averages[district] = df_ndwi.T[available_counties].mean(axis=1)
        # Convert index to datetime for proper plotting
        district_averages[district].index = pd.to_datetime(district_averages[district].index.str.replace('NDWI_', ''))

# --- 4. Plot the results ---
fig, ax = plt.subplots(figsize=(16, 8))

# Plot each district with its assigned color
for district, avg_data in district_averages.items():
    color = UNIVERSAL_DISTRICT_COLORS[district]
    ax.plot(avg_data.index, avg_data.values, 
            marker='o', linestyle='-', 
            color=color, label=district, 
            linewidth=2, markersize=4)

ax.set_title('Soybean Water Content (NDWI) by Agricultural District', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Average Soybean NDWI', fontsize=12)
ax.legend(fontsize=11, title='Agricultural District')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)

# Format x-axis to show years
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_minor_locator(mdates.MonthLocator([1, 7]))

plt.tight_layout()
plt.show()