import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from IPython.display import display
import seaborn as sns


#      SCRIPT 1: Plot Overall NDRE Trend by Agricultural District
# =================================================================

print("--- Processing NDRE Data ---")

# --- 1. Load Datasets ---
ndre_file = 'data/maryland_only_ndre_timeseries_FINAL.csv'
ndre_df = pd.read_csv(ndre_file, index_col='NAME')

nass_file = 'data/maryland_nass_data_cleaned_with_district.csv'
nass_df = pd.read_csv(nass_file)
county_to_district = nass_df[['County', 'Ag District']].drop_duplicates()

# --- 2. Prepare and Standardize Data ---
ndre_df.index.name = 'County'
ndre_df = ndre_df.reset_index()
ndre_df['County'] = ndre_df['County'].str.upper().str.strip()
county_to_district['County'] = county_to_district['County'].str.upper().str.strip()

ndre_long = ndre_df.melt(id_vars='County', var_name='date', value_name='NDRE')
ndre_long['date'] = pd.to_datetime(ndre_long['date'].str.replace('NDRE_', ''))

# --- 3. Merge and Aggregate ---
ndre_with_districts = pd.merge(ndre_long, county_to_district, on='County', how='left')
district_avg_ndre = ndre_with_districts.groupby(['date', 'Ag District'])['NDRE'].mean()
plot_data_ndre = district_avg_ndre.unstack(level='Ag District')

# --- 4. Plot 1: Overall Trend Time-Series ---
fig, ax = plt.subplots(figsize=(16, 8))
plot_data_ndre.plot(ax=ax, style='-o', alpha=0.8)
ax.set_title('Average Monthly Soybean NDRE by Agricultural District (2021-2024)', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Average Soybean NDRE', fontsize=12)
ax.legend(title='Ag District')
ax.grid(True, linestyle='--', linewidth=0.5)
ax.set_ylim(0, 1)
plt.show()


# =================================================================
#      SCRIPT 2: Plot Seasonal NDRE Profile by District
# =================================================================

# --- 1. Extract month number ---
ndre_with_districts['month'] = ndre_with_districts['date'].dt.month

# --- 2. Create a monthly box plot ---
plt.figure(figsize=(14, 8))
sns.boxplot(data=ndre_with_districts, x='month', y='NDRE', hue='Ag District')
plt.title('Typical Seasonal NDRE Profile by Agricultural District', fontsize=18)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Soybean NDRE Distribution', fontsize=12)
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

# --- 2. Calculate average growing season (Jun-Aug) NDRE ---
growing_season_ndre = ndre_with_districts[ndre_with_districts['date'].dt.month.isin([6, 7, 8])]
year_comparison_ndre = growing_season_ndre[growing_season_ndre['date'].dt.year.isin([dry_year, wet_year])]
comparison_summary_ndre = year_comparison_ndre.groupby([year_comparison_ndre['date'].dt.year.rename('Year'), 'Ag District'])['NDRE'].mean().reset_index()

# --- 3. Create a grouped bar chart ---
plt.figure(figsize=(12, 7))
sns.barplot(data=comparison_summary_ndre, x='Ag District', y='NDRE', hue='Year')
plt.title(f'Growing Season NDRE: Drought Year ({dry_year}) vs. Wet Year ({wet_year})', fontsize=16)
plt.ylabel('Average Growing Season NDRE', fontsize=12)
plt.xlabel('Agricultural District', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()


# =================================================================
#      SCRIPT 4: Plot NDRE vs. Final Yield (with Consistent Colors)
# =================================================================

# --- 1. Define a consistent color palette for the districts ---
district_colors = {
    'UPPER EASTERN SHORE': 'blue',
    'LOWER EASTERN SHORE': 'cyan',
    'NORTH CENTRAL': 'green',
    'SOUTHERN': 'orange',
    'WESTERN': 'purple'
}

# --- 2. Calculate a peak growing season NDRE metric for each county for each year ---
years_to_analyze = [2021, 2022, 2023, 2024]
all_years_data = []

nass_yield_df = pd.read_csv('data/Soybean_Yield_BU:Acre_By_County.csv')
nass_yield_df['County'] = nass_yield_df['County'].str.upper().str.strip()

for year in years_to_analyze:
    peak_ndre_df = ndre_with_districts[ndre_with_districts['date'].dt.year == year]
    peak_ndre_df = peak_ndre_df[peak_ndre_df['date'].dt.month.isin([7, 8])]
    
    if not peak_ndre_df.empty:
        peak_ndre_metric = peak_ndre_df.groupby('County')['NDRE'].max().reset_index()
        peak_ndre_metric = peak_ndre_metric.rename(columns={'NDRE': 'Peak_NDRE'})
        
        nass_yield_year = nass_yield_df[nass_yield_df['Year'] == year][['County', 'Value']]
        if not nass_yield_year.empty:
            nass_yield_year.columns = ['County', 'Yield_BuAcre']
            
            validation_df = pd.merge(peak_ndre_metric, nass_yield_year, on='County')
            validation_df = pd.merge(validation_df, county_to_district, on='County')
            validation_df['Year'] = year
            
            all_years_data.append(validation_df)

# --- 3. Create subplots for each year with consistent colors ---
if all_years_data:
    combined_data = pd.concat(all_years_data, ignore_index=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True, sharey=True)
    fig.suptitle('Peak Growing Season NDRE vs. Final Yield (2021-2024)', fontsize=18, y=0.95)
    
    axes_flat = axes.flatten()

    for i, year in enumerate(years_to_analyze):
        ax = axes_flat[i]
        year_data = combined_data[combined_data['Year'] == year]
        
        if not year_data.empty:
            sns.regplot(data=year_data, x='Peak_NDRE', y='Yield_BuAcre', 
                       scatter=False, color='gray', ax=ax, line_kws={'linestyle':'--'})
            
            sns.scatterplot(data=year_data, x='Peak_NDRE', y='Yield_BuAcre', 
                           hue='Ag District', s=100, ax=ax, palette=district_colors)
            
            ax.set_title(f'Year {year}', fontsize=14)
            ax.set_xlabel('Peak Soybean NDRE (Jul-Aug)', fontsize=10)
            ax.set_ylabel('Final Yield (Bushels / Acre)', fontsize=10)
            ax.grid(True, linestyle='--', linewidth=0.5)
            ax.legend(title='Ag District', fontsize=8)
        else:
            ax.text(0.5, 0.5, f'No data for {year}', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(f'Year {year}', fontsize=14)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()
