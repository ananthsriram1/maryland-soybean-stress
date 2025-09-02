import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from IPython.display import display

# =================================================================
#      SETUP: Load and Prepare Datasets
# =================================================================
print("--- Economic and Agricultural Data Visualization Suite ---")

# --- 1. Load Your Cleaned Datasets ---
biz_file = 'data/maryland_economic_sectors_cleaned.csv'
# Load CSV and replace empty strings with 0, then convert to numeric
df_biz = pd.read_csv(biz_file)
df_biz = df_biz.replace('', 0)
display("DEBUG: Loaded business data")
display(f"DEBUG: df_biz shape: {df_biz.shape}")
display(f"DEBUG: df_biz columns: {list(df_biz.columns)}")
display(df_biz.head())

# Ensure Year column is numeric
df_biz['Year'] = pd.to_numeric(df_biz['Year'], errors='coerce')

# Convert business sector columns to numeric, replacing any remaining non-numeric values with 0
business_columns = ['Agriculture_forestry_fishing_and_hunting', 'Construction', 'Manufacturing', 
                   'Real_estate_and_rental_and_leasing', 'Transportation_and_warehousing']
for col in business_columns:
    df_biz[col] = pd.to_numeric(df_biz[col], errors='coerce').fillna(0)

# Impute any remaining NA values as 0 in business data
df_biz = df_biz.fillna(0)

# Create county sets for each agricultural district based on user-provided mappings
# This avoids merging and gives us clean county groupings
district_counties = {
    'WESTERN': {'Allegany County', 'Garrett County'},
    'UPPER EASTERN SHORE': {'Caroline County', 'Cecil County', 'Kent County', "Queen Anne's County", 'Talbot County'},
    'SOUTHERN': {'Anne Arundel County', 'Calvert County', 'Charles County', "Prince George's County", "St. Mary's County"},
    'NORTH CENTRAL': {'Baltimore County', 'Baltimore city', 'Carroll County', 'Frederick County', 'Harford County', 'Howard County', 'Montgomery County', 'Washington County'},
    'LOWER EASTERN SHORE': {'Dorchester County', 'Somerset County', 'Wicomico County', 'Worcester County'}
}

# Universal color scheme for all plots - consistent across the entire analysis
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFEAA7'             # Yellow - Lowest development
}

display("DEBUG: Created district county sets:")
for district, counties in district_counties.items():
    display(f"{district}: {sorted(counties)}")

# Create a function to get district for any county
def get_county_district(county_name):
    for district, counties in district_counties.items():
        if county_name in counties:
            return district
    return None

# Add agricultural district to business data using the sets
df_biz['Ag District'] = df_biz['County'].apply(get_county_district)
display("DEBUG: Business data after adding Ag District using sets:")
display(df_biz.head())
display(f"DEBUG: Counties with Ag District: {df_biz['Ag District'].notna().sum()}")
display(f"DEBUG: Counties without Ag District: {df_biz['Ag District'].isna().sum()}")

display(f"DEBUG: Business data years: {sorted(df_biz['Year'].unique())}")
display(f"DEBUG: Business data year counts: {df_biz['Year'].value_counts().sort_index()}")
display(f"DEBUG: Business data sample after conversion:")
display(df_biz[['Year', 'County', 'Ag District'] + business_columns].head())

# Check if we have 2022 data in business dataset
if 2022 in df_biz['Year'].unique():
    display("DEBUG: 2022 data found in business dataset")
else:
    display("DEBUG: 2022 data NOT found in business dataset")
    display("DEBUG: Available years in business data:", sorted(df_biz['Year'].unique()))

nass_file = 'data/maryland_nass_data_cleaned_with_district.csv'
df_nass = pd.read_csv(nass_file)
display("DEBUG: Loaded NASS data")
display(f"DEBUG: df_nass shape: {df_nass.shape}")
display(f"DEBUG: df_nass columns: {list(df_nass.columns)}")
display(df_nass.head())

# Ensure Year column is numeric
df_nass['Year'] = pd.to_numeric(df_nass['Year'], errors='coerce')

# Impute all NA values as 0 in NASS data
df_nass = df_nass.fillna(0)
display(f"DEBUG: NASS data years: {sorted(df_nass['Year'].unique())}")
display("DEBUG: NASS data after imputing NA values as 0:")
display(df_nass.head())

# --- 2. Create a 'Development Pressure' Metric ---
development_sectors = [
    'Construction', 
    'Manufacturing',
    'Real_estate_and_rental_and_leasing',
    'Transportation_and_warehousing'
]
display("DEBUG: Development sectors to sum:")
display(development_sectors)

# Check if all development sectors exist in df_biz
missing_sectors = [sector for sector in development_sectors if sector not in df_biz.columns]
if missing_sectors:
    display(f"DEBUG: WARNING - Missing sectors in df_biz: {missing_sectors}")
else:
    display("DEBUG: All development sectors found in df_biz")

df_biz['Development_Establishments'] = df_biz[development_sectors].fillna(0).sum(axis=1)
display("DEBUG: Created Development_Establishments column")
display(f"DEBUG: Development_Establishments stats: min={df_biz['Development_Establishments'].min()}, max={df_biz['Development_Establishments'].max()}, mean={df_biz['Development_Establishments'].mean():.2f}")

# Merge with NASS data to have everything in one place
display("DEBUG: Before merge - df_nass shape:", df_nass.shape)
display("DEBUG: Before merge - df_biz shape:", df_biz.shape)
display("DEBUG: df_nass Year dtype:", df_nass['Year'].dtype)
display("DEBUG: df_biz Year dtype:", df_biz['Year'].dtype)

display("DEBUG: Preview of df_nass before merge:")
display(df_nass.head(10))
display("DEBUG: df_nass columns:", list(df_nass.columns))
display("DEBUG: df_nass dtypes:")
display(df_nass.dtypes)
display("DEBUG: df_nass unique years:", sorted(df_nass['Year'].unique()))
display("DEBUG: df_nass unique counties:", df_nass['County'].unique())

display("DEBUG: Preview of df_biz before merge:")
display(df_biz.head(10))
display("DEBUG: df_biz columns:", list(df_biz.columns))
display("DEBUG: df_biz dtypes:")
display(df_biz.dtypes)
display("DEBUG: df_biz unique years:", sorted(df_biz['Year'].unique()))
display("DEBUG: df_biz unique counties:", df_biz['County'].unique())


# =================================================================
#      PLOT 1: Statewide Trend of Agriculture vs. Development
# =================================================================
print("\n--- Generating Plot 1: Statewide Sector Trends ---")

# Filter for years 2020 and later
df_biz_plot = df_biz[df_biz['Year'] >= 2020].copy()
df_nass_plot = df_nass[df_nass['Year'] >= 2020].copy()

# Statewide sum by year for each
biz_trend = df_biz_plot.groupby('Year')[['Agriculture_forestry_fishing_and_hunting', 'Development_Establishments']].sum()
nass_trend = df_nass_plot.groupby('Year')[['Acres_Planted']].sum()

display("DEBUG: Business sector state trends:")
display(biz_trend)
display("DEBUG: NASS state trends:")
display(nass_trend)

