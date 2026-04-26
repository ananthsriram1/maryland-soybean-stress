import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from IPython.display import display

# =================================================================
#      SCRIPT 1: Plot Overall NDVI Trend by Agricultural District
# =================================================================

print("--- Processing NDVI Data ---")

# --- 1. Load Datasets ---
ndvi_file = 'data/maryland_only_soybean_ndvi_timeseries_FINAL.csv'
ndvi_df = pd.read_csv(ndvi_file, index_col='NAME')

nass_file = 'data/maryland_nass_data_cleaned_with_district.csv'
nass_df = pd.read_csv(nass_file)
county_to_district = nass_df[['County', 'Ag District']].drop_duplicates()

# --- 2. Prepare and Standardize Data ---
ndvi_df.index.name = 'County'
ndvi_df = ndvi_df.reset_index()
ndvi_df['County'] = ndvi_df['County'].str.upper().str.strip()
county_to_district['County'] = county_to_district['County'].str.upper().str.strip()

ndvi_long = ndvi_df.melt(id_vars='County', var_name='date', value_name='NDVI')
ndvi_long['date'] = pd.to_datetime(ndvi_long['date'].str.replace('SoybeanNDVI_', ''))

# --- 3. Merge and Aggregate ---
ndvi_with_districts = pd.merge(ndvi_long, county_to_district, on='County', how='left')
district_avg_ndvi = ndvi_with_districts.groupby(['date', 'Ag District'])['NDVI'].mean()
plot_data_ndvi = district_avg_ndvi.unstack(level='Ag District')

