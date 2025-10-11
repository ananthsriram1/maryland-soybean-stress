import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from IPython.display import display
from statsmodels.tsa.stattools import ccf
from statsmodels.tsa.stattools import grangercausalitytests




# --- 1. Load all your environmental datasets ---
precip_df = pd.read_csv('data/maryland_precipitation_combined_wide.csv', index_col='County')
pdsi_df = pd.read_csv('data/maryland_pdsi_combined_wide.csv', index_col='County')
phdi_df = pd.read_csv('data/maryland_phdi_combined_wide.csv', index_col='County')
pmdi_df = pd.read_csv('data/maryland_pmdi_combined_wide.csv', index_col='County')


# --- 2. Convert each dataset from "wide" to "long" format ---
# The melt function "un-pivots" the data
precip_long = precip_df.melt(ignore_index=False, var_name='date', value_name='Precip').reset_index()
pdsi_long = pdsi_df.melt(ignore_index=False, var_name='date', value_name='PDSI').reset_index()
phdi_long = phdi_df.melt(ignore_index=False, var_name='date', value_name='PHDI').reset_index()
pmdi_long = pmdi_df.melt(ignore_index=False, var_name='date', value_name='PMDI').reset_index()

# Clean up the date column in each
precip_long['date'] = precip_long['date'].str.replace('Precip_', '')
pdsi_long['date'] = pdsi_long['date'].str.replace('PDSI_', '')
phdi_long['date'] = phdi_long['date'].str.replace('PHDI_', '')
pmdi_long['date'] = pmdi_long['date'].str.replace('PMDI_', '')

# --- 3. Merge into a single combined DataFrame ---
merged_df = pd.merge(precip_long, pdsi_long, on=['County', 'date'])
merged_df = pd.merge(merged_df, phdi_long, on=['County', 'date'])
merged_df = pd.merge(merged_df, pmdi_long, on=['County', 'date'])

print("Combined environmental data preview:")
display(merged_df.head())

# --- 4. Calculate and Plot the Correlation Matrix ---
# Select only the numerical columns for correlation
correlation_matrix = merged_df[['Precip', 'PDSI', 'PHDI', 'PMDI']].corr()

print("\nCorrelation Matrix:")
display(correlation_matrix)

# Create a heatmap for better visualization
plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
plt.title('Correlation Matrix of Environmental Variables', fontsize=16)
plt.show()

# --- 1. Calculate the statewide average for each variable ---
statewide_avg = merged_df.groupby('date')[['Precip', 'PDSI', 'PHDI', 'PMDI']].mean().sort_index()

# --- 2. Normalize the data ---
# This scales each variable so they have a mean of 0 and standard deviation of 1.
# This allows us to compare their relative fluctuations on the same scale.
normalized_df = (statewide_avg - statewide_avg.mean()) / statewide_avg.std()
normalized_df.index = pd.to_datetime(normalized_df.index)

# --- 3. Plot the normalized time-series ---
plt.figure(figsize=(16, 8))
plt.plot(normalized_df.index, normalized_df['Precip'], label='Precipitation', color='blue')
plt.plot(normalized_df.index, normalized_df['PDSI'], label='PDSI', color='red', linestyle='--')
plt.plot(normalized_df.index, normalized_df['PHDI'], label='PHDI', color='orange', linestyle=':')
plt.plot(normalized_df.index, normalized_df['PMDI'], label='PMDI', color='green', linestyle='-.')

plt.title('Normalized Environmental Variables for Maryland (Statewide Average)', fontsize=18)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Normalized Value (Standard Deviations from Mean)', fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.axhline(0, color='black', linewidth=0.8) # Add a line at zero for reference
plt.show()

print("## Descriptive Statistics of Environmental Variables ##")
display(statewide_avg.describe())

ccf_precip_pdsi = ccf(normalized_df['Precip'], normalized_df['PDSI'], adjusted=False)
ccf_precip_phdi = ccf(normalized_df['Precip'], normalized_df['PHDI'], adjusted=False)
ccf_precip_pmdi = ccf(normalized_df['Precip'], normalized_df['PMDI'], adjusted=False)