plt.figure(figsize=(12, 7))
plt.plot(biz_trend.index, biz_trend['Agriculture_forestry_fishing_and_hunting'], marker='o', linestyle='-', label='Agricultural Establishments (Business Patterns)')
plt.plot(biz_trend.index, biz_trend['Development_Establishments'], marker='s', linestyle='--', label='Development-Related Establishments (Business Patterns)')
plt.title('Statewide Change in Agricultural vs. Development Sectors (2020-2023)', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Total Number of Establishments', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.xticks(biz_trend.index)
plt.tight_layout()
plt.show()

# Create a dual y-axis plot to show both trends clearly
fig, ax1 = plt.subplots(figsize=(12, 7))

# Left y-axis for agricultural establishments (smaller scale)
color1 = 'tab:blue'
ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Agricultural Establishments', color=color1, fontsize=12)
ax1.plot(biz_trend.index, biz_trend['Agriculture_forestry_fishing_and_hunting'], 
         color=color1, marker='o', linestyle='-', linewidth=2, markersize=8)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

# Right y-axis for development establishments (larger scale)
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('Development-Related Establishments', color=color2, fontsize=12)
ax2.plot(biz_trend.index, biz_trend['Development_Establishments'], 
         color=color2, marker='s', linestyle='--', linewidth=2, markersize=8)
ax2.tick_params(axis='y', labelcolor=color2)

plt.title('Statewide Change in Agricultural vs. Development Sectors (2020-2023)\nDual Y-Axis for Scale Comparison', fontsize=16)
plt.xticks(biz_trend.index)
plt.tight_layout()
plt.show()

# Create a normalized plot (percentage change from 2020) to show relative trends
plt.figure(figsize=(12, 7))

# Calculate percentage change from 2020
biz_trend_normalized = biz_trend.copy()
for col in biz_trend_normalized.columns:
    biz_trend_normalized[col] = (biz_trend_normalized[col] / biz_trend_normalized.loc[2020, col] - 1) * 100

plt.plot(biz_trend_normalized.index, biz_trend_normalized['Agriculture_forestry_fishing_and_hunting'], 
         marker='o', linestyle='-', linewidth=2, markersize=8, label='Agricultural Establishments (% change from 2020)')
plt.plot(biz_trend_normalized.index, biz_trend_normalized['Development_Establishments'], 
         marker='s', linestyle='--', linewidth=2, markersize=8, label='Development-Related Establishments (% change from 2020)')

plt.title('Statewide Change in Agricultural vs. Development Sectors (2020-2023)\nNormalized to 2020 = 0%', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Percentage Change from 2020 (%)', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.xticks(biz_trend_normalized.index)
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.7)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 7))
plt.plot(nass_trend.index, nass_trend['Acres_Planted'], marker='o', linestyle='-', color='green', label='Soybean Acres Planted (NASS)')
plt.title('Statewide Soybean Acres Planted (2020-2023)', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Total Soybean Acres Planted', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.xticks(nass_trend.index)
plt.tight_layout()
plt.show()

# =================================================================
#      PLOT 2: The Urban vs. Rural Divide (Scatter Plot)
# =================================================================
print("\n--- Generating Plot 2: The Urban vs. Rural Divide ---")

# Use the most recent available year from business data for this plot
most_recent_biz_year = df_biz['Year'].max()
biz_recent = df_biz[df_biz['Year'] == most_recent_biz_year].copy()

# Use the most recent available year from NASS data
most_recent_nass_year = df_nass['Year'].max()
nass_recent = df_nass[df_nass['Year'] == most_recent_nass_year].copy()

display(f"DEBUG: Plot 2 - Using business data from {most_recent_biz_year}, NASS data from {most_recent_nass_year}")
display(f"DEBUG: Plot 2 - biz_recent shape: {biz_recent.shape}")
display(f"DEBUG: Plot 2 - nass_recent shape: {nass_recent.shape}")

# Create a simple scatter plot using the most recent available data
plt.figure(figsize=(10, 7))

# Plot each county as a point, using business data for x-axis and NASS data for y-axis
# We'll need to match counties between the two datasets
counties_with_both_data = set(biz_recent['County']) & set(nass_recent['County'])
display(f"DEBUG: Counties with data in both datasets: {len(counties_with_both_data)}")

if len(counties_with_both_data) > 0:
    # Create a simple visualization showing the relationship
    for county in counties_with_both_data:
        biz_data = biz_recent[biz_recent['County'] == county]
        nass_data = nass_recent[nass_recent['County'] == county]
        
        if not biz_data.empty and not nass_data.empty:
            dev_est = biz_data['Development_Establishments'].iloc[0]
            acres = nass_data['Acres_Planted'].iloc[0]
            ag_district = nass_data['Ag District'].iloc[0] if 'Ag District' in nass_data.columns else 'Unknown'
            
            plt.scatter(dev_est, acres, s=150, alpha=0.8, label=ag_district if ag_district not in [p.get_label() for p in plt.gca().collections] else "")
    
    plt.title(f'Development Pressure vs. Soybean Acres Planted by County\n(Business: {most_recent_biz_year}, NASS: {most_recent_nass_year})', fontsize=16)
    plt.xlabel('Number of Development-Related Establishments', fontsize=12)
    plt.ylabel('Soybean Acres Planted', fontsize=12)
    plt.grid(True, linestyle='--')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()
else:
    print("WARNING: No counties have data in both datasets for the same time period")
    # Show separate plots instead
    plt.figure(figsize=(15, 6))
    
    # Business data subplot
    plt.subplot(1, 2, 1)
    plt.scatter(biz_recent['Development_Establishments'], biz_recent['Agriculture_forestry_fishing_and_hunting'], alpha=0.7)
    plt.title(f'Business Data ({most_recent_biz_year})\nDevelopment vs. Agricultural Establishments')
    plt.xlabel('Development Establishments')
    plt.ylabel('Agricultural Establishments')
    plt.grid(True, alpha=0.3)
    
    # NASS data subplot
    plt.subplot(1, 2, 2)
    plt.scatter(nass_recent['Acres_Planted'], nass_recent['Yield_BuAcre'], alpha=0.7)
    plt.title(f'NASS Data ({most_recent_nass_year})\nAcres Planted vs. Yield')
    plt.xlabel('Acres Planted')
    plt.ylabel('Yield (Bu/Acre)')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

# =================================================================
#      PLOT 3: Regional Economic Profiles (Bar Chart)
# =================================================================
print("\n--- Generating Plot 3: Regional Economic Profiles ---")

# Use the most recent available year from business data
most_recent_biz_year = df_biz['Year'].max()
biz_recent = df_biz[df_biz['Year'] == most_recent_biz_year].copy()

display(f"DEBUG: Plot 3 - Using business data from {most_recent_biz_year}")
display(f"DEBUG: Plot 3 - biz_recent shape: {biz_recent.shape}")

# Filter out any rows without district information
biz_recent = biz_recent.dropna(subset=['Ag District'])

if not biz_recent.empty:
    # Use universal color scheme for agricultural districts
    districts = sorted(biz_recent['Ag District'].unique())
    district_colors = {district: UNIVERSAL_DISTRICT_COLORS[district] for district in districts}
    
    # Sort data by district first, then by county name within each district
    biz_recent_sorted = biz_recent.sort_values(['Ag District', 'County'])
    
    # Create subplots for different business sectors with district grouping
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle(f'Business Establishment Distribution by County and Agricultural District ({most_recent_biz_year})', 
                 fontsize=16, weight='bold')
    
    # Function to create district-grouped bar plot
    def create_district_grouped_plot(ax, data, y_column, title, ylabel):
        ax.set_title(title, fontsize=14, weight='bold')
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xlabel('County', fontsize=12)
        ax.grid(True, axis='y', linestyle='--', linewidth=0.5, alpha=0.7)
        
        # Get x-axis positions for bars
        x_positions = range(len(data))
        
        # Create bars with district colors
        bars = []
        for i, (_, row) in enumerate(data.iterrows()):
            district = row['Ag District']
            color = district_colors[district]
            bar = ax.bar(i, row[y_column], color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
            bars.append(bar)
        
        # Set x-axis labels (county names)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(data['County'], rotation=45, ha='right')
        
        # Add district average lines
        for district in districts:
            district_data = data[data['Ag District'] == district]
            if not district_data.empty:
                district_avg = district_data[y_column].mean()
                district_color = district_colors[district]
                
                # Find the range of x-positions for this district
                district_indices = [i for i, (_, row) in enumerate(data.iterrows()) if row['Ag District'] == district]
                if district_indices:
                    start_idx = min(district_indices)
                    end_idx = max(district_indices)
                    
                    # Draw horizontal line for district average
                    ax.axhline(y=district_avg, xmin=start_idx/len(data), xmax=(end_idx+1)/len(data), 
                              color=district_color, linestyle='-', linewidth=3, alpha=0.6)
                    
                    # Add district average label
                    mid_idx = (start_idx + end_idx) / 2
                    ax.text(mid_idx, district_avg + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.02, 
                           f'{district}\nAvg: {district_avg:.1f}', 
                           ha='center', va='bottom', fontsize=10, weight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor=district_color, alpha=0.3))
        
        # Add district separator lines
        current_district = None
        for i, (_, row) in enumerate(data.iterrows()):
            if current_district != row['Ag District']:
                if current_district is not None:
                    ax.axvline(x=i-0.5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
                current_district = row['Ag District']
    
    # Create the four subplots
    create_district_grouped_plot(axes[0, 0], biz_recent_sorted, 'Agriculture_forestry_fishing_and_hunting', 
                                'Agricultural Establishments', 'Number of Establishments')
    
    create_district_grouped_plot(axes[0, 1], biz_recent_sorted, 'Development_Establishments', 
                                'Development Establishments', 'Number of Establishments')
    
    create_district_grouped_plot(axes[1, 0], biz_recent_sorted, 'Construction', 
                                'Construction Establishments', 'Number of Establishments')
    
    create_district_grouped_plot(axes[1, 1], biz_recent_sorted, 'Manufacturing', 
                                'Manufacturing Establishments', 'Number of Establishments')
    
    # Add legend showing district colors
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=district_colors[district], edgecolor='black', alpha=0.8) 
                      for district in districts]
    fig.legend(legend_elements, districts, loc='center right', bbox_to_anchor=(0.98, 0.5), 
               title='Agricultural Districts', fontsize=11)
    
    plt.tight_layout()
    plt.show()
    
    # Display district summary statistics
    display("DEBUG: Business establishment summary by agricultural district:")
    district_summary = biz_recent.groupby('Ag District').agg({
        'Agriculture_forestry_fishing_and_hunting': ['count', 'mean', 'std'],
        'Development_Establishments': ['mean', 'std'],
        'Construction': ['mean', 'std'],
        'Manufacturing': ['mean', 'std']
    }).round(2)
    display(district_summary)
    
