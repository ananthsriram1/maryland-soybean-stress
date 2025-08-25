import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from IPython.display import display

# Plot PDSI, PHDI, and PMDI by Agricultural District

print("--- Processing PDSI Data ---")
# --- 1. Load Datasets ---
pdsi_file = 'data/maryland_pdsi_combined_wide.csv'
pdsi_df = pd.read_csv(pdsi_file, index_col='County')

nass_file_for_districts = 'data/maryland_nass_data_cleaned_with_district.csv'
district_map_df = pd.read_csv(nass_file_for_districts)
county_to_district = district_map_df[['County', 'Ag District']].drop_duplicates()

# --- 2. Prepare and Standardize Data ---
pdsi_long = pdsi_df.reset_index().melt(
    id_vars='County', var_name='date', value_name='PDSI'
)
pdsi_long['date'] = pdsi_long['date'].str.replace('PDSI_', '')
pdsi_long['date'] = pd.to_datetime(pdsi_long['date'])
pdsi_long['County'] = pdsi_long['County'].str.upper().str.strip()
county_to_district['County'] = county_to_district['County'].str.upper().str.strip()

# --- 3. Merge and Aggregate ---
pdsi_with_districts = pd.merge(pdsi_long, county_to_district, on='County', how='left')
district_avg_pdsi = pdsi_with_districts.groupby(['date', 'Ag District'])['PDSI'].mean()
plot_data_pdsi = district_avg_pdsi.unstack(level='Ag District')

# --- 4. Plot 1: Rolling Average ---
rolling_avg_pdsi = plot_data_pdsi.rolling(window=3, center=True).mean()
fig, ax = plt.subplots(figsize=(16, 8))
for district in rolling_avg_pdsi.columns:
    ax.plot(rolling_avg_pdsi.index, rolling_avg_pdsi[district], label=district, alpha=0.8, linewidth=2.5)
