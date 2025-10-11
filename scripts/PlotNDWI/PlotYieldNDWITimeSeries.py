#!/usr/bin/env python3
"""
Yield vs NDWI Time Series Analysis

This script creates time series plots showing yield and NDWI throughout the years
with lines averaging each by agricultural district, following the format of PlotMonthlyNDWI.

Author: Analysis for Maryland Soybean Stress Project
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

# Set style for better plots
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    try:
        plt.style.use('seaborn')
    except OSError:
        plt.style.use('default')
        print("⚠️  Using default matplotlib style")

sns.set_palette("husl")

# Universal color scheme for agricultural districts (same as other scripts)
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFD700'             # Bright Gold - Lowest development (more visible)
}

def load_and_prepare_data():
    """Load and prepare NDWI and NASS yield data"""
    print("🔄 Loading NDWI and NASS data...")
    
    try:
        # Load NDWI data
        ndwi_df = pd.read_csv('data/maryland_ndwi_10day_final_imputed.csv', index_col='NAME')
        print(f"   ✅ NDWI data loaded: {ndwi_df.shape}")
        
        # Load NASS yield data
        nass_df = pd.read_csv('data/maryland_nass_data_cleaned_with_district.csv')
        print(f"   ✅ NASS data loaded: {nass_df.shape}")
        
        return ndwi_df, nass_df
    except Exception as e:
        print(f"   ❌ Error loading data: {e}")
        raise

def extract_yearly_data(ndwi_df, nass_df):
    """Extract and organize yearly NDWI and yield data by agricultural district"""
    print("📊 Extracting yearly NDWI and yield data...")
    
    # Process NDWI data - calculate yearly averages
    ndwi_yearly_data = []
    
    for county in ndwi_df.index:
        district = ndwi_df.loc[county, 'Ag_District']
        
        for year in [2019, 2020, 2021, 2022, 2023, 2024]:
            # Find all NDWI columns for this year
            year_cols = [col for col in ndwi_df.columns if str(year) in col]
            
            if year_cols:
                # Get NDWI values for this county-year
                ndwi_values = []
                for col in year_cols:
                    value = ndwi_df.loc[county, col]
                    if pd.notna(value) and value != 0:
                        ndwi_values.append(value)
                
                if ndwi_values:
                    avg_ndwi = np.mean(ndwi_values)
                    min_ndwi = np.min(ndwi_values)
                    max_ndwi = np.max(ndwi_values)
                    
                    ndwi_yearly_data.append({
                        'County': county,
                        'District': district,
                        'Year': year,
                        'Avg_NDWI': avg_ndwi,
                        'Min_NDWI': min_ndwi,
                        'Max_NDWI': max_ndwi,
                        'Data_Points': len(ndwi_values)
                    })
    
    ndwi_yearly_df = pd.DataFrame(ndwi_yearly_data)
    print(f"   ✅ NDWI yearly data extracted: {len(ndwi_yearly_df)} records")
    
    # Process NASS yield data
    yield_yearly_data = []
    
    for _, row in nass_df.iterrows():
        county = row['County']
        year = row['Year']
        yield_value = row['Yield_BuAcre']
        district = row['Ag District']
        
        if pd.notna(yield_value) and yield_value > 0:
            yield_yearly_data.append({
                'County': county,
                'District': district,
                'Year': year,
                'Yield_BuAcre': yield_value
            })
    
    yield_yearly_df = pd.DataFrame(yield_yearly_data)
    print(f"   ✅ Yield yearly data extracted: {len(yield_yearly_df)} records")
    
    return ndwi_yearly_df, yield_yearly_df

def create_yield_time_series_plots(yield_df):
    """Create time series plots for yield by agricultural district"""
    print("\n📊 Creating yield time series plots...")
    
    # Create output directory
    output_dir = 'outputs/YieldNDWITimeSeries'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate district averages by year
    district_yearly_avg = yield_df.groupby(['District', 'Year']).agg({
        'Yield_BuAcre': ['mean', 'std', 'count']
    }).round(2)
    
    # Flatten column names
    district_yearly_avg.columns = ['Avg_Yield', 'Std_Yield', 'County_Count']
    district_yearly_avg = district_yearly_avg.reset_index()
    
    # Calculate global axis limits for consistency
    all_yield_values = yield_df['Yield_BuAcre'].values
    y_min = np.percentile(all_yield_values, 5) - 5  # 5th percentile minus buffer
    y_max = np.percentile(all_yield_values, 95) + 5  # 95th percentile plus buffer
    
    # Round to nice numbers
    y_min = np.floor(y_min / 5) * 5
    y_max = np.ceil(y_max / 5) * 5
    
    print(f"   📏 Setting consistent Y-axis range: {y_min:.0f} to {y_max:.0f} Bu/Acre")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Get unique years and sort them
    years = sorted(yield_df['Year'].unique())
    
    # Plot data for each district
    for district in sorted(district_yearly_avg['District'].unique()):
        district_data = district_yearly_avg[district_yearly_avg['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        # Plot the main line with district averages
        ax.plot(district_data['Year'], district_data['Avg_Yield'], 
               marker='o', linewidth=3, markersize=8, 
               color=color, label=f'{district} (n={district_data["County_Count"].sum()})', 
               alpha=0.8)
        
        # Add error bars for standard deviation
        ax.errorbar(district_data['Year'], district_data['Avg_Yield'], 
                   yerr=district_data['Std_Yield'], 
                   color=color, alpha=0.3, capsize=5)
        
        # Add individual county data points (more visible)
        county_data = yield_df[yield_df['District'] == district]
        for year in years:
            year_county_data = county_data[county_data['Year'] == year]
            if len(year_county_data) > 0:
                x_jittered = np.random.normal(year, 0.1, len(year_county_data))
                ax.scatter(x_jittered, year_county_data['Yield_BuAcre'], 
                         color=color, alpha=0.6, s=40, zorder=1, edgecolors='white', linewidth=0.5)
    
    # Customize the plot
    ax.set_title('Soybean Yield Time Series by Agricultural District\n(2019-2024)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    ax.set_ylim(y_min, y_max)  # Set consistent Y-axis limits
    ax.grid(True, alpha=0.3)
    ax.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add statistics text box
    total_counties = yield_df['County'].nunique()
    total_districts = yield_df['District'].nunique()
    avg_yield = yield_df['Yield_BuAcre'].mean()
    min_yield = yield_df['Yield_BuAcre'].min()
    max_yield = yield_df['Yield_BuAcre'].max()
    
    stats_text = f'Overall Statistics:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Districts: {total_districts}\n'
    stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre\n'
    stats_text += f'Range: {min_yield:.1f} - {max_yield:.1f}'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Yield_Time_Series_by_District.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_ndwi_time_series_plots(ndwi_df):
    """Create time series plots for NDWI by agricultural district"""
    print("\n📊 Creating NDWI time series plots...")
    
    # Create output directory
    output_dir = 'outputs/YieldNDWITimeSeries'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate district averages by year
    district_yearly_avg = ndwi_df.groupby(['District', 'Year']).agg({
        'Avg_NDWI': ['mean', 'std', 'count']
    }).round(3)
    
    # Flatten column names
    district_yearly_avg.columns = ['Avg_NDWI', 'Std_NDWI', 'County_Count']
    district_yearly_avg = district_yearly_avg.reset_index()
    
    # Calculate global axis limits for consistency
    all_ndwi_values = ndwi_df['Avg_NDWI'].values
    y_min = np.percentile(all_ndwi_values, 5) - 0.05  # 5th percentile minus buffer
    y_max = np.percentile(all_ndwi_values, 95) + 0.05  # 95th percentile plus buffer
    
    # Round to nice numbers
    y_min = np.floor(y_min * 10) / 10
    y_max = np.ceil(y_max * 10) / 10
    
    print(f"   📏 Setting consistent Y-axis range: {y_min:.1f} to {y_max:.1f}")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Get unique years and sort them
    years = sorted(ndwi_df['Year'].unique())
    
    # Plot data for each district
    for district in sorted(district_yearly_avg['District'].unique()):
        district_data = district_yearly_avg[district_yearly_avg['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        # Plot the main line with district averages
        ax.plot(district_data['Year'], district_data['Avg_NDWI'], 
               marker='o', linewidth=3, markersize=8, 
               color=color, label=f'{district} (n={district_data["County_Count"].sum()})', 
               alpha=0.8)
        
        # Add error bars for standard deviation
        ax.errorbar(district_data['Year'], district_data['Avg_NDWI'], 
                   yerr=district_data['Std_NDWI'], 
                   color=color, alpha=0.3, capsize=5)
        
        # Add individual county data points (more visible)
        county_data = ndwi_df[ndwi_df['District'] == district]
        for year in years:
            year_county_data = county_data[county_data['Year'] == year]
            if len(year_county_data) > 0:
                x_jittered = np.random.normal(year, 0.1, len(year_county_data))
                ax.scatter(x_jittered, year_county_data['Avg_NDWI'], 
                         color=color, alpha=0.6, s=40, zorder=1, edgecolors='white', linewidth=0.5)
    
    # Customize the plot
    ax.set_title('NDWI Time Series by Agricultural District\n(2019-2024)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('NDWI (Normalized Difference Water Index)', fontsize=12)
    ax.set_ylim(y_min, y_max)  # Set consistent Y-axis limits
    ax.grid(True, alpha=0.3)
    ax.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add horizontal line at water stress threshold
    ax.axhline(y=0.1325, color='red', linestyle='--', alpha=0.7, linewidth=2, 
              label='Water Stress Threshold (0.1325)')
    
    # Add statistics text box
    total_counties = ndwi_df['County'].nunique()
    total_districts = ndwi_df['District'].nunique()
    avg_ndwi = ndwi_df['Avg_NDWI'].mean()
    min_ndwi = ndwi_df['Avg_NDWI'].min()
    max_ndwi = ndwi_df['Avg_NDWI'].max()
    
    stats_text = f'Overall Statistics:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Districts: {total_districts}\n'
    stats_text += f'Avg NDWI: {avg_ndwi:.3f}\n'
    stats_text += f'Range: {min_ndwi:.3f} - {max_ndwi:.3f}'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/NDWI_Time_Series_by_District.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_yield_ndwi_correlation_plots(ndwi_df, yield_df):
    """Create yearly scatter plots showing yield vs NDWI correlation by county"""
    print("\n📊 Creating yield vs NDWI correlation plots by year...")
    
    # Create output directory
    output_dir = 'outputs/YieldNDWITimeSeries'
    os.makedirs(output_dir, exist_ok=True)
    
    # Debug: Print data info
    print(f"   🔍 NDWI data shape: {ndwi_df.shape}")
    print(f"   🔍 Yield data shape: {yield_df.shape}")
    print(f"   🔍 NDWI columns: {list(ndwi_df.columns)}")
    print(f"   🔍 Yield columns: {list(yield_df.columns)}")
    
    # Standardize county names for merging
    def standardize_county_name(name):
        """Standardize county names to match between datasets"""
        if pd.isna(name):
            return name
        
        name = str(name).upper().strip()
        # Handle specific cases
        name = name.replace("'", "")
        name = name.replace(" ", " ")
        
        # Handle specific mappings
        county_mappings = {
            "QUEEN ANNES": "QUEEN ANNE'S",
            "ST MARYS": "ST. MARY'S", 
            "PRINCE GEORGES": "PRINCE GEORGE'S"
        }
        
        return county_mappings.get(name, name)
    
    # Apply standardization
    ndwi_df_clean = ndwi_df.copy()
    yield_df_clean = yield_df.copy()
    
    ndwi_df_clean['County_Standardized'] = ndwi_df_clean['County'].apply(standardize_county_name)
    yield_df_clean['County_Standardized'] = yield_df_clean['County'].apply(standardize_county_name)
    
    # Merge NDWI and yield data by standardized county name and year
    merged_df = pd.merge(ndwi_df_clean, yield_df_clean, 
                        left_on=['County_Standardized', 'Year'], 
                        right_on=['County_Standardized', 'Year'], 
                        how='inner')
    
    # Clean up the merged dataframe - drop standardized county columns if they exist
    columns_to_drop = [col for col in ['County_Standardized_x', 'County_Standardized_y', 'County_Standardized'] 
                       if col in merged_df.columns]
    if columns_to_drop:
        merged_df = merged_df.drop(columns_to_drop, axis=1)
    
    print(f"   🔍 Merged data shape after standardization: {merged_df.shape}")
    
    if len(merged_df) == 0:
        print("   ⚠️  No matching data found between NDWI and yield datasets!")
        print(f"   🔍 NDWI counties: {set(ndwi_df['County'])}")
        print(f"   🔍 Yield counties: {set(yield_df['County'])}")
        print(f"   🔍 NDWI years: {sorted(ndwi_df['Year'].unique())}")
        print(f"   🔍 Yield years: {sorted(yield_df['Year'].unique())}")
        return
    
    # Get unique years and sort them
    years = sorted(merged_df['Year'].unique())
    print(f"   🔍 Available years: {years}")
    
    # Calculate global axis limits for consistency
    ndwi_min = np.percentile(merged_df['Avg_NDWI'], 2) - 0.02
    ndwi_max = np.percentile(merged_df['Avg_NDWI'], 98) + 0.02
    yield_min = np.percentile(merged_df['Yield_BuAcre'], 2) - 2
    yield_max = np.percentile(merged_df['Yield_BuAcre'], 98) + 2
    
    # Round to nice numbers
    ndwi_min = np.floor(ndwi_min * 10) / 10
    ndwi_max = np.ceil(ndwi_max * 10) / 10
    yield_min = np.floor(yield_min / 5) * 5
    yield_max = np.ceil(yield_max / 5) * 5
    
    print(f"   📏 Setting consistent axis ranges:")
    print(f"      NDWI: {ndwi_min:.1f} to {ndwi_max:.1f}")
    print(f"      Yield: {yield_min:.0f} to {yield_max:.0f} Bu/Acre")
    
    # Create subplots
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()
    
    for i, year in enumerate(years):
        ax = axes[i]
        
        # Get data for this year
        year_data = merged_df[merged_df['Year'] == year]
        
        # Determine which district column to use (after merge, we might have District_x and District_y)
        district_col = 'District_x' if 'District_x' in year_data.columns else 'District'
        
        # Plot each district with different colors
        for district in sorted(year_data[district_col].unique()):
            district_data = year_data[year_data[district_col] == district]
            color = UNIVERSAL_DISTRICT_COLORS[district]
            
            # Plot individual counties as scatter points
            ax.scatter(district_data['Avg_NDWI'], district_data['Yield_BuAcre'], 
                      color=color, s=60, alpha=0.7, edgecolors='white', linewidth=0.5,
                      label=district, zorder=2)
        
        # Calculate and plot trend line for all data points in this year
        if len(year_data) > 1:
            from scipy.stats import pearsonr, linregress
            
            # Calculate correlation coefficient
            correlation, p_value = pearsonr(year_data['Avg_NDWI'], year_data['Yield_BuAcre'])
            
            # Calculate linear regression
            slope, intercept, r_value, p_value_reg, std_err = linregress(year_data['Avg_NDWI'], year_data['Yield_BuAcre'])
            
            # Create trend line
            x_trend = np.linspace(year_data['Avg_NDWI'].min(), year_data['Avg_NDWI'].max(), 100)
            y_trend = slope * x_trend + intercept
            
            # Plot trend line
            ax.plot(x_trend, y_trend, 'r--', linewidth=2, alpha=0.8, zorder=1)
            
            # Add correlation coefficient text
            ax.text(0.05, 0.95, f'r = {correlation:.3f}', transform=ax.transAxes, 
                   fontsize=12, fontweight='bold', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # Customize subplot
        ax.set_title(f'Soybean Yield vs NDWI - {year}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Average NDWI', fontsize=11)
        ax.set_ylabel('Yield (Bu/Acre)', fontsize=11)
        
        # Set consistent axis limits
        ax.set_xlim(ndwi_min, ndwi_max)
        ax.set_ylim(yield_min, yield_max)
        
        ax.grid(True, alpha=0.3)
        
        # Add legend only to the first subplot
        if i == 0:
            ax.legend(title='Agricultural District', loc='upper left', fontsize=9)
    
    # Remove empty subplots if any
    for i in range(len(years), len(axes)):
        fig.delaxes(axes[i])
    
    plt.suptitle('Soybean Yield vs NDWI Correlation by Year\n(Individual Counties)', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Yield_vs_NDWI_Correlation_by_Year.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_county_trend_lines_plot(ndwi_df, yield_df):
    """Create a plot showing individual county trend lines over time"""
    print("\n📊 Creating individual county trend lines plot...")
    
    # Create output directory
    output_dir = 'outputs/YieldNDWITimeSeries'
    os.makedirs(output_dir, exist_ok=True)
    
    # Standardize county names for merging (same function as above)
    def standardize_county_name(name):
        """Standardize county names to match between datasets"""
        if pd.isna(name):
            return name
        
        name = str(name).upper().strip()
        # Handle specific cases
        name = name.replace("'", "")
        name = name.replace(" ", " ")
        
        # Handle specific mappings
        county_mappings = {
            "QUEEN ANNES": "QUEEN ANNE'S",
            "ST MARYS": "ST. MARY'S", 
            "PRINCE GEORGES": "PRINCE GEORGE'S"
        }
        
        return county_mappings.get(name, name)
    
    # Apply standardization
    ndwi_df_clean = ndwi_df.copy()
    yield_df_clean = yield_df.copy()
    
    ndwi_df_clean['County_Standardized'] = ndwi_df_clean['County'].apply(standardize_county_name)
    yield_df_clean['County_Standardized'] = yield_df_clean['County'].apply(standardize_county_name)
    
    # Merge NDWI and yield data by standardized county name and year
    merged_df = pd.merge(ndwi_df_clean, yield_df_clean, 
                        left_on=['County_Standardized', 'Year'], 
                        right_on=['County_Standardized', 'Year'], 
                        how='inner')
    
    # Clean up the merged dataframe - drop standardized county columns if they exist
    columns_to_drop = [col for col in ['County_Standardized_x', 'County_Standardized_y', 'County_Standardized'] 
                       if col in merged_df.columns]
    if columns_to_drop:
        merged_df = merged_df.drop(columns_to_drop, axis=1)
    
    if len(merged_df) == 0:
        print("   ⚠️  No matching data found between NDWI and yield datasets!")
        return
    
    # Calculate global axis limits for consistency
    ndwi_min = np.percentile(merged_df['Avg_NDWI'], 5) - 0.05
    ndwi_max = np.percentile(merged_df['Avg_NDWI'], 95) + 0.05
    yield_min = np.percentile(merged_df['Yield_BuAcre'], 5) - 5
    yield_max = np.percentile(merged_df['Yield_BuAcre'], 95) + 5
    
    # Round to nice numbers
    ndwi_min = np.floor(ndwi_min * 10) / 10
    ndwi_max = np.ceil(ndwi_max * 10) / 10
    yield_min = np.floor(yield_min / 5) * 5
    yield_max = np.ceil(yield_max / 5) * 5
    
    print(f"   📏 Setting consistent axis ranges:")
    print(f"      NDWI: {ndwi_min:.1f} to {ndwi_max:.1f}")
    print(f"      Yield: {yield_min:.0f} to {yield_max:.0f} Bu/Acre")
    
    # Create subplots for NDWI and Yield
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Debug: Print available columns
    print(f"   🔍 Available columns: {list(merged_df.columns)}")
    
    # Determine which county column to use (after merge, we might have County_x and County_y)
    county_col = 'County_x' if 'County_x' in merged_df.columns else 'County'
    district_col = 'District_x' if 'District_x' in merged_df.columns else 'District'
    
    # Plot NDWI trend lines by county
    for county in sorted(merged_df[county_col].unique()):
        county_data = merged_df[merged_df[county_col] == county].sort_values('Year')
        district = county_data[district_col].iloc[0]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        if len(county_data) > 1:  # Only plot if we have multiple years of data
            ax1.plot(county_data['Year'], county_data['Avg_NDWI'], 
                    marker='o', linewidth=1.5, markersize=4, 
                    color=color, alpha=0.6, label=district if county == sorted(merged_df[county_col].unique())[0] else "")
    
    # Plot Yield trend lines by county
    for county in sorted(merged_df[county_col].unique()):
        county_data = merged_df[merged_df[county_col] == county].sort_values('Year')
        district = county_data[district_col].iloc[0]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        if len(county_data) > 1:  # Only plot if we have multiple years of data
            ax2.plot(county_data['Year'], county_data['Yield_BuAcre'], 
                    marker='s', linewidth=1.5, markersize=4, 
                    color=color, alpha=0.6, label=district if county == sorted(merged_df[county_col].unique())[0] else "")
    
    # Customize NDWI plot
    ax1.set_title('NDWI Trend Lines by County\n(2019-2024)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Average NDWI', fontsize=12)
    ax1.set_ylim(ndwi_min, ndwi_max)
    ax1.grid(True, alpha=0.3)
    ax1.legend(title='Agricultural District', loc='upper right')
    
    # Add horizontal line at water stress threshold
    ax1.axhline(y=0.1325, color='red', linestyle='--', alpha=0.7, linewidth=2, 
               label='Water Stress Threshold')
    
    # Customize Yield plot
    ax2.set_title('Yield Trend Lines by County\n(2019-2024)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    ax2.set_ylim(yield_min, yield_max)
    ax2.grid(True, alpha=0.3)
    ax2.legend(title='Agricultural District', loc='upper right')
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Individual_County_Trend_Lines.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_combined_yield_ndwi_correlation_plot(ndwi_df, yield_df):
    """Create a single combined plot showing yield vs NDWI correlation across all years by county"""
    print("\n📊 Creating combined yield vs NDWI correlation plot (all years)...")
    
    # Create output directory
    output_dir = 'outputs/YieldNDWITimeSeries'
    os.makedirs(output_dir, exist_ok=True)
    
    # Standardize county names for merging (same function as above)
    def standardize_county_name(name):
        """Standardize county names to match between datasets"""
        if pd.isna(name):
            return name
        
        name = str(name).upper().strip()
        # Handle specific cases
        name = name.replace("'", "")
        name = name.replace(" ", " ")
        
        # Handle specific mappings
        county_mappings = {
            "QUEEN ANNES": "QUEEN ANNE'S",
            "ST MARYS": "ST. MARY'S", 
            "PRINCE GEORGES": "PRINCE GEORGE'S"
        }
        
        return county_mappings.get(name, name)
    
    # Apply standardization
    ndwi_df_clean = ndwi_df.copy()
    yield_df_clean = yield_df.copy()
    
    ndwi_df_clean['County_Standardized'] = ndwi_df_clean['County'].apply(standardize_county_name)
    yield_df_clean['County_Standardized'] = yield_df_clean['County'].apply(standardize_county_name)
    
    # Merge NDWI and yield data by standardized county name and year
    merged_df = pd.merge(ndwi_df_clean, yield_df_clean, 
                        left_on=['County_Standardized', 'Year'], 
                        right_on=['County_Standardized', 'Year'], 
                        how='inner')
    
    # Clean up the merged dataframe - drop standardized county columns if they exist
    columns_to_drop = [col for col in ['County_Standardized_x', 'County_Standardized_y', 'County_Standardized'] 
                       if col in merged_df.columns]
    if columns_to_drop:
        merged_df = merged_df.drop(columns_to_drop, axis=1)
    
    if len(merged_df) == 0:
        print("   ⚠️  No matching data found between NDWI and yield datasets!")
        return
    
    # Calculate global axis limits for consistency
    ndwi_min = np.percentile(merged_df['Avg_NDWI'], 2) - 0.02
    ndwi_max = np.percentile(merged_df['Avg_NDWI'], 98) + 0.02
    yield_min = np.percentile(merged_df['Yield_BuAcre'], 2) - 2
    yield_max = np.percentile(merged_df['Yield_BuAcre'], 98) + 2
    
    # Round to nice numbers
    ndwi_min = np.floor(ndwi_min * 10) / 10
    ndwi_max = np.ceil(ndwi_max * 10) / 10
    yield_min = np.floor(yield_min / 5) * 5
    yield_max = np.ceil(yield_max / 5) * 5
    
    print(f"   📏 Setting axis ranges:")
    print(f"      NDWI: {ndwi_min:.1f} to {ndwi_max:.1f}")
    print(f"      Yield: {yield_min:.0f} to {yield_max:.0f} Bu/Acre")
    
    # Determine which district column to use (after merge, we might have District_x and District_y)
    district_col = 'District_x' if 'District_x' in merged_df.columns else 'District'
    county_col = 'County_x' if 'County_x' in merged_df.columns else 'County'
    
    # Create the combined plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot each district with both scatter points and individual trend lines
    from scipy.stats import pearsonr, linregress
    
    for district in sorted(merged_df[district_col].unique()):
        district_data = merged_df[merged_df[district_col] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        # Plot individual counties as scatter points
        ax.scatter(district_data['Avg_NDWI'], district_data['Yield_BuAcre'], 
                  color=color, s=60, alpha=0.7, edgecolors='white', linewidth=0.5,
                  label=district, zorder=2)
        
        # Calculate and plot individual district trend line
        if len(district_data) > 1:
            # Calculate correlation coefficient for this district
            correlation, p_value = pearsonr(district_data['Avg_NDWI'], district_data['Yield_BuAcre'])
            
            # Calculate linear regression for this district
            slope, intercept, r_value, p_value_reg, std_err = linregress(district_data['Avg_NDWI'], district_data['Yield_BuAcre'])
            
            # Create trend line for this district
            x_trend = np.linspace(district_data['Avg_NDWI'].min(), district_data['Avg_NDWI'].max(), 100)
            y_trend = slope * x_trend + intercept
            
            # Plot district trend line
            ax.plot(x_trend, y_trend, color=color, linewidth=2, alpha=0.8, zorder=1, 
                   linestyle='--', label=f'{district} (r = {correlation:.3f})')
    
    # Customize the plot
    ax.set_title('Soybean Yield vs NDWI Correlation by Agricultural District\n(All Years Combined - Individual Counties with District Trend Lines)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Average NDWI', fontsize=12)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    
    # Set consistent axis limits
    ax.set_xlim(ndwi_min, ndwi_max)
    ax.set_ylim(yield_min, yield_max)
    
    ax.grid(True, alpha=0.3)
    
    # Position legend on the right side to avoid overlap with statistics
    ax.legend(title='Agricultural District', loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=10)
    
    # Add statistics text box on the right side
    total_counties = merged_df[county_col].nunique()
    total_districts = merged_df[district_col].nunique()
    total_years = merged_df['Year'].nunique()
    avg_ndwi = merged_df['Avg_NDWI'].mean()
    avg_yield = merged_df['Yield_BuAcre'].mean()
    
    stats_text = f'Overall Statistics:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Districts: {total_districts}\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Data Points: {len(merged_df)}\n'
    stats_text += f'Avg NDWI: {avg_ndwi:.3f}\n'
    stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre'
    
    # Position statistics box on the right side to avoid overlap
    ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Combined_Yield_vs_NDWI_Correlation_All_Years.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_combined_yield_ndwi_correlation_with_overall_trend(ndwi_df, yield_df):
    """Create a copy of the combined plot but with an overall average trend line in dark red"""
    print("\n📊 Creating combined yield vs NDWI correlation plot with overall trend line...")
    
    # Create output directory
    output_dir = 'outputs/YieldNDWITimeSeries'
    os.makedirs(output_dir, exist_ok=True)
    
    # Standardize county names for merging (same function as above)
    def standardize_county_name(name):
        """Standardize county names to match between datasets"""
        if pd.isna(name):
            return name
        
        name = str(name).upper().strip()
        # Handle specific cases
        name = name.replace("'", "")
        name = name.replace(" ", " ")
        
        # Handle specific mappings
        county_mappings = {
            "QUEEN ANNES": "QUEEN ANNE'S",
            "ST MARYS": "ST. MARY'S", 
            "PRINCE GEORGES": "PRINCE GEORGE'S"
        }
        
        return county_mappings.get(name, name)
    
    # Apply standardization
    ndwi_df_clean = ndwi_df.copy()
    yield_df_clean = yield_df.copy()
    
    ndwi_df_clean['County_Standardized'] = ndwi_df_clean['County'].apply(standardize_county_name)
    yield_df_clean['County_Standardized'] = yield_df_clean['County'].apply(standardize_county_name)
    
    # Merge NDWI and yield data by standardized county name and year
    merged_df = pd.merge(ndwi_df_clean, yield_df_clean, 
                        left_on=['County_Standardized', 'Year'], 
                        right_on=['County_Standardized', 'Year'], 
                        how='inner')
    
    # Clean up the merged dataframe - drop standardized county columns if they exist
    columns_to_drop = [col for col in ['County_Standardized_x', 'County_Standardized_y', 'County_Standardized'] 
                       if col in merged_df.columns]
    if columns_to_drop:
        merged_df = merged_df.drop(columns_to_drop, axis=1)
    
    if len(merged_df) == 0:
        print("   ⚠️  No matching data found between NDWI and yield datasets!")
        return
    
    # Calculate global axis limits for consistency
    ndwi_min = np.percentile(merged_df['Avg_NDWI'], 2) - 0.02
    ndwi_max = np.percentile(merged_df['Avg_NDWI'], 98) + 0.02
    yield_min = np.percentile(merged_df['Yield_BuAcre'], 2) - 2
    yield_max = np.percentile(merged_df['Yield_BuAcre'], 98) + 2
    
    # Round to nice numbers
    ndwi_min = np.floor(ndwi_min * 10) / 10
    ndwi_max = np.ceil(ndwi_max * 10) / 10
    yield_min = np.floor(yield_min / 5) * 5
    yield_max = np.ceil(yield_max / 5) * 5
    
    print(f"   📏 Setting axis ranges:")
    print(f"      NDWI: {ndwi_min:.1f} to {ndwi_max:.1f}")
    print(f"      Yield: {yield_min:.0f} to {yield_max:.0f} Bu/Acre")
    
    # Determine which district column to use (after merge, we might have District_x and District_y)
    district_col = 'District_x' if 'District_x' in merged_df.columns else 'District'
    county_col = 'County_x' if 'County_x' in merged_df.columns else 'County'
    
    # Create the combined plot
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot each district with both scatter points and individual trend lines
    from scipy.stats import pearsonr, linregress
    
    for district in sorted(merged_df[district_col].unique()):
        district_data = merged_df[merged_df[district_col] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        # Plot individual counties as scatter points
        ax.scatter(district_data['Avg_NDWI'], district_data['Yield_BuAcre'], 
                  color=color, s=60, alpha=0.7, edgecolors='white', linewidth=0.5,
                  label=district, zorder=2)
        
        # Calculate and plot individual district trend line
        if len(district_data) > 1:
            # Calculate correlation coefficient for this district
            correlation, p_value = pearsonr(district_data['Avg_NDWI'], district_data['Yield_BuAcre'])
            
            # Calculate linear regression for this district
            slope, intercept, r_value, p_value_reg, std_err = linregress(district_data['Avg_NDWI'], district_data['Yield_BuAcre'])
            
            # Create trend line for this district
            x_trend = np.linspace(district_data['Avg_NDWI'].min(), district_data['Avg_NDWI'].max(), 100)
            y_trend = slope * x_trend + intercept
            
            # Plot district trend line
            ax.plot(x_trend, y_trend, color=color, linewidth=2, alpha=0.8, zorder=1, 
                   linestyle='--', label=f'{district} (r = {correlation:.3f})')
    
    # Calculate and plot overall trend line for all data points in dark red
    if len(merged_df) > 1:
        # Calculate overall correlation coefficient
        overall_correlation, p_value = pearsonr(merged_df['Avg_NDWI'], merged_df['Yield_BuAcre'])
        
        # Calculate overall linear regression
        slope, intercept, r_value, p_value_reg, std_err = linregress(merged_df['Avg_NDWI'], merged_df['Yield_BuAcre'])
        
        # Create overall trend line
        x_trend = np.linspace(merged_df['Avg_NDWI'].min(), merged_df['Avg_NDWI'].max(), 100)
        y_trend = slope * x_trend + intercept
        
        # Plot overall trend line in dark red
        ax.plot(x_trend, y_trend, color='darkred', linewidth=4, alpha=0.9, zorder=3, 
               linestyle='-', label=f'Overall Trend (r = {overall_correlation:.3f})')
    
    # Customize the plot
    ax.set_title('Soybean Yield vs NDWI Correlation by Agricultural District\n(All Years Combined - Individual Counties with District & Overall Trend Lines)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Average NDWI', fontsize=12)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    
    # Set consistent axis limits
    ax.set_xlim(ndwi_min, ndwi_max)
    ax.set_ylim(yield_min, yield_max)
    
    ax.grid(True, alpha=0.3)
    
    # Position legend on the left side to avoid overlap with statistics
    ax.legend(title='Agricultural District', loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=10)
    
    # Add statistics text box on the right side
    total_counties = merged_df[county_col].nunique()
    total_districts = merged_df[district_col].nunique()
    total_years = merged_df['Year'].nunique()
    avg_ndwi = merged_df['Avg_NDWI'].mean()
    avg_yield = merged_df['Yield_BuAcre'].mean()
    
    stats_text = f'Overall Statistics:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Districts: {total_districts}\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Data Points: {len(merged_df)}\n'
    stats_text += f'Avg NDWI: {avg_ndwi:.3f}\n'
    stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre'
    
    # Position statistics box on the right side to avoid overlap
    ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Combined_Yield_vs_NDWI_Correlation_with_Overall_Trend.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def print_summary_statistics(ndwi_df, yield_df):
    """Print summary statistics for the time series analysis"""
    print("\n📊 YIELD vs NDWI TIME SERIES ANALYSIS SUMMARY")
    print("=" * 60)
    
    # NDWI statistics
    print(f"\n📈 NDWI Statistics:")
    print(f"   Total records: {len(ndwi_df):,}")
    print(f"   Counties: {ndwi_df['County'].nunique()}")
    print(f"   Districts: {ndwi_df['District'].nunique()}")
    print(f"   Years: {ndwi_df['Year'].nunique()} ({min(ndwi_df['Year'])}-{max(ndwi_df['Year'])})")
    
    # Yield statistics
    print(f"\n📈 Yield Statistics:")
    print(f"   Total records: {len(yield_df):,}")
    print(f"   Counties: {yield_df['County'].nunique()}")
    print(f"   Districts: {yield_df['District'].nunique()}")
    print(f"   Years: {yield_df['Year'].nunique()} ({min(yield_df['Year'])}-{max(yield_df['Year'])})")
    
    # District averages
    print(f"\n🏛️  District NDWI Averages:")
    district_ndwi_avg = ndwi_df.groupby('District')['Avg_NDWI'].agg(['mean', 'std', 'count']).round(3)
    district_ndwi_avg = district_ndwi_avg.sort_values('mean', ascending=False)
    
    for district, row in district_ndwi_avg.iterrows():
        print(f"   {district:<25}: {row['mean']:>6.3f} ± {row['std']:>5.3f} (n={row['count']:>3})")
    
    print(f"\n🏛️  District Yield Averages:")
    district_yield_avg = yield_df.groupby('District')['Yield_BuAcre'].agg(['mean', 'std', 'count']).round(1)
    district_yield_avg = district_yield_avg.sort_values('mean', ascending=False)
    
    for district, row in district_yield_avg.iterrows():
        print(f"   {district:<25}: {row['mean']:>6.1f} ± {row['std']:>5.1f} Bu/Acre (n={row['count']:>3})")
    
    # Year-over-year trends
    print(f"\n📅 Year-over-Year Trends:")
    yearly_ndwi_avg = ndwi_df.groupby('Year')['Avg_NDWI'].mean().round(3)
    yearly_yield_avg = yield_df.groupby('Year')['Yield_BuAcre'].mean().round(1)
    
    for year in sorted(yearly_ndwi_avg.index):
        ndwi_val = yearly_ndwi_avg[year]
        yield_val = yearly_yield_avg[year]
        print(f"   {year}: NDWI={ndwi_val:>6.3f}, Yield={yield_val:>6.1f} Bu/Acre")

def main():
    """Main function to run the yield vs NDWI time series analysis"""
    print("🌱 YIELD vs NDWI TIME SERIES ANALYSIS")
    print("=" * 60)
    
    # Load data
    ndwi_df, nass_df = load_and_prepare_data()
    
    # Extract yearly data
    ndwi_yearly_df, yield_yearly_df = extract_yearly_data(ndwi_df, nass_df)
    
    # Create time series plots
    create_yield_time_series_plots(yield_yearly_df)
    create_ndwi_time_series_plots(ndwi_yearly_df)
    
    # Create new correlation and trend line plots
    create_yield_ndwi_correlation_plots(ndwi_yearly_df, yield_yearly_df)
    create_county_trend_lines_plot(ndwi_yearly_df, yield_yearly_df)
    create_combined_yield_ndwi_correlation_plot(ndwi_yearly_df, yield_yearly_df)
    create_combined_yield_ndwi_correlation_with_overall_trend(ndwi_yearly_df, yield_yearly_df)
    
    # Print summary statistics
    print_summary_statistics(ndwi_yearly_df, yield_yearly_df)
    
    print(f"\n✅ Yield vs NDWI time series analysis completed!")
    print(f"📁 Output directory: outputs/YieldNDWITimeSeries/")

if __name__ == "__main__":
    main()