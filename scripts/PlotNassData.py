import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

# --- 1. Load your final, clean NASS dataset ---
file_path = 'data/maryland_nass_data_cleaned_with_district.csv'
df = pd.read_csv(file_path)

print("Successfully loaded the cleaned NASS dataset. Here's a preview:")
display(df.head())

# --- 2. Group data by Year and Ag District and aggregate ---
# For acreage and production, we want the SUM for the entire district.
sum_cols = ['Acres_Planted', 'Acres_Harvested', 'Production_BU', 'Irrigated_Acres']
district_sums = df.groupby(['Year', 'Ag District'])[sum_cols].sum()

# For yield, we want the MEAN for the district.
avg_cols = ['Yield_BuAcre']
district_avgs = df.groupby(['Year', 'Ag District'])[avg_cols].mean()

# Combine the summed and averaged data into one table.
district_data = pd.merge(district_sums, district_avgs, on=['Year', 'Ag District'])

# Unstack the 'Ag District' level to turn it into columns for easy plotting.
plot_data = district_data.unstack(level='Ag District')

print("\nData aggregated by district and ready for plotting:")
display(plot_data.head())

# --- 3. Generate a Plot for Each Variable ---
# We will loop through each of our key variables and create a separate plot.
variables_to_plot = ['Acres_Planted', 'Acres_Harvested', 'Yield_BuAcre', 'Irrigated_Acres']

for var in variables_to_plot:
    plt.figure(figsize=(12, 7))
    
    # Select the data for the current variable and plot each district's line.
    data_to_plot = plot_data[var]
    
    for district in data_to_plot.columns:
        plt.plot(data_to_plot.index, data_to_plot[district], marker='o', linestyle='-', label=district)

    # Formatting the plot
    plt.title(f'Soybean {var.replace("_", " ")} by Agricultural District (2012-2024)', fontsize=16)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel(var.replace("_", " "), fontsize=12)
    plt.legend(title='Ag District', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.tight_layout() # Adjust layout to make room for the legend
    plt.show()