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