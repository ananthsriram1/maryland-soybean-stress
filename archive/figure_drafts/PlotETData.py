import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from IPython.display import display

# =================================================================
#      SETUP: Load and Prepare the Master ET Dataset
# =================================================================
print("--- ET Data Visualization Suite ---")

# --- 1. Load Datasets ---
et_file = 'data/maryland_only_et_timeseries_FINAL.csv'
et_df = pd.read_csv(et_file, index_col='NAME')

nass_file = 'data/maryland_nass_data_cleaned_with_district.csv'
nass_df = pd.read_csv(nass_file)
county_to_district = nass_df[['County', 'Ag District']].drop_duplicates()

# --- 2. Prepare and Standardize Data ---
et_df.index.name = 'County'
et_df = et_df.reset_index()

# Standardize the 'County' column in both DataFrames to ensure they match.
et_df['County'] = et_df['County'].str.upper().str.strip()
county_to_district['County'] = county_to_district['County'].str.upper().str.strip()

# Melt the wide dataframe to a long format.
et_long = et_df.melt(id_vars='County', var_name='date', value_name='ET')
# The .replace() function correctly handles your 'ET_YYYY-MM' column names.
et_long['date'] = pd.to_datetime(et_long['date'].str.replace('ET_', ''))

# --- 3. Merge and Aggregate ---
et_with_districts = pd.merge(et_long, county_to_district, on='County', how='left')
district_avg_et = et_with_districts.groupby(['date', 'Ag District'])['ET'].mean()
plot_data_et = district_avg_et.unstack(level='Ag District')

print("Data prepared. Generating plots...")

# =================================================================
#      PLOT 1: Overall ET Trend by Agricultural District
# =================================================================
fig, ax = plt.subplots(figsize=(16, 8))
plot_data_et.plot(ax=ax, style='-o', alpha=0.8)
ax.set_title('Average Monthly Soybean Evapotranspiration (ET) by District', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Average ET (mm per month)', fontsize=12)
ax.legend(title='Ag District')
ax.grid(True, linestyle='--', linewidth=0.5)
plt.show()


# =================================================================
#      PLOT 2: Typical Seasonal ET Profile by District
# =================================================================
et_with_districts['month'] = et_with_districts['date'].dt.month
plt.figure(figsize=(14, 8))
sns.boxplot(data=et_with_districts, x='month', y='ET', hue='Ag District')
plt.title('Typical Seasonal ET Profile by Agricultural District', fontsize=18)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Soybean ET Distribution (mm)', fontsize=12)
plt.legend(title='Ag District', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()


# =================================================================
#      PLOT 3: Drought Impact (Dry Year vs. Wet Year)
# =================================================================
dry_year = 2023
wet_year = 2021

growing_season_et = et_with_districts[et_with_districts['date'].dt.month.isin([6, 7, 8])]
year_comparison_et = growing_season_et[growing_season_et['date'].dt.year.isin([dry_year, wet_year])]
# For ET, we sum the monthly values to get a total for the growing season
comparison_summary_et = year_comparison_et.groupby([year_comparison_et['date'].dt.year.rename('Year'), 'Ag District'])['ET'].sum().reset_index()

plt.figure(figsize=(12, 7))
sns.barplot(data=comparison_summary_et, x='Ag District', y='ET', hue='Year')
plt.title(f'Total Growing Season ET: Drought Year ({dry_year}) vs. Wet Year ({wet_year})', fontsize=16)
plt.ylabel('Total Growing Season ET (mm)', fontsize=12)
plt.xlabel('Agricultural District', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()


# =================================================================
#      SCRIPT 4: Plot ET vs. Final Yield (with Consistent Colors)
# =================================================================

# --- 1. Define a consistent color palette for the districts ---
district_colors = {
    'UPPER EASTERN SHORE': 'blue',
    'LOWER EASTERN SHORE': 'cyan',
    'NORTH CENTRAL': 'green',
    'SOUTHERN': 'orange',
    'WESTERN': 'purple'
}

# --- 2. Calculate a peak growing season ET metric for each county for each year ---
years_to_analyze = [2021, 2022, 2023, 2024]
all_years_data = []

nass_yield_df = pd.read_csv('data/nass/Soybean_Yield_BU:Acre_By_County.csv')
nass_yield_df['County'] = nass_yield_df['County'].str.upper().str.strip()

for year in years_to_analyze:
    peak_et_df = et_with_districts[et_with_districts['date'].dt.year == year]
    peak_et_df = peak_et_df[peak_et_df['date'].dt.month.isin([7, 8])]
    
    if not peak_et_df.empty:
        peak_et_metric = peak_et_df.groupby('County')['ET'].max().reset_index()
        peak_et_metric = peak_et_metric.rename(columns={'ET': 'Peak_ET'})
        
        nass_yield_year = nass_yield_df[nass_yield_df['Year'] == year][['County', 'Value']]
        if not nass_yield_year.empty:
            nass_yield_year.columns = ['County', 'Yield_BuAcre']
            
            validation_df = pd.merge(peak_et_metric, nass_yield_year, on='County')
            validation_df = pd.merge(validation_df, county_to_district, on='County')
            validation_df['Year'] = year
            
            all_years_data.append(validation_df)

# --- 3. Create subplots for each year with consistent colors ---
if all_years_data:
    combined_data = pd.concat(all_years_data, ignore_index=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), sharex=True, sharey=True)
    fig.suptitle('Peak Growing Season ET vs. Final Yield (2021-2024)', fontsize=18, y=0.95)
    
    axes_flat = axes.flatten()

    for i, year in enumerate(years_to_analyze):
        ax = axes_flat[i]
        year_data = combined_data[combined_data['Year'] == year]
        
        if not year_data.empty:
            sns.regplot(data=year_data, x='Peak_ET', y='Yield_BuAcre', 
                       scatter=False, color='gray', ax=ax, line_kws={'linestyle':'--'})
            
            sns.scatterplot(data=year_data, x='Peak_ET', y='Yield_BuAcre', 
                           hue='Ag District', s=100, ax=ax, palette=district_colors)
            
            ax.set_title(f'Year {year}', fontsize=14)
            ax.set_xlabel('Peak Soybean ET (Jul-Aug)', fontsize=10)
            ax.set_ylabel('Final Yield (Bushels / Acre)', fontsize=10)
            ax.grid(True, linestyle='--', linewidth=0.5)
            ax.legend(title='Ag District', fontsize=8)
        else:
            ax.text(0.5, 0.5, f'No data for {year}', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12)
            ax.set_title(f'Year {year}', fontsize=14)
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()