# --- 4. Plot 1: Overall Trend Time-Series ---
fig, ax = plt.subplots(figsize=(16, 8))
plot_data_ndvi.plot(ax=ax, style='-o', alpha=0.8)
ax.set_title('Average Monthly Soybean NDVI by Agricultural District (2021-2024)', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Average Soybean NDVI', fontsize=12)
ax.legend(title='Ag District')
ax.grid(True, linestyle='--', linewidth=0.5)
ax.set_ylim(0, 1)
plt.show()


# =================================================================
#      SCRIPT 2: Plot Seasonal NDVI Profile by District
# =================================================================

# --- 1. Extract month number ---
ndvi_with_districts['month'] = ndvi_with_districts['date'].dt.month

# --- 2. Create a monthly box plot ---
plt.figure(figsize=(14, 8))
sns.boxplot(data=ndvi_with_districts, x='month', y='NDVI', hue='Ag District')
plt.title('Typical Seasonal NDVI Profile by Agricultural District', fontsize=18)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Soybean NDVI Distribution', fontsize=12)
plt.legend(title='Ag District', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()


# =================================================================
#      SCRIPT 3: Plot Drought Impact (Dry Year vs. Wet Year)
# =================================================================

# --- 1. Define years for comparison (update these based on your drought data) ---
dry_year = 2023
wet_year = 2021

# --- 2. Calculate average growing season (Jun-Aug) NDVI ---
growing_season_ndvi = ndvi_with_districts[ndvi_with_districts['date'].dt.month.isin([6, 7, 8])]
year_comparison_ndvi = growing_season_ndvi[growing_season_ndvi['date'].dt.year.isin([dry_year, wet_year])]
comparison_summary_ndvi = year_comparison_ndvi.groupby([year_comparison_ndvi['date'].dt.year.rename('Year'), 'Ag District'])['NDVI'].mean().reset_index()

# --- 3. Create a grouped bar chart ---
plt.figure(figsize=(12, 7))
sns.barplot(data=comparison_summary_ndvi, x='Ag District', y='NDVI', hue='Year')
plt.title(f'Growing Season NDVI: Drought Year ({dry_year}) vs. Wet Year ({wet_year})', fontsize=16)
plt.ylabel('Average Growing Season NDVI', fontsize=12)
plt.xlabel('Agricultural District', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()


# =================================================================
#      SCRIPT 4: Plot NDVI vs. Final Yield (Multi-Year Analysis)
# =================================================================

# --- 1. Load NASS yield data for all years ---
nass_yield_df = pd.read_csv('data/Soybean_Yield_BU:Acre_By_County.csv')
nass_yield_df['County'] = nass_yield_df['County'].str.upper().str.strip()

# --- 2. Analyze each year from 2021-2024 ---
years_to_analyze = [2021, 2022, 2023, 2024]
all_years_data = []

for year in years_to_analyze:
    # Calculate peak growing season NDVI metric for each county for this year
    peak_ndvi_df = ndvi_with_districts[ndvi_with_districts['date'].dt.year == year]
    peak_ndvi_df = peak_ndvi_df[peak_ndvi_df['date'].dt.month.isin([7, 8])]
    
    if not peak_ndvi_df.empty:
        peak_ndvi_metric = peak_ndvi_df.groupby('County')['NDVI'].max().reset_index()
        peak_ndvi_metric = peak_ndvi_metric.rename(columns={'NDVI': 'Peak_NDVI'})
        
        # Prepare NASS yield data for this year
        nass_yield_year = nass_yield_df[nass_yield_df['Year'] == year][['County', 'Value']]
        if not nass_yield_year.empty:
            nass_yield_year.columns = ['County', 'Yield_BuAcre']
            
            # Merge NDVI metric with yield data
            validation_df_ndvi = pd.merge(peak_ndvi_metric, nass_yield_year, on='County')
            validation_df_ndvi = pd.merge(validation_df_ndvi, county_to_district, on='County')
            validation_df_ndvi['Year'] = year
            
            all_years_data.append(validation_df_ndvi)

# --- 3. Combine all years data ---
if all_years_data:
    combined_data = pd.concat(all_years_data, ignore_index=True)
    
    # Create a comprehensive scatter plot for all years
    plt.figure(figsize=(14, 10))
    
    # Create subplots for each year
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Peak Growing Season NDVI vs. Final Yield (2021-2024)', fontsize=18, y=0.95)
    
    for i, year in enumerate(years_to_analyze):
        row = i // 2
        col = i % 2
        ax = axes[row, col]
        
        year_data = combined_data[combined_data['Year'] == year]
        
        if not year_data.empty:
            # Add regression line
            sns.regplot(data=year_data, x='Peak_NDVI', y='Yield_BuAcre', 
                       scatter=False, color='red', ax=ax)
            # Add scatter plot
            sns.scatterplot(data=year_data, x='Peak_NDVI', y='Yield_BuAcre', 
                           hue='Ag District', s=80, ax=ax)
            
            ax.set_title(f'Year {year}', fontsize=14)
            ax.set_xlabel('Peak Soybean NDVI (Jul-Aug)', fontsize=10)
            ax.set_ylabel('Final Yield (Bushels / Acre)', fontsize=10)
            ax.grid(True, linestyle='--', linewidth=0.5)
            ax.legend(title='Ag District', fontsize=8)
        else:
            ax.text(0.5, 0.5, f'No data for {year}', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(f'Year {year}', fontsize=14)
    
    plt.tight_layout()
    plt.show()
    
    # --- 4. Create a combined analysis plot ---
    plt.figure(figsize=(12, 8))
    
    # Color code by year
    colors = ['blue', 'green', 'red', 'purple']
    for i, year in enumerate(years_to_analyze):
        year_data = combined_data[combined_data['Year'] == year]
        if not year_data.empty:
            plt.scatter(year_data['Peak_NDVI'], year_data['Yield_BuAcre'], 
                       c=colors[i], label=f'{year}', s=80, alpha=0.7)
    
    # Add overall regression line
    sns.regplot(data=combined_data, x='Peak_NDVI', y='Yield_BuAcre', 
               scatter=False, color='black', line_kws={'linewidth': 2})
    
    plt.title('Peak Growing Season NDVI vs. Final Yield (All Years Combined)', fontsize=16)
    plt.xlabel('Peak Soybean NDVI (Jul-Aug)', fontsize=12)
    plt.ylabel('Final Yield (Bushels / Acre)', fontsize=12)
    plt.legend(title='Year')
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.show()
    
    # --- 5. Print summary statistics ---
    print("\n=== NDVI vs. Yield Analysis Summary ===")
    for year in years_to_analyze:
        year_data = combined_data[combined_data['Year'] == year]
        if not year_data.empty:
            correlation = year_data['Peak_NDVI'].corr(year_data['Yield_BuAcre'])
            print(f"Year {year}: {len(year_data)} counties, Correlation: {correlation:.3f}")
        else:
            print(f"Year {year}: No data available")
else:
    print("No data available for any of the specified years.")