# --- Create the Cross-Correlation Plot ---
plt.figure(figsize=(12, 6))
plt.stem(range(len(ccf_precip_pdsi))[:13], ccf_precip_pdsi[:13], use_line_collection=True)
plt.title('Cross-Correlation: Precipitation vs. PDSI', fontsize=16)
plt.xlabel('Lag (Months)', fontsize=12)
plt.ylabel('Correlation Coefficient', fontsize=12)
plt.axhline(0, color='black', linewidth=0.8)
plt.grid(True, linestyle='--', linewidth=0.5)
plt.show()

# --- Create the Cross-Correlation Plot ---
plt.figure(figsize=(12, 6))
plt.stem(range(len(ccf_precip_phdi))[:13], ccf_precip_phdi[:13], use_line_collection=True)
plt.title('Cross-Correlation: Precipitation vs. PHDI', fontsize=16)
plt.xlabel('Lag (Months)', fontsize=12)
plt.ylabel('Correlation Coefficient', fontsize=12)
plt.axhline(0, color='black', linewidth=0.8)
plt.grid(True, linestyle='--', linewidth=0.5)
plt.show()

# --- Create the Cross-Correlation Plot ---
plt.figure(figsize=(12, 6))
plt.stem(range(len(ccf_precip_pmdi))[:13], ccf_precip_pmdi[:13], use_line_collection=True)
plt.title('Cross-Correlation: Precipitation vs. PMDI', fontsize=16)
plt.xlabel('Lag (Months)', fontsize=12)
plt.ylabel('Correlation Coefficient', fontsize=12)
plt.axhline(0, color='black', linewidth=0.8)
plt.grid(True, linestyle='--', linewidth=0.5)
plt.show()

print("\n## Granger Causality Test: Does Precipitation predict PDSI? ##")
granger_test_results = grangercausalitytests(statewide_avg[['PDSI', 'Precip']], maxlag=3, verbose=True)
print(granger_test_results)

print("\n## Granger Causality Test: Does Precipitation predict PHDI? ##")
granger_test_results = grangercausalitytests(statewide_avg[['PHDI', 'Precip']], maxlag=3, verbose=True)
print(granger_test_results)

print("\n## Granger Causality Test: Does Precipitation predict PMDI? ##")
granger_test_results = grangercausalitytests(statewide_avg[['PMDI', 'Precip']], maxlag=3, verbose=True)
print(granger_test_results)

# --- Agricultural District-level Analysis of Precipitation and PDSI ---
print("\n## Creating Agricultural District-level Analysis of Precipitation and PDSI ##")

# Define the agricultural district mapping
district_counties = {
    'WESTERN': {'Allegany', 'Garrett'},
    'UPPER EASTERN SHORE': {'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'},
    'SOUTHERN': {'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"},
    'NORTH CENTRAL': {'Baltimore', 'Baltimore City', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 'Washington'},
    'LOWER EASTERN SHORE': {'Dorchester', 'Somerset', 'Wicomico', 'Worcester'}
}

# Add year and month columns for better analysis
merged_df['date'] = pd.to_datetime(merged_df['date'])
merged_df['Year'] = merged_df['date'].dt.year
merged_df['Month'] = merged_df['date'].dt.month

# Create a mapping from county to district
county_to_district = {}
for district, counties in district_counties.items():
    for county in counties:
        county_to_district[county] = district

# Add district information to the dataframe
merged_df['District'] = merged_df['County'].map(county_to_district)

# Remove rows where district mapping failed
merged_df = merged_df.dropna(subset=['District'])

# Filter for growing season months (April-October)
growing_season_df = merged_df[merged_df['Month'].between(4, 10)]

# Calculate yearly averages by district
district_yearly = growing_season_df.groupby(['District', 'Year'])[['Precip', 'PDSI']].mean().reset_index()

# Get unique districts and years
districts = sorted(district_yearly['District'].unique())
years = sorted(district_yearly['Year'].unique())

print(f"Analyzing {len(districts)} agricultural districts from {min(years)} to {max(years)}")
print(f"Districts: {districts}")

# Calculate global axis limits for consistency
precip_min = district_yearly['Precip'].min() - 0.5
precip_max = district_yearly['Precip'].max() + 0.5
pdsi_min = district_yearly['PDSI'].min() - 0.5
pdsi_max = district_yearly['PDSI'].max() + 0.5

print(f"Fixed axis ranges - Precipitation: {precip_min:.1f} to {precip_max:.1f}, PDSI: {pdsi_min:.1f} to {pdsi_max:.1f}")

# Create subplots for each district
n_districts = len(districts)
n_cols = 3
n_rows = (n_districts + n_cols - 1) // n_cols

fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6*n_rows))
axes = axes.flatten() if n_districts > 1 else [axes]