ax.set_title('3-Month Rolling Average PDSI by Agricultural District', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('PDSI Value', fontsize=12)
ax.axhline(y=0, color='r', linestyle='--', label='Drought Threshold (0)')
ax.legend(title='Ag District')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.show()

# --- 5. Plot 2: Growing Season Average ---
growing_season_pdsi = plot_data_pdsi[plot_data_pdsi.index.month.isin([6, 7, 8])]
annual_growing_season_pdsi = growing_season_pdsi.groupby(growing_season_pdsi.index.year).mean()
plt.figure(figsize=(12, 7))
for district in annual_growing_season_pdsi.columns:
    plt.plot(annual_growing_season_pdsi.index, annual_growing_season_pdsi[district], marker='o', linestyle='-', label=district)
plt.title('Average Growing Season (Jun-Aug) PDSI by District', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Average PDSI Value', fontsize=12)
plt.xticks(annual_growing_season_pdsi.index)
plt.axhline(y=0, color='r', linestyle='--', label='Drought Threshold (0)')
plt.legend(title='Ag District')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

print("--- Processing PHDI Data ---")

# --- 1. Load Datasets ---
phdi_file = 'data/maryland_phdi_combined_wide.csv'
phdi_df = pd.read_csv(phdi_file, index_col='County')

# --- 2. Prepare and Standardize Data ---
phdi_long = phdi_df.reset_index().melt(
    id_vars='County', var_name='date', value_name='PHDI'
)
phdi_long['date'] = phdi_long['date'].str.replace('PHDI_', '')
phdi_long['date'] = pd.to_datetime(phdi_long['date'])
phdi_long['County'] = phdi_long['County'].str.upper().str.strip()
# county_to_district is already standardized from the previous script

# --- 3. Merge and Aggregate ---
phdi_with_districts = pd.merge(phdi_long, county_to_district, on='County', how='left')
district_avg_phdi = phdi_with_districts.groupby(['date', 'Ag District'])['PHDI'].mean()
plot_data_phdi = district_avg_phdi.unstack(level='Ag District')

# --- 4. Plot 1: Rolling Average ---
rolling_avg_phdi = plot_data_phdi.rolling(window=3, center=True).mean()
fig, ax = plt.subplots(figsize=(16, 8))
for district in rolling_avg_phdi.columns:
    ax.plot(rolling_avg_phdi.index, rolling_avg_phdi[district], label=district, alpha=0.8, linewidth=2.5)
ax.set_title('3-Month Rolling Average PHDI by Agricultural District', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('PHDI Value', fontsize=12)
ax.axhline(y=0, color='r', linestyle='--', label='Drought Threshold (0)')
ax.legend(title='Ag District')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.show()

# --- 5. Plot 2: Growing Season Average ---
growing_season_phdi = plot_data_phdi[plot_data_phdi.index.month.isin([6, 7, 8])]
annual_growing_season_phdi = growing_season_phdi.groupby(growing_season_phdi.index.year).mean()
plt.figure(figsize=(12, 7))
for district in annual_growing_season_phdi.columns:
    plt.plot(annual_growing_season_phdi.index, annual_growing_season_phdi[district], marker='o', linestyle='-', label=district)
plt.title('Average Growing Season (Jun-Aug) PHDI by District', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Average PHDI Value', fontsize=12)
plt.xticks(annual_growing_season_phdi.index)
plt.axhline(y=0, color='r', linestyle='--', label='Drought Threshold (0)')
plt.legend(title='Ag District')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

print("--- Processing PMDI Data ---")

# --- 1. Load Datasets ---
pmdi_file = 'data/maryland_pmdi_combined_wide.csv'
pmdi_df = pd.read_csv(pmdi_file, index_col='County')

# --- 2. Prepare and Standardize Data ---
pmdi_long = pmdi_df.reset_index().melt(
    id_vars='County', var_name='date', value_name='PMDI'
)
pmdi_long['date'] = pmdi_long['date'].str.replace('PMDI_', '')
pmdi_long['date'] = pd.to_datetime(pmdi_long['date'])
pmdi_long['County'] = pmdi_long['County'].str.upper().str.strip()
# county_to_district is already standardized

# --- 3. Merge and Aggregate ---
pmdi_with_districts = pd.merge(pmdi_long, county_to_district, on='County', how='left')
district_avg_pmdi = pmdi_with_districts.groupby(['date', 'Ag District'])['PMDI'].mean()
plot_data_pmdi = district_avg_pmdi.unstack(level='Ag District')

# --- 4. Plot 1: Rolling Average ---
rolling_avg_pmdi = plot_data_pmdi.rolling(window=3, center=True).mean()
fig, ax = plt.subplots(figsize=(16, 8))
for district in rolling_avg_pmdi.columns:
    ax.plot(rolling_avg_pmdi.index, rolling_avg_pmdi[district], label=district, alpha=0.8, linewidth=2.5)
ax.set_title('3-Month Rolling Average PMDI by Agricultural District', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('PMDI Value', fontsize=12)
ax.axhline(y=0, color='r', linestyle='--', label='Drought Threshold (0)')
ax.legend(title='Ag District')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.show()

# --- 5. Plot 2: Growing Season Average ---
growing_season_pmdi = plot_data_pmdi[plot_data_pmdi.index.month.isin([6, 7, 8])]
annual_growing_season_pmdi = growing_season_pmdi.groupby(growing_season_pmdi.index.year).mean()
plt.figure(figsize=(12, 7))
for district in annual_growing_season_pmdi.columns:
    plt.plot(annual_growing_season_pmdi.index, annual_growing_season_pmdi[district], marker='o', linestyle='-', label=district)
plt.title('Average Growing Season (Jun-Aug) PMDI by District', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Average PMDI Value', fontsize=12)
plt.xticks(annual_growing_season_pmdi.index)
plt.axhline(y=0, color='r', linestyle='--', label='Drought Threshold (0)')
plt.legend(title='Ag District')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()