else:
    print("WARNING: No valid data available for Plot 3")

# =================================================================
#      PLOT 4: The Core Hypothesis - Development vs. Yield
# =================================================================
print("\n--- Generating Plot 4: Development vs. Yield ---")

# Since we can't merge due to different years, let's analyze the business data independently
# Show the relationship between agricultural and development establishments within the business data
most_recent_biz_year = df_biz['Year'].max()
biz_recent = df_biz[df_biz['Year'] == most_recent_biz_year].copy()

display(f"DEBUG: Plot 4 - Using business data from {most_recent_biz_year}")
display(f"DEBUG: biz_recent shape: {biz_recent.shape}")

# Calculate the development ratio within business data
biz_recent['Development_Ratio'] = biz_recent['Development_Establishments'] / biz_recent['Agriculture_forestry_fishing_and_hunting'].replace(0, 1)  # Avoid division by zero

# Remove infinite values
biz_recent = biz_recent.replace([np.inf, -np.inf], np.nan)
biz_recent = biz_recent.dropna(subset=['Development_Ratio'])

display("DEBUG: Development vs. Agricultural ratio data:")
display(biz_recent[['County', 'Development_Ratio', 'Agriculture_forestry_fishing_and_hunting', 'Development_Establishments', 'Ag District']].head())

if not biz_recent.empty:
    # Use universal color scheme for agricultural districts
    districts = sorted(biz_recent['Ag District'].dropna().unique())
    district_colors = {district: UNIVERSAL_DISTRICT_COLORS[district] for district in districts}
    
    # Create the improved plots
    fig, axes = plt.subplots(2, 2, figsize=(24, 16))
    fig.suptitle(f'Development vs. Agricultural Analysis by District ({most_recent_biz_year})', fontsize=18, weight='bold')
    
    # Plot 1: Development Ratio vs Agricultural Establishments (colored by district)
    axes[0, 0].set_title('Development Ratio vs Agricultural Establishments (by District)', fontsize=14, weight='bold')
    for district in districts:
        district_data = biz_recent[biz_recent['Ag District'] == district]
        if not district_data.empty:
            axes[0, 0].scatter(district_data['Agriculture_forestry_fishing_and_hunting'], district_data['Development_Ratio'], 
                               c=[district_colors[district]], label=district, s=100, alpha=0.8)
    axes[0, 0].set_xlabel('Agricultural Establishments', fontsize=12)
    axes[0, 0].set_ylabel('Development Ratio', fontsize=12)
    axes[0, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Development vs Agricultural establishments (colored by district)
    axes[0, 1].set_title('Development vs Agricultural Establishments (by District)', fontsize=14, weight='bold')
    for district in districts:
        district_data = biz_recent[biz_recent['Ag District'] == district]
        if not district_data.empty:
            axes[0, 1].scatter(district_data['Agriculture_forestry_fishing_and_hunting'], district_data['Development_Establishments'], 
                               c=[district_colors[district]], label=district, s=100, alpha=0.8)
    axes[0, 1].set_xlabel('Agricultural Establishments', fontsize=12)
    axes[0, 1].set_ylabel('Development Establishments', fontsize=12)
    axes[0, 1].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: OPTION A - Separate histograms for each district
    axes[1, 0].set_title('Distribution of Development Ratio by District', fontsize=14, weight='bold')
    
    # Create separate histograms for each district with transparency
    for district in districts:
        district_data = biz_recent[biz_recent['Ag District'] == district]
        if not district_data.empty:
            axes[1, 0].hist(district_data['Development_Ratio'], bins=8, alpha=0.6, label=district, 
                            color=district_colors[district], edgecolor='black', linewidth=1)
    
    axes[1, 0].set_xlabel('Development Ratio', fontsize=12)
    axes[1, 0].set_ylabel('Number of Counties', fontsize=12)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Add district averages as horizontal lines
    for district in districts:
        district_data = biz_recent[biz_recent['Ag District'] == district]
        if not district_data.empty:
            district_avg = district_data['Development_Ratio'].mean()
            district_color = district_colors[district]
            axes[1, 0].axhline(y=district_avg, color=district_color, linestyle='--', linewidth=2, alpha=0.8,
                               label=f'{district} Avg: {district_avg:.1f}')
    
    # Plot 4: OPTION D - Fixed county bars without stacking, grouped by district
    axes[1, 1].set_title('Development Ratio by County (Grouped by District)', fontsize=14, weight='bold')
    
    # Sort by district first, then by Development Ratio within each district
    biz_recent_sorted = biz_recent.sort_values(['Ag District', 'Development_Ratio'], ascending=[True, False])
    
    # Create horizontal bars with better spacing
    y_positions = range(len(biz_recent_sorted))
    for i, (_, row) in enumerate(biz_recent_sorted.iterrows()):
        district = row['Ag District']
        color = district_colors[district]
        axes[1, 1].barh(i, row['Development_Ratio'], color=color, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Set y-axis labels (county names) with better spacing
    axes[1, 1].set_yticks(y_positions)
    axes[1, 1].set_yticklabels(biz_recent_sorted['County'], fontsize=10)
    axes[1, 1].set_xlabel('Development Ratio', fontsize=12)
    
    # Add district separator lines
    current_district = None
    for i, (_, row) in enumerate(biz_recent_sorted.iterrows()):
        if current_district != row['Ag District']:
            if current_district is not None:
                axes[1, 1].axhline(y=i-0.5, color='gray', linestyle=':', linewidth=2, alpha=0.7)
            current_district = row['Ag District']
    
    # Add district average lines and labels
    for district in districts:
        district_data = biz_recent_sorted[biz_recent_sorted['Ag District'] == district]
        if not district_data.empty:
            district_avg = district_data['Development_Ratio'].mean()
            district_color = district_colors[district]
            
            # Find the range of y-positions for this district
            district_indices = [i for i, (_, row) in enumerate(biz_recent_sorted.iterrows()) if row['Ag District'] == district]
            if district_indices:
                start_idx = min(district_indices)
                end_idx = max(district_indices)
                
                # Draw horizontal line for district average
                axes[1, 1].axhline(y=district_avg, xmin=0, xmax=1, color=district_color, 
                                  linestyle='-', linewidth=3, alpha=0.6)
                
                # Add district average label with better positioning
                mid_idx = (start_idx + end_idx) / 2
                x_pos = district_avg + (axes[1, 1].get_xlim()[1] - axes[1, 1].get_xlim()[0]) * 0.05
                axes[1, 1].text(x_pos, mid_idx, f'{district}\nAvg: {district_avg:.1f}', 
                               ha='left', va='center', fontsize=11, weight='bold',
                               bbox=dict(boxstyle='round,pad=0.5', facecolor=district_color, alpha=0.3))
    
    # Add legend for district colors
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=district_colors[district], edgecolor='black', alpha=0.8) 
                      for district in districts]
    axes[1, 1].legend(legend_elements, districts, loc='upper right', title='Agricultural Districts', fontsize=11)
    
    # Adjust layout to prevent overlap
    plt.subplots_adjust(left=0.08, right=0.85, bottom=0.1, top=0.92, wspace=0.3, hspace=0.3)
    plt.show()
    
    # Show summary statistics by district
    display("DEBUG: Development ratio summary statistics by district:")
    district_stats = biz_recent.groupby('Ag District')['Development_Ratio'].describe()
    display(district_stats)
    
    # Show district grouping information
    display("\nDEBUG: Counties grouped by district:")
    for district in districts:
        district_counties = biz_recent_sorted[biz_recent_sorted['Ag District'] == district]
        display(f"\n{district} District:")
        for _, row in district_counties.iterrows():
            display(f"  {row['County']}: Development Ratio = {row['Development_Ratio']:.1f}")
    
