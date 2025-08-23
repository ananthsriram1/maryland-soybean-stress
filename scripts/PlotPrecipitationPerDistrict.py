import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from IPython.display import display

# --- 1. Load Your Datasets ---
precip_file = 'data/maryland_precipitation_combined_wide.csv'
precip_df = pd.read_csv(precip_file, index_col='County')

nass_file_for_districts = 'data/maryland_nass_data_cleaned_with_district.csv'
district_map_df = pd.read_csv(nass_file_for_districts)
county_to_district = district_map_df[['County', 'Ag District']].drop_duplicates()


# --- 2. Reshape, Prepare, and STANDARDIZE the Data ---
# "Melt" the wide dataframe to a long format.
precip_long = precip_df.reset_index().melt(
    id_vars='County', 
    var_name='date', 
    value_name='Precipitation'
)

# Clean up the date column.
precip_long['date'] = precip_long['date'].str.replace('Precip_', '')
precip_long['date'] = pd.to_datetime(precip_long['date'])

# --- THIS IS THE FIX ---
# Standardize the 'County' column in both DataFrames to ensure they match.
precip_long['County'] = precip_long['County'].str.upper().str.strip()
county_to_district['County'] = county_to_district['County'].str.upper().str.strip()
# --- END OF FIX ---


# --- 3. Merge Precipitation Data with District Information ---
# This merge should now work correctly.
precip_with_districts = pd.merge(precip_long, county_to_district, on='County', how='left')


# --- 4. Calculate the Average Precipitation per District ---
district_avg_precip = precip_with_districts.groupby(['date', 'Ag District'])['Precipitation'].mean()
plot_data = district_avg_precip.unstack(level='Ag District')

# --- Calculate a 3-month rolling average for each district ---
rolling_avg_data = plot_data.rolling(window=3, center=True).mean()

# --- Plot the smoothed results ---
fig, ax = plt.subplots(figsize=(16, 8))

for district in rolling_avg_data.columns:
    ax.plot(rolling_avg_data.index, rolling_avg_data[district], label=district, alpha=0.8, linewidth=2.5)

# Formatting the plot
ax.set_title('3-Month Rolling Average Precipitation by Agricultural District', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Average Precipitation (Inches)', fontsize=12)
ax.legend(title='Ag District')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)
ax.axhline(y=plot_data.stack().mean(), color='r', linestyle='--', label='Overall Mean Precip') # Add overall average line
ax.legend(title='Ag District')

# Format the x-axis dates
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
plt.show()

# --- Filter for only the growing season months (June, July, August) ---
growing_season_data = plot_data[plot_data.index.month.isin([6, 7, 8])]

# --- Calculate the average precipitation for each growing season (year) ---
annual_growing_season_avg = growing_season_data.groupby(growing_season_data.index.year).mean()

# --- Plot the results ---
plt.figure(figsize=(12, 7))

for district in annual_growing_season_avg.columns:
    plt.plot(
        annual_growing_season_avg.index, 
        annual_growing_season_avg[district], 
        marker='o', 
        linestyle='-', 
        label=district
    )

# Formatting the plot
plt.title('Average Growing Season (Jun-Aug) Precipitation by District', fontsize=16)
plt.xlabel('Year', fontsize=12)
plt.ylabel('Average Precipitation (Inches)', fontsize=12)
plt.xticks(annual_growing_season_avg.index) # Ensure every year is a tick
plt.legend(title='Ag District')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()