for i, district in enumerate(districts):
    ax = axes[i]
    
    # Get data for this district
    district_data = district_yearly[district_yearly['District'] == district]
    
    # Plot precipitation
    ax.plot(district_data['Year'], district_data['Precip'], 
            marker='o', linewidth=3, markersize=8, 
            color='blue', label='Precipitation', alpha=0.8)
    
    # Create second y-axis for PDSI
    ax2 = ax.twinx()
    ax2.plot(district_data['Year'], district_data['PDSI'], 
             marker='s', linewidth=3, markersize=8, 
             color='red', label='PDSI', alpha=0.8, linestyle='--')
    
    # Set fixed axis limits
    ax.set_ylim(precip_min, precip_max)
    ax2.set_ylim(pdsi_min, pdsi_max)
    
    # Customize the plot
    ax.set_title(f'{district}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Precipitation (inches)', fontsize=12, color='blue')
    ax2.set_ylabel('PDSI', fontsize=12, color='red')
    
    # Color the y-axis labels
    ax.tick_params(axis='y', labelcolor='blue')
    ax2.tick_params(axis='y', labelcolor='red')
    
    ax.grid(True, alpha=0.3)
    
    # Add horizontal reference lines
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
    
    # Add legend only to first subplot
    if i == 0:
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

# Remove empty subplots
for i in range(n_districts, len(axes)):
    fig.delaxes(axes[i])

plt.suptitle('Agricultural District Precipitation and PDSI Analysis (Growing Season Averages)', 
             fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout()
plt.show()

# Save the plot
plt.savefig('outputs/DroughtIndices/District_Precip_PDSI_Analysis_Fixed_Axes.png', dpi=300, bbox_inches='tight')
print("💾 Saved: outputs/DroughtIndices/District_Precip_PDSI_Analysis_Fixed_Axes.png")

# Create a summary table of district statistics
print("\n## Agricultural District Summary Statistics ##")
district_stats = district_yearly.groupby('District')[['Precip', 'PDSI']].agg(['mean', 'std', 'min', 'max']).round(2)
print(district_stats)

# Create a heatmap of district-year data for better visualization
print("\n## Creating District-Year Heatmaps ##")

# Pivot data for heatmap
precip_heatmap = district_yearly.pivot(index='District', columns='Year', values='Precip')
pdsi_heatmap = district_yearly.pivot(index='District', columns='Year', values='PDSI')

# Create heatmaps
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Precipitation heatmap
sns.heatmap(precip_heatmap, annot=True, cmap='Blues', fmt='.1f', ax=ax1, cbar_kws={'label': 'Precipitation (inches)'})
ax1.set_title('Precipitation by Agricultural District and Year\n(Growing Season Averages)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Year', fontsize=12)
ax1.set_ylabel('Agricultural District', fontsize=12)

# PDSI heatmap
sns.heatmap(pdsi_heatmap, annot=True, cmap='RdBu_r', center=0, fmt='.2f', ax=ax2, cbar_kws={'label': 'PDSI'})
ax2.set_title('PDSI by Agricultural District and Year\n(Growing Season Averages)', fontsize=14, fontweight='bold')
ax2.set_xlabel('Year', fontsize=12)
ax2.set_ylabel('Agricultural District', fontsize=12)

plt.tight_layout()
plt.show()

# Save the heatmaps
plt.savefig('outputs/DroughtIndices/District_Heatmaps_Precip_PDSI.png', dpi=300, bbox_inches='tight')
print("💾 Saved: outputs/DroughtIndices/District_Heatmaps_Precip_PDSI.png")


