import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from IPython.display import display

# --- 1. Load your final, clean dataset ---
file_path = 'data/maryland_only_soybean_ndvi_timeseries_FINAL.csv'
df = pd.read_csv(file_path, index_col='NAME')

# --- 2. Define the counties for each NASS Agricultural District ---
# NOTE: We are combining Upper and Lower Eastern Shore for a cleaner chart.
upper_eastern_shore_counties = [
    'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'
]

# Lower Eastern Shore counties  
lower_eastern_shore_counties = [
    'Dorchester', 'Somerset', 'Wicomico', 'Worcester'
]

north_central_counties = [
    'Baltimore', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 
    'Washington'
]
southern_md_counties = [
    'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"
]
western_md_counties = [
    'Allegany', 'Garrett'
]

# --- 3. Calculate the average NDVI for each region ---
upper_eastern_avg = df.T[upper_eastern_shore_counties].mean(axis=1)
lower_eastern_avg = df.T[lower_eastern_shore_counties].mean(axis=1)
north_central_avg = df.T[north_central_counties].mean(axis=1)
southern_avg = df.T[southern_md_counties].mean(axis=1)
western_avg = df.T[western_md_counties].mean(axis=1)

# Convert the index to a proper datetime format for plotting.
upper_eastern_avg.index = pd.to_datetime(upper_eastern_avg.index.str.replace('SoybeanNDVI_', ''))
lower_eastern_avg.index = pd.to_datetime(lower_eastern_avg.index.str.replace('SoybeanNDVI_', ''))
north_central_avg.index = pd.to_datetime(north_central_avg.index.str.replace('SoybeanNDVI_', ''))
southern_avg.index = pd.to_datetime(southern_avg.index.str.replace('SoybeanNDVI_', ''))
western_avg.index = pd.to_datetime(western_avg.index.str.replace('SoybeanNDVI_', ''))


# --- 4. Plot the results ---
fig, ax = plt.subplots(figsize=(16, 8))

# Plot a separate line for each agricultural district
ax.plot(upper_eastern_avg.index, upper_eastern_avg.values, marker='o', linestyle='-', label='Upper Eastern Shore')
ax.plot(lower_eastern_avg.index, lower_eastern_avg.values, marker='s', linestyle='--', label='Lower Eastern Shore')
ax.plot(north_central_avg.index, north_central_avg.values, marker='^', linestyle=':', label='North Central MD')
ax.plot(southern_avg.index, southern_avg.values, marker='D', linestyle='-.', label='Southern MD')
ax.plot(western_avg.index, western_avg.values, marker='*', linestyle='-', label='Western MD')

# Formatting the plot
ax.set_title('Soybean NDVI by Maryland Agricultural District (2021-2024)', fontsize=18)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Average Soybean NDVI', fontsize=12)
ax.legend(fontsize=11)
ax.grid(True, which='both', linestyle='--', linewidth=0.5)
ax.set_ylim(0, 1)

# Format the x-axis dates
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
plt.setp(ax.xaxis.get_minorticklabels(), rotation=45)

plt.show()