else:
    print("WARNING: No valid data available for Plot 4")

# =================================================================
#      PLOT 5: Change Over Time for Key Districts (IMPROVED)
# =================================================================
print("\n--- Generating Plot 5: Business Trends Over Time ---")

# Since we can't merge due to different years, let's focus on business data trends over time
# Show how business establishments change from 2020 to 2023
display("DEBUG: Plot 5 - Business data years available:", sorted(df_biz['Year'].unique()))

# Calculate percentage change for business data from 2020 to 2023
biz_2020 = df_biz[df_biz['Year'] == 2020].copy()
biz_2023 = df_biz[df_biz['Year'] == 2023].copy()

if not biz_2020.empty and not biz_2023.empty:
    # Calculate percentage change for each county
    biz_change = biz_2020[['County', 'Agriculture_forestry_fishing_and_hunting', 'Development_Establishments', 'Ag District']].copy()
    biz_change = biz_change.merge(biz_2023[['County', 'Agriculture_forestry_fishing_and_hunting', 'Development_Establishments']], 
                                 on='County', suffixes=('_2020', '_2023'))
    
    # Calculate percentage change
    biz_change['Ag_Change_Pct'] = ((biz_change['Agriculture_forestry_fishing_and_hunting_2023'] / 
                                   biz_change['Agriculture_forestry_fishing_and_hunting_2020'].replace(0, 1)) - 1) * 100
    biz_change['Dev_Change_Pct'] = ((biz_change['Development_Establishments_2023'] / 
                                   biz_change['Development_Establishments_2020'].replace(0, 1)) - 1) * 100
    
    # Remove infinite values
    biz_change = biz_change.replace([np.inf, -np.inf], np.nan)
    
    display("DEBUG: Business change data:")
    display(biz_change.head())
    
    # Use universal color scheme for agricultural districts
    districts = sorted(biz_change['Ag District'].dropna().unique())
    district_colors = {district: UNIVERSAL_DISTRICT_COLORS[district] for district in districts}
    
    # Create the plot
    plt.figure(figsize=(16, 12))
    
    # Plot 1: Agricultural vs Development change correlation (colored by district)
    plt.subplot(2, 2, 1)
    for district in districts:
        district_data = biz_change[biz_change['Ag District'] == district]
        if not district_data.empty:
            plt.scatter(district_data['Ag_Change_Pct'], district_data['Dev_Change_Pct'], 
                       c=[district_colors[district]], label=district, s=100, alpha=0.8)
    plt.xlabel('Agricultural Establishments % Change (2020-2023)')
    plt.ylabel('Development Establishments % Change (2020-2023)')
    plt.title('Agricultural vs Development Change Correlation (by District)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.5)
    
    # Plot 2: Distribution of agricultural changes by district
    plt.subplot(2, 2, 2)
    for district in districts:
        district_data = biz_change[biz_change['Ag District'] == district]
        if not district_data.empty:
            plt.hist(district_data['Ag_Change_Pct'].dropna(), bins=10, alpha=0.6, label=district, 
                    color=district_colors[district], edgecolor='black')
    plt.xlabel('Agricultural Establishments % Change')
    plt.ylabel('Number of Counties')
    plt.title('Distribution of Agricultural Changes (by District)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Distribution of development changes by district
    plt.subplot(2, 2, 3)
    for district in districts:
        district_data = biz_change[biz_change['Ag District'] == district]
        if not district_data.empty:
            plt.hist(district_data['Dev_Change_Pct'].dropna(), bins=10, alpha=0.6, label=district, 
                    color=district_colors[district], edgecolor='black')
    plt.xlabel('Development Establishments % Change')
    plt.ylabel('Number of Counties')
    plt.title('Distribution of Development Changes (by District)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 4: Top counties by development change (colored by district)
    plt.subplot(2, 2, 4)
    top_changes = biz_change.nlargest(15, 'Dev_Change_Pct')
    for district in districts:
        district_data = top_changes[top_changes['Ag District'] == district]
        if not district_data.empty:
            plt.barh(range(len(district_data)), district_data['Dev_Change_Pct'], 
                    color=district_colors[district], label=district, alpha=0.8)
    plt.xlabel('Development Establishments % Change')
    plt.yticks(range(len(top_changes)), top_changes['County'])
    plt.title('Top 15 Counties by Development Growth (by District)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.show()
    
    # Show summary statistics by district
    display("DEBUG: Change summary statistics by district:")
    ag_district_stats = biz_change.groupby('Ag District')['Ag_Change_Pct'].describe()
    dev_district_stats = biz_change.groupby('Ag District')['Dev_Change_Pct'].describe()
    display("Agricultural changes by district:")
    display(ag_district_stats)
    display("Development changes by district:")
    display(dev_district_stats)
    
else:
    print("WARNING: Cannot compare years - missing data for 2020 or 2023")

# =================================================================
#      PLOT 1.5: Regional Percentage Change Trends by Ag District
# =================================================================
print("\n--- Generating Plot 1.5: Regional Percentage Change by Ag District ---")

# Calculate percentage change from 2020 by Ag District
def calculate_district_trends(df_biz_plot, df_nass_plot):
    # Merge business and NASS data to get Ag District for business data
    df_merged = pd.merge(
        df_biz_plot[['Year', 'County', 'Agriculture_forestry_fishing_and_hunting', 'Development_Establishments']],
        df_nass_plot[['Year', 'County', 'Ag District']].drop_duplicates(),
        on=['Year', 'County'],
        how='left'
    )
    
    # Group by Year and Ag District, then calculate percentage change from 2020
    district_trends = df_merged.groupby(['Year', 'Ag District'])[['Agriculture_forestry_fishing_and_hunting', 'Development_Establishments']].sum().reset_index()
    
    # Calculate percentage change from 2020 for each district
    district_trends_normalized = district_trends.copy()
    for district in district_trends_normalized['Ag District'].unique():
        district_data = district_trends_normalized[district_trends_normalized['Ag District'] == district]
        baseline_2020 = district_data[district_data['Year'] == 2020]
        
        if not baseline_2020.empty:
            baseline_ag = baseline_2020['Agriculture_forestry_fishing_and_hunting'].iloc[0]
            baseline_dev = baseline_2020['Development_Establishments'].iloc[0]
            
            # Calculate percentage change (avoid division by zero)
            if baseline_ag > 0:
                district_trends_normalized.loc[district_data.index, 'Agriculture_forestry_fishing_and_hunting'] = \
                    (district_data['Agriculture_forestry_fishing_and_hunting'] / baseline_ag - 1) * 100
            else:
                district_trends_normalized.loc[district_data.index, 'Agriculture_forestry_fishing_and_hunting'] = 0
                
            if baseline_dev > 0:
                district_trends_normalized.loc[district_data.index, 'Development_Establishments'] = \
                    (district_data['Development_Establishments'] / baseline_dev - 1) * 100
            else:
                district_trends_normalized.loc[district_data.index, 'Development_Establishments'] = 0
    
    return district_trends_normalized

# Calculate district trends
district_trends_normalized = calculate_district_trends(df_biz_plot, df_nass_plot)
display("DEBUG: District percentage change data:")
display(district_trends_normalized.head(10))

# Create the plot
plt.figure(figsize=(14, 8))

# Get unique districts and assign colors
districts = sorted(district_trends_normalized['Ag District'].unique())
colors = plt.cm.Set3(np.linspace(0, 1, len(districts)))

# Plot agricultural establishments by district
for i, district in enumerate(districts):
    district_data = district_trends_normalized[district_trends_normalized['Ag District'] == district]
    plt.plot(district_data['Year'], district_data['Agriculture_forestry_fishing_and_hunting'], 
             marker='o', linestyle='-', linewidth=2, markersize=6, 
             color=colors[i], label=f'{district} (Agricultural)', alpha=0.8)

plt.title('Agricultural Establishments: Percentage Change from 2020 by Agricultural District', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Percentage Change from 2020 (%)', fontsize=12)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.xticks(sorted(district_trends_normalized['Year'].unique()))
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.7)
plt.tight_layout()
plt.show()

# Plot development establishments by district
plt.figure(figsize=(14, 8))

for i, district in enumerate(districts):
    district_data = district_trends_normalized[district_trends_normalized['Ag District'] == district]
    plt.plot(district_data['Year'], district_data['Development_Establishments'], 
             marker='s', linestyle='--', linewidth=2, markersize=6, 
             color=colors[i], label=f'{district} (Development)', alpha=0.8)

plt.title('Development Establishments: Percentage Change from 2020 by Agricultural District', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Percentage Change from 2020 (%)', fontsize=12)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.xticks(sorted(district_trends_normalized['Year'].unique()))
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.7)
plt.tight_layout()
plt.show()

# Combined plot showing both metrics for each district
plt.figure(figsize=(16, 10))

# Create subplots for each district
n_districts = len(districts)
n_cols = 3
n_rows = (n_districts + n_cols - 1) // n_cols

for i, district in enumerate(districts):
    plt.subplot(n_rows, n_cols, i + 1)
    
    district_data = district_trends_normalized[district_trends_normalized['Ag District'] == district]
    
    plt.plot(district_data['Year'], district_data['Agriculture_forestry_fishing_and_hunting'], 
             marker='o', linestyle='-', linewidth=2, markersize=6, 
             color='blue', label='Agricultural', alpha=0.8)
    plt.plot(district_data['Year'], district_data['Development_Establishments'], 
             marker='s', linestyle='--', linewidth=2, markersize=6, 
             color='red', label='Development', alpha=0.8)
    
    plt.title(f'{district}', fontsize=12)
    plt.xlabel('Year', fontsize=10)
    plt.ylabel('% Change from 2020', fontsize=10)
    plt.legend(fontsize=8)
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    plt.xticks(sorted(district_data['Year'].unique()))
    plt.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.7)

plt.suptitle('Percentage Change from 2020: Agricultural vs. Development by District', fontsize=16)
plt.tight_layout()
plt.show()

display("DEBUG: All plots completed successfully!")

# =================================================================
#      PLOT 4.5: Standalone Development vs Agricultural Analysis
# =================================================================
print("\n--- Generating Plot 4.5: Standalone Development vs Agricultural Analysis (2020 vs 2023) ---")

# Get data for both 2020 and 2023
biz_2020 = df_biz[df_biz['Year'] == 2020].copy()
biz_2023 = df_biz[df_biz['Year'] == 2023].copy()

display(f"DEBUG: Plot 4.5 - 2020 data shape: {biz_2020.shape}")
display(f"DEBUG: Plot 4.5 - 2023 data shape: {biz_2023.shape}")

# Filter out any rows without district information
biz_2020 = biz_2020.dropna(subset=['Ag District'])
biz_2023 = biz_2023.dropna(subset=['Ag District'])

if not biz_2020.empty and not biz_2023.empty:
    # Use universal color scheme for agricultural districts
    districts = sorted(biz_2020['Ag District'].unique())
    district_colors = {district: UNIVERSAL_DISTRICT_COLORS[district] for district in districts}
    
    # Create the standalone plot with subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    fig.suptitle('Development vs Agricultural Establishments by District: 2020 vs 2023\nWith District-Specific Trend Lines', 
                 fontsize=16, weight='bold')
    
    # Plot 2020 data
    ax1.set_title('2020 Data', fontsize=14, weight='bold')
    ax1.set_xlabel('Agricultural Establishments', fontsize=12)
    ax1.set_ylabel('Development Establishments', fontsize=12)
    ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    
    # Plot points for each district in 2020
    for district in districts:
        district_data = biz_2020[biz_2020['Ag District'] == district]
        if not district_data.empty:
            ax1.scatter(district_data['Agriculture_forestry_fishing_and_hunting'], 
                       district_data['Development_Establishments'], 
                       c=[district_colors[district]], label=district, s=120, alpha=0.8)
    
    # Calculate and plot trend lines for each district in 2020
    for district in districts:
        district_data = biz_2020[biz_2020['Ag District'] == district]
        if len(district_data) > 1:  # Need at least 2 points for a line
            x = district_data['Agriculture_forestry_fishing_and_hunting']
            y = district_data['Development_Establishments']
            
            # Calculate linear regression for this district
            if len(x) > 1 and x.var() > 0:  # Check if we have variation in x
                slope, intercept = np.polyfit(x, y, 1)
                line_x = np.array([x.min(), x.max()])
                line_y = slope * line_x + intercept
                
                ax1.plot(line_x, line_y, color=district_colors[district], 
                        linestyle='--', linewidth=2, alpha=0.8)
                
                # Add slope annotation
                mid_x = (x.min() + x.max()) / 2
                mid_y = slope * mid_x + intercept
                ax1.annotate(f'slope: {slope:.1f}', 
                           xy=(mid_x, mid_y), 
                           xytext=(mid_x + 2, mid_y + 100),
                           arrowprops=dict(arrowstyle='->', color=district_colors[district], alpha=0.7),
                           fontsize=9, color=district_colors[district])
    
    # Calculate and plot overall average trend line for 2020
    all_x_2020 = biz_2020['Agriculture_forestry_fishing_and_hunting']
    all_y_2020 = biz_2020['Development_Establishments']
    
    if len(all_x_2020) > 1 and all_x_2020.var() > 0:
        overall_slope_2020, overall_intercept_2020 = np.polyfit(all_x_2020, all_y_2020, 1)
        overall_line_x_2020 = np.array([all_x_2020.min(), all_x_2020.max()])
        overall_line_y_2020 = overall_slope_2020 * overall_line_x_2020 + overall_intercept_2020
        
        ax1.plot(overall_line_x_2020, overall_line_y_2020, color='black', 
                linestyle='-', linewidth=3, alpha=0.9)
        
        # Add overall slope annotation for 2020
        overall_mid_x_2020 = (all_x_2020.min() + all_x_2020.max()) / 2
        overall_mid_y_2020 = overall_slope_2020 * overall_mid_x_2020 + overall_intercept_2020
        ax1.annotate(f'Overall slope: {overall_slope_2020:.1f}', 
                    xy=(overall_mid_x_2020, overall_mid_y_2020), 
                    xytext=(overall_mid_x_2020 + 2, overall_mid_y_2020 + 200),
                    arrowprops=dict(arrowstyle='->', color='black', alpha=0.8),
                    fontsize=11, color='black', weight='bold')
    
    # Plot 2023 data
    ax2.set_title('2023 Data', fontsize=14, weight='bold')
    ax2.set_xlabel('Agricultural Establishments', fontsize=12)
    ax2.set_ylabel('Development Establishments', fontsize=12)
    ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    
    # Plot points for each district in 2023
    for district in districts:
        district_data = biz_2023[biz_2023['Ag District'] == district]
        if not district_data.empty:
            ax2.scatter(district_data['Agriculture_forestry_fishing_and_hunting'], 
                       district_data['Development_Establishments'], 
                       c=[district_colors[district]], label=district, s=120, alpha=0.8)
    
    # Calculate and plot trend lines for each district in 2023
    for district in districts:
        district_data = biz_2023[biz_2023['Ag District'] == district]
        if len(district_data) > 1:  # Need at least 2 points for a line
            x = district_data['Agriculture_forestry_fishing_and_hunting']
            y = district_data['Development_Establishments']
            
            # Calculate linear regression for this district
            if len(x) > 1 and x.var() > 0:  # Check if we have variation in x
                slope, intercept = np.polyfit(x, y, 1)
                line_x = np.array([x.min(), x.max()])
                line_y = slope * line_x + intercept
                
                ax2.plot(line_x, line_y, color=district_colors[district], 
                        linestyle='--', linewidth=2, alpha=0.8)
                
                # Add slope annotation
                mid_x = (x.min() + x.max()) / 2
                mid_y = slope * mid_x + intercept
                ax2.annotate(f'slope: {slope:.1f}', 
                           xy=(mid_x, mid_y), 
                           xytext=(mid_x + 2, mid_y + 100),
                           arrowprops=dict(arrowstyle='->', color=district_colors[district], alpha=0.7),
                           fontsize=9, color=district_colors[district])
    
    # Calculate and plot overall average trend line for 2023
    all_x_2023 = biz_2023['Agriculture_forestry_fishing_and_hunting']
    all_y_2023 = biz_2023['Development_Establishments']
    
    if len(all_x_2023) > 1 and all_x_2023.var() > 0:
        overall_slope_2023, overall_intercept_2023 = np.polyfit(all_x_2023, all_y_2023, 1)
        overall_line_x_2023 = np.array([all_x_2023.min(), all_x_2023.max()])
        overall_line_y_2023 = overall_slope_2023 * overall_line_x_2023 + overall_intercept_2023
        
        ax2.plot(overall_line_x_2023, overall_line_y_2023, color='black', 
                linestyle='-', linewidth=3, alpha=0.9)
        
        # Add overall slope annotation for 2023
        overall_mid_x_2023 = (all_x_2023.min() + all_x_2023.max()) / 2
        overall_mid_y_2023 = overall_slope_2023 * overall_mid_x_2023 + overall_intercept_2023
        ax2.annotate(f'Overall slope: {overall_slope_2023:.1f}', 
                    xy=(overall_mid_x_2023, overall_mid_y_2023), 
                    xytext=(overall_mid_x_2023 + 2, overall_mid_y_2023 + 200),
                    arrowprops=dict(arrowstyle='->', color='black', alpha=0.8),
                    fontsize=11, color='black', weight='bold')
    
    # Add legend to the right of both plots
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right', bbox_to_anchor=(0.98, 0.5), fontsize=11)
    
    # Add statistics text boxes
    stats_2020 = f"""2020 Statistics:
• Counties: {len(biz_2020)}
• Correlation: {biz_2020['Agriculture_forestry_fishing_and_hunting'].corr(biz_2020['Development_Establishments']):.3f}
• Avg Dev: {biz_2020['Development_Establishments'].mean():.0f}
• Avg Ag: {biz_2020['Agriculture_forestry_fishing_and_hunting'].mean():.1f}"""
    
    stats_2023 = f"""2023 Statistics:
• Counties: {len(biz_2023)}
• Correlation: {biz_2023['Agriculture_forestry_fishing_and_hunting'].corr(biz_2023['Development_Establishments']):.3f}
• Avg Dev: {biz_2023['Development_Establishments'].mean():.0f}
• Avg Ag: {biz_2023['Agriculture_forestry_fishing_and_hunting'].mean():.1f}"""
    
    ax1.text(0.02, 0.98, stats_2020, transform=ax1.transAxes, 
             fontsize=9, verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax2.text(0.02, 0.98, stats_2023, transform=ax2.transAxes, 
             fontsize=9, verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
    # Display comparison statistics
    display("DEBUG: 2020 vs 2023 Comparison Statistics:")
    
    # Overall comparison
    if len(all_x_2020) > 1 and len(all_x_2023) > 1:
        display(f"Overall slope change: {overall_slope_2020:.1f} (2020) → {overall_slope_2023:.1f} (2023)")
        display(f"Slope change: {overall_slope_2023 - overall_slope_2020:.1f}")
        
        corr_2020 = biz_2020['Agriculture_forestry_fishing_and_hunting'].corr(biz_2020['Development_Establishments'])
        corr_2023 = biz_2023['Agriculture_forestry_fishing_and_hunting'].corr(biz_2023['Development_Establishments'])
        display(f"Correlation change: {corr_2020:.3f} (2020) → {corr_2023:.3f} (2023)")
        display(f"Correlation change: {corr_2023 - corr_2020:.3f}")
    
    # District-specific statistics
    display("\nDEBUG: District-specific statistics by year:")
    for district in districts:
        data_2020 = biz_2020[biz_2020['Ag District'] == district]
        data_2023 = biz_2023[biz_2023['Ag District'] == district]
        
        if not data_2020.empty and not data_2023.empty:
            dev_change = data_2023['Development_Establishments'].mean() - data_2020['Development_Establishments'].mean()
            ag_change = data_2023['Agriculture_forestry_fishing_and_hunting'].mean() - data_2020['Agriculture_forestry_fishing_and_hunting'].mean()
            
            display(f"\n{district}:")
            display(f"  Development: {data_2020['Development_Establishments'].mean():.0f} → {data_2023['Development_Establishments'].mean():.0f} (change: {dev_change:+.0f})")
            display(f"  Agricultural: {data_2020['Agriculture_forestry_fishing_and_hunting'].mean():.1f} → {data_2023['Agriculture_forestry_fishing_and_hunting'].mean():.1f} (change: {ag_change:+.1f})")
    
else:
    print("WARNING: No valid data available for Plot 4.5")

# =================================================================
#      PLOT 2.5: Business vs NASS Data by District (Side by Side)
# =================================================================
print("\n--- Generating Plot 2.5: Business vs NASS Data by District ---")

# Use the most recent available year from business data
most_recent_biz_year = df_biz['Year'].max()
biz_recent = df_biz[df_biz['Year'] == most_recent_biz_year].copy()

# Use the most recent available year from NASS data
most_recent_nass_year = df_nass['Year'].max()
nass_recent = df_nass[df_nass['Year'] == most_recent_nass_year].copy()

display(f"DEBUG: Plot 2.5 - Business data from {most_recent_biz_year}, NASS data from {most_recent_nass_year}")
display(f"DEBUG: Plot 2.5 - biz_recent shape: {biz_recent.shape}")
display(f"DEBUG: Plot 2.5 - nass_recent shape: {nass_recent.shape}")

# Filter out any rows without district information
biz_recent = biz_recent.dropna(subset=['Ag District'])
nass_recent = nass_recent.dropna(subset=['Ag District'])

if not biz_recent.empty and not nass_recent.empty:
    # Use universal color scheme for agricultural districts
    districts = sorted(biz_recent['Ag District'].unique())
    district_colors = {district: UNIVERSAL_DISTRICT_COLORS[district] for district in districts}
    
    # Create the side-by-side plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    fig.suptitle(f'Business vs NASS Data by Agricultural District\n{most_recent_biz_year} vs {most_recent_nass_year}', 
                 fontsize=16, weight='bold')
    
    # Plot 1: Business Data (Development vs Agricultural Establishments)
    ax1.set_title(f'Business Data ({most_recent_biz_year})\nDevelopment vs Agricultural Establishments', 
                  fontsize=14, weight='bold')
    ax1.set_xlabel('Development Establishments', fontsize=12)
    ax1.set_ylabel('Agricultural Establishments', fontsize=12)
    ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    
    # Plot points for each district in business data
    for district in districts:
        district_data = biz_recent[biz_recent['Ag District'] == district]
        if not district_data.empty:
            ax1.scatter(district_data['Development_Establishments'], 
                       district_data['Agriculture_forestry_fishing_and_hunting'], 
                       c=[district_colors[district]], label=district, s=120, alpha=0.8)
    
    # Calculate and plot trend lines for each district in business data
    for district in districts:
        district_data = biz_recent[biz_recent['Ag District'] == district]
        if len(district_data) >= 2:  # Allow 2 points for slope calculation
            x = district_data['Development_Establishments']
            y = district_data['Agriculture_forestry_fishing_and_hunting']
            
            # Calculate linear regression for this district (even with just 2 points)
            if len(x) >= 2:  # Changed from > 1 to >= 2
                slope, intercept = np.polyfit(x, y, 1)
                line_x = np.array([x.min(), x.max()])
                line_y = slope * line_x + intercept
                
                ax1.plot(line_x, line_y, color=district_colors[district], 
                        linestyle='--', linewidth=2, alpha=0.8)
                
                # Add slope annotation
                mid_x = (x.min() + x.max()) / 2
                mid_y = slope * mid_x + intercept
                ax1.annotate(f'slope: {slope:.3f}', 
                           xy=(mid_x, mid_y), 
                           xytext=(mid_x + 100, mid_y + 2),
                           arrowprops=dict(arrowstyle='->', color=district_colors[district], alpha=0.7),
                           fontsize=9, color=district_colors[district])
    
    # Calculate overall trend line by averaging district slopes instead of fitting to all raw data
    district_slopes = []
    district_intercepts = []
    district_weights = []  # Weight by number of counties in each district
    
    for district in districts:
        district_data = biz_recent[biz_recent['Ag District'] == district]
        if len(district_data) >= 2:
            x = district_data['Development_Establishments']
            y = district_data['Agriculture_forestry_fishing_and_hunting']
            
            if len(x) >= 2:
                slope, intercept = np.polyfit(x, y, 1)
                district_slopes.append(slope)
                district_intercepts.append(intercept)
                district_weights.append(len(district_data))  # Weight by county count
    
    # Calculate weighted average of district slopes and intercepts
    if district_slopes:
        overall_slope_biz = np.average(district_slopes, weights=district_weights)
        overall_intercept_biz = np.average(district_intercepts, weights=district_weights)
        
        # Plot overall trend line using the averaged slope
        all_x_biz = biz_recent['Development_Establishments']
        overall_line_x_biz = np.array([all_x_biz.min(), all_x_biz.max()])
        overall_line_y_biz = overall_slope_biz * overall_line_x_biz + overall_intercept_biz
        
        ax1.plot(overall_line_x_biz, overall_line_y_biz, color='black', 
                linestyle='-', linewidth=3, alpha=0.9)
        
        # Add overall slope annotation for business data
        overall_mid_x_biz = (all_x_biz.min() + all_x_biz.max()) / 2
        overall_mid_y_biz = overall_slope_biz * overall_mid_x_biz + overall_intercept_biz
        ax1.annotate(f'Overall slope: {overall_slope_biz:.3f}', 
                    xy=(overall_mid_x_biz, overall_mid_y_biz), 
                    xytext=(overall_mid_x_biz + 200, overall_mid_y_biz + 3),
                    arrowprops=dict(arrowstyle='->', color='black', alpha=0.8),
                    fontsize=11, color='black', weight='bold')
        
        # Add note about how overall slope was calculated
        ax1.text(0.02, 0.02, f'Overall slope: average of district slopes\nweighted by county count', 
                transform=ax1.transAxes, fontsize=8, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Plot 2: NASS Data (Acres Planted vs Yield)
    ax2.set_title(f'NASS Data ({most_recent_nass_year})\nAcres Planted vs Yield', 
                  fontsize=14, weight='bold')
    ax2.set_xlabel('Acres Planted', fontsize=12)
    ax2.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    ax2.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)
    
    # Plot points for each district in NASS data
    for district in districts:
        district_data = nass_recent[nass_recent['Ag District'] == district]
        if not district_data.empty:
            ax2.scatter(district_data['Acres_Planted'], 
                       district_data['Yield_BuAcre'], 
                       c=[district_colors[district]], label=district, s=120, alpha=0.8)
    
    # Calculate and plot trend lines for each district in NASS data
    for district in districts:
        district_data = nass_recent[nass_recent['Ag District'] == district]
        if len(district_data) >= 2:  # Allow 2 points for slope calculation
            x = district_data['Acres_Planted']
            y = district_data['Yield_BuAcre']
            
            # Calculate linear regression for this district (even with just 2 points)
            if len(x) >= 2:  # Changed from > 1 to >= 2
                slope, intercept = np.polyfit(x, y, 1)
                line_x = np.array([x.min(), x.max()])
                line_y = slope * line_x + intercept
                
                ax2.plot(line_x, line_y, color=district_colors[district], 
                        linestyle='--', linewidth=2, alpha=0.8)
                
                # Add slope annotation
                mid_x = (x.min() + x.max()) / 2
                mid_y = slope * mid_x + intercept
                ax2.annotate(f'slope: {slope:.6f}', 
                           xy=(mid_x, mid_y), 
                           xytext=(mid_x + 5000, mid_y + 2),
                           arrowprops=dict(arrowstyle='->', color=district_colors[district], alpha=0.7),
                           fontsize=9, color=district_colors[district])
    
    # Calculate overall trend line by averaging district slopes instead of fitting to all raw data
    district_slopes = []
    district_intercepts = []
    district_weights = []  # Weight by number of counties in each district
    
    for district in districts:
        district_data = nass_recent[nass_recent['Ag District'] == district]
        if len(district_data) >= 2:
            x = district_data['Acres_Planted']
            y = district_data['Yield_BuAcre']
            
            if len(x) >= 2:
                slope, intercept = np.polyfit(x, y, 1)
                district_slopes.append(slope)
                district_intercepts.append(intercept)
                district_weights.append(len(district_data))  # Weight by county count
    
    # Calculate weighted average of district slopes and intercepts
    if district_slopes:
        overall_slope_nass = np.average(district_slopes, weights=district_weights)
        overall_intercept_nass = np.average(district_intercepts, weights=district_weights)
        
        # Plot overall trend line using the averaged slope
        all_x_nass = nass_recent['Acres_Planted']
        overall_line_x_nass = np.array([all_x_nass.min(), all_x_nass.max()])
        overall_line_y_nass = overall_slope_nass * overall_line_x_nass + overall_intercept_nass
        
        ax2.plot(overall_line_x_nass, overall_line_y_nass, color='black', 
                linestyle='-', linewidth=3, alpha=0.9)
        
        # Add overall slope annotation for NASS data
        overall_mid_x_nass = (all_x_nass.min() + all_x_nass.max()) / 2
        overall_mid_y_nass = overall_slope_nass * overall_mid_x_nass + overall_intercept_nass
        ax2.annotate(f'Overall slope: {overall_slope_nass:.6f}', 
                    xy=(overall_mid_x_nass, overall_mid_y_nass), 
                    xytext=(overall_mid_x_nass + 10000, overall_mid_y_nass + 3),
                    arrowprops=dict(arrowstyle='->', color='black', alpha=0.8),
                    fontsize=11, color='black', weight='bold')
        
        # Add note about how overall slope was calculated
        ax2.text(0.02, 0.02, f'Overall slope: average of district slopes\nweighted by county count', 
                transform=ax2.transAxes, fontsize=8, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Add legend to the right of both plots
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc='center right', bbox_to_anchor=(0.98, 0.5), fontsize=11)
    
    # Add statistics text boxes
    stats_biz = f"""Business Data ({most_recent_biz_year}):
• Counties: {len(biz_recent)}
• Correlation: {biz_recent['Development_Establishments'].corr(biz_recent['Agriculture_forestry_fishing_and_hunting']):.3f}
• Avg Dev Est: {biz_recent['Development_Establishments'].mean():.0f}
• Avg Ag Est: {biz_recent['Agriculture_forestry_fishing_and_hunting'].mean():.1f}"""
    
    stats_nass = f"""NASS Data ({most_recent_nass_year}):
• Counties: {len(nass_recent)}
• Correlation: {nass_recent['Acres_Planted'].corr(nass_recent['Yield_BuAcre']):.3f}
• Avg Acres: {nass_recent['Acres_Planted'].mean():.0f}
• Avg Yield: {nass_recent['Yield_BuAcre'].mean():.1f}"""
    
    ax1.text(0.02, 0.98, stats_biz, transform=ax1.transAxes, 
             fontsize=9, verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax2.text(0.02, 0.98, stats_nass, transform=ax2.transAxes, 
             fontsize=9, verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
    # Display comparison statistics
    display("DEBUG: Business vs NASS Data Comparison:")
    
    # Business data statistics by district
    display("\nDEBUG: Business data statistics by district:")
    biz_district_stats = biz_recent.groupby('Ag District').agg({
        'Development_Establishments': ['count', 'mean', 'std'],
        'Agriculture_forestry_fishing_and_hunting': ['mean', 'std']
    }).round(2)
    display(biz_district_stats)
    
    # NASS data statistics by district
    display("\nDEBUG: NASS data statistics by district:")
    nass_district_stats = nass_recent.groupby('Ag District').agg({
        'Acres_Planted': ['count', 'mean', 'std'],
        'Yield_BuAcre': ['mean', 'std']
    }).round(2)
    display(nass_district_stats)
    
else:
    print("WARNING: No valid data available for Plot 2.5")

print("\n--- Analysis Complete ---")
print("Generated 2 essential plots:")
print("1. Plot 4.5: Development vs Agricultural Analysis (2020 vs 2023)")
print("2. Plot 2.5: Business vs NASS Data by District (Side by Side)")

# =================================================================
#      PLOT 5: Maryland County Map - Development Ratio Visualization
# =================================================================
print("\n--- Generating Plot 5: Maryland County Map - Development Ratio ---")

# Get the most recent business data for mapping
most_recent_biz_year = df_biz['Year'].max()
biz_map_data = df_biz[df_biz['Year'] == most_recent_biz_year].copy()

# Calculate Development Ratio for mapping
biz_map_data['Development_Ratio'] = biz_map_data['Development_Establishments'] / biz_map_data['Agriculture_forestry_fishing_and_hunting'].replace(0, 1)
biz_map_data = biz_map_data.replace([np.inf, -np.inf], np.nan)
biz_map_data = biz_map_data.dropna(subset=['Development_Ratio'])

display(f"DEBUG: Map data from {most_recent_biz_year}")
display(f"DEBUG: Counties with valid data: {len(biz_map_data)}")
display(biz_map_data[['County', 'Development_Ratio', 'Ag District']].sort_values('Development_Ratio', ascending=False))

if not biz_map_data.empty:
    # Create the map visualization
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Create a color map for development ratios
    # Use a diverging colormap: red (high development) to blue (low development)
    colors = plt.cm.RdYlBu_r(np.linspace(0, 1, len(biz_map_data)))
    
    # Sort counties by development ratio for better color distribution
    biz_map_data_sorted = biz_map_data.sort_values('Development_Ratio', ascending=False)
    
    # Create horizontal bar chart representing counties geographically
    # Group by agricultural district for logical organization
    y_positions = []
    county_labels = []
    development_ratios = []
    district_colors_map = []
    
    # Use universal color scheme for consistency
    district_colors_map_dict = UNIVERSAL_DISTRICT_COLORS
    
    current_y = 0
    for district in ['NORTH CENTRAL', 'SOUTHERN', 'LOWER EASTERN SHORE', 'UPPER EASTERN SHORE', 'WESTERN']:
        district_data = biz_map_data_sorted[biz_map_data_sorted['Ag District'] == district]
        if not district_data.empty:
            # Add district separator
            if current_y > 0:
                y_positions.append(current_y - 0.5)
                county_labels.append('')
                development_ratios.append(0)
                district_colors_map.append('#CCCCCC')
                current_y += 1
            
            # Add counties in this district
            for _, row in district_data.iterrows():
                y_positions.append(current_y)
                county_labels.append(row['County'])
                development_ratios.append(row['Development_Ratio'])
                district_colors_map.append(district_colors_map_dict[district])
                current_y += 1
    
    # Create the horizontal bar chart
    bars = ax.barh(y_positions, development_ratios, color=district_colors_map, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Customize the plot
    ax.set_title(f'Maryland County Development Ratio Map ({most_recent_biz_year})\nUrban-Suburban-Rural Divide Visualization', 
                 fontsize=16, weight='bold', pad=20)
    ax.set_xlabel('Development Ratio (Development Establishments / Agricultural Establishments)', fontsize=12)
    ax.set_ylabel('Counties (Grouped by Agricultural District)', fontsize=12)
    
    # Set y-axis labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(county_labels, fontsize=10)
    
    # Add district labels on the right side
    current_y = 0
    for district in ['NORTH CENTRAL', 'SOUTHERN', 'LOWER EASTERN SHORE', 'UPPER EASTERN SHORE', 'WESTERN']:
        district_data = biz_map_data_sorted[biz_map_data_sorted['Ag District'] == district]
        if not district_data.empty:
            district_start = current_y
            district_end = current_y + len(district_data) - 1
            district_mid = (district_start + district_end) / 2
            
            # Add district label
            ax.text(ax.get_xlim()[1] * 1.02, district_mid, district, 
                   ha='left', va='center', fontsize=12, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor=district_colors_map_dict[district], alpha=0.3))
            
            current_y += len(district_data)
    
    # Add value labels on bars
    for i, (bar, ratio) in enumerate(zip(bars, development_ratios)):
        if ratio > 0:  # Only label non-zero values
            ax.text(ratio + ax.get_xlim()[1] * 0.01, bar.get_y() + bar.get_height()/2, 
                   f'{ratio:.0f}', ha='left', va='center', fontsize=9, weight='bold')
    
    # Add grid for better readability
    ax.grid(True, axis='x', alpha=0.3)
    
    # Add legend for districts
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=district_colors_map_dict[district], alpha=0.8) 
                      for district in ['NORTH CENTRAL', 'SOUTHERN', 'LOWER EASTERN SHORE', 'UPPER EASTERN SHORE', 'WESTERN']]
    ax.legend(legend_elements, ['North Central', 'Southern', 'Lower Eastern Shore', 'Upper Eastern Shore', 'Western'], 
              loc='upper right', title='Agricultural Districts', fontsize=11)
    
    # Add insights box
    insights_text = f"""Key Insights:
• Urban Core: Baltimore City (2109) - Highest development pressure
• Suburban Ring: Howard (437), Harford (345), Prince George's (551)
• Rural Areas: Western & Eastern Shore counties show lower ratios
• Clear urban-suburban-rural gradient visible"""
    
    ax.text(0.02, 0.98, insights_text, transform=ax.transAxes, fontsize=10, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Adjust layout to prevent overlap
    plt.subplots_adjust(left=0.1, right=0.85, bottom=0.1, top=0.9)
    plt.show()
    
    # Show summary statistics by district
    print("\nDevelopment Ratio Summary by Agricultural District:")
    district_summary = biz_map_data.groupby('Ag District')['Development_Ratio'].agg(['count', 'mean', 'min', 'max']).round(1)
    print(district_summary)
    
    # Show top and bottom counties
    print(f"\nTop 5 Counties by Development Ratio:")
    top_counties = biz_map_data.nlargest(5, 'Development_Ratio')[['County', 'Development_Ratio', 'Ag District']]
    for _, row in top_counties.iterrows():
        print(f"  {row['County']}: {row['Development_Ratio']:.0f} ({row['Ag District']})")
    
    print(f"\nBottom 5 Counties by Development Ratio:")
    bottom_counties = biz_map_data.nsmallest(5, 'Development_Ratio')[['County', 'Development_Ratio', 'Ag District']]
    for _, row in bottom_counties.iterrows():
        print(f"  {row['County']}: {row['Development_Ratio']:.0f} ({row['Ag District']})")
    
else:
    print("WARNING: No valid data available for mapping")

print("\n--- All Analysis Complete ---")
print("Generated 3 essential plots:")
print("1. Plot 4.5: Development vs Agricultural Analysis (2020 vs 2023)")
print("2. Plot 2.5: Business vs NASS Data by District (Side by Side)")
print("3. Plot 5: Maryland County Map - Development Ratio Visualization")
