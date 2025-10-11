#!/usr/bin/env python3
"""
NDWI vs Water Statistics Correlation Analysis

This script analyzes the correlation between NDWI and drought (PDSI) data,
as well as NDWI and precipitation data, by month and agricultural district.

Author: Analysis for Maryland Soybean Stress Project
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
import os
from scipy import stats
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

# Growing season months
GROWING_SEASON_MONTHS = ['April', 'May', 'June', 'July', 'August', 'September', 'October']

def load_and_prepare_data():
    """Load and prepare NDWI, PDSI, and precipitation data"""
    print("🔄 Loading water statistics data...")
    
    try:
        # Load NDWI data
        ndwi_df = pd.read_csv('data/maryland_ndwi_10day_final_imputed.csv', index_col='NAME')
        print(f"   ✅ NDWI data loaded: {ndwi_df.shape}")
        
        # Load PDSI data
        pdsi_df = pd.read_csv('data/maryland_pdsi_combined_wide.csv', index_col='County')
        print(f"   ✅ PDSI data loaded: {pdsi_df.shape}")
        
        # Load precipitation data
        precip_df = pd.read_csv('data/maryland_precipitation_combined_wide.csv', index_col='County')
        print(f"   ✅ Precipitation data loaded: {precip_df.shape}")
        
        return ndwi_df, pdsi_df, precip_df
    except Exception as e:
        print(f"   ❌ Error loading data: {e}")
        raise

def extract_monthly_ndwi_data(ndwi_df):
    """Extract and organize NDWI data by month and agricultural district"""
    print("📊 Extracting monthly NDWI data...")
    
    monthly_data = []
    
    for county in ndwi_df.index:
        district = ndwi_df.loc[county, 'Ag_District']
        
        for year in [2019, 2020, 2021, 2022, 2023, 2024]:
            for month in GROWING_SEASON_MONTHS:
                # Find columns for this month and year
                month_cols = [col for col in ndwi_df.columns 
                             if col.startswith(f'NDWI_{month}_') and str(year) in col]
                
                if month_cols:
                    # Get NDWI values for this county-month-year
                    ndwi_values = []
                    for col in month_cols:
                        value = ndwi_df.loc[county, col]
                        if pd.notna(value) and value != 0:
                            ndwi_values.append(value)
                    
                    if ndwi_values:
                        avg_ndwi = np.mean(ndwi_values)
                        
                        monthly_data.append({
                            'County': county,
                            'District': district,
                            'Year': year,
                            'Month': month,
                            'Avg_NDWI': avg_ndwi
                        })
    
    ndwi_monthly_df = pd.DataFrame(monthly_data)
    print(f"   ✅ NDWI monthly data extracted: {len(ndwi_monthly_df)} records")
    return ndwi_monthly_df

def extract_monthly_pdsi_data(pdsi_df):
    """Extract and organize PDSI data by month"""
    print("📊 Extracting monthly PDSI data...")
    
    pdsi_data = []
    
    for county in pdsi_df.index:
        for year in [2019, 2020, 2021, 2022, 2023, 2024]:
            for month in GROWING_SEASON_MONTHS:
                # Find PDSI column for this month and year
                month_num = GROWING_SEASON_MONTHS.index(month) + 4  # April=4, May=5, etc.
                col_name = f'PDSI_{year}-{month_num:02d}'
                
                if col_name in pdsi_df.columns:
                    pdsi_value = pdsi_df.loc[county, col_name]
                    if pd.notna(pdsi_value):
                        pdsi_data.append({
                            'County': county,
                            'Year': year,
                            'Month': month,
                            'PDSI': pdsi_value
                        })
    
    pdsi_monthly_df = pd.DataFrame(pdsi_data)
    print(f"   ✅ PDSI monthly data extracted: {len(pdsi_monthly_df)} records")
    return pdsi_monthly_df

def extract_monthly_precipitation_data(precip_df):
    """Extract and organize precipitation data by month"""
    print("📊 Extracting monthly precipitation data...")
    
    precip_data = []
    
    for county in precip_df.index:
        for year in [2019, 2020, 2021, 2022, 2023, 2024]:
            for month in GROWING_SEASON_MONTHS:
                # Find precipitation column for this month and year
                month_num = GROWING_SEASON_MONTHS.index(month) + 4  # April=4, May=5, etc.
                col_name = f'Precip_{year}-{month_num:02d}'
                
                if col_name in precip_df.columns:
                    precip_value = precip_df.loc[county, col_name]
                    if pd.notna(precip_value):
                        precip_data.append({
                            'County': county,
                            'Year': year,
                            'Month': month,
                            'Precipitation': precip_value
                        })
    
    precip_monthly_df = pd.DataFrame(precip_data)
    print(f"   ✅ Precipitation monthly data extracted: {len(precip_monthly_df)} records")
    return precip_monthly_df

def merge_data(ndwi_df, pdsi_df, precip_df):
    """Merge NDWI, PDSI, and precipitation data"""
    print("🔗 Merging data...")
    
    # Merge NDWI with PDSI
    merged_df = pd.merge(ndwi_df, pdsi_df, 
                        on=['County', 'Year', 'Month'], 
                        how='inner')
    
    # Merge with precipitation
    merged_df = pd.merge(merged_df, precip_df, 
                        on=['County', 'Year', 'Month'], 
                        how='inner')
    
    print(f"   ✅ Merged data: {len(merged_df)} records")
    print(f"   📍 Counties: {merged_df['County'].nunique()}")
    print(f"   🏛️  Districts: {merged_df['District'].nunique()}")
    print(f"   📅 Years: {sorted(merged_df['Year'].unique())}")
    print(f"   📆 Months: {sorted(merged_df['Month'].unique())}")
    
    return merged_df

def create_pdsi_correlation_plots(merged_df):
    """Create plots showing correlation between NDWI and PDSI by month"""
    print("\n📊 Creating PDSI correlation plots...")
    
    # Create output directory
    output_dir = 'outputs/NDWIWaterStatistics'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate global axis limits for consistency
    ndwi_min = np.percentile(merged_df['Avg_NDWI'], 5) - 0.05
    ndwi_max = np.percentile(merged_df['Avg_NDWI'], 95) + 0.05
    ndwi_min = np.floor(ndwi_min * 10) / 10
    ndwi_max = np.ceil(ndwi_max * 10) / 10
    
    pdsi_min = np.percentile(merged_df['PDSI'], 5) - 0.5
    pdsi_max = np.percentile(merged_df['PDSI'], 95) + 0.5
    pdsi_min = np.floor(pdsi_min)
    pdsi_max = np.ceil(pdsi_max)
    
    print(f"   📏 Setting consistent axes - NDWI: {ndwi_min:.1f} to {ndwi_max:.1f}, PDSI: {pdsi_min:.0f} to {pdsi_max:.0f}")
    
    for month in GROWING_SEASON_MONTHS:
        print(f"   📈 Creating PDSI correlation plot for {month}...")
        
        # Filter data for this month
        month_data = merged_df[merged_df['Month'] == month].copy()
        
        if len(month_data) == 0:
            print(f"   ⚠️  No data found for {month}")
            continue
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Plot data for each district
        correlations = []
        
        for district in sorted(month_data['District'].unique()):
            district_data = month_data[month_data['District'] == district]
            color = UNIVERSAL_DISTRICT_COLORS[district]
            
            # Calculate correlation
            correlation = np.corrcoef(district_data['PDSI'], district_data['Avg_NDWI'])[0,1]
            correlations.append({'District': district, 'Correlation': correlation, 'Count': len(district_data)})
            
            # Plot scatter points
            ax.scatter(district_data['PDSI'], district_data['Avg_NDWI'], 
                      color=color, label=f'{district} (r={correlation:.3f}, n={len(district_data)})', 
                      alpha=0.7, s=60, edgecolors='white', linewidth=0.5)
            
            # Add trend line
            if len(district_data) > 2:
                z = np.polyfit(district_data['PDSI'], district_data['Avg_NDWI'], 1)
                p = np.poly1d(z)
                x_trend = np.linspace(district_data['PDSI'].min(), district_data['PDSI'].max(), 100)
                ax.plot(x_trend, p(x_trend), color=color, linestyle='--', alpha=0.8, linewidth=2)
        
        # Customize the plot
        ax.set_title(f'NDWI vs PDSI Correlation in {month}\nby Agricultural District (2019-2024)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('PDSI (Palmer Drought Severity Index)', fontsize=12)
        ax.set_ylabel('NDWI (Normalized Difference Water Index)', fontsize=12)
        ax.set_xlim(pdsi_min, pdsi_max)  # Set consistent X-axis limits
        ax.set_ylim(ndwi_min, ndwi_max)  # Set consistent Y-axis limits
        ax.grid(True, alpha=0.3)
        ax.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Add horizontal line at water stress threshold
        ax.axhline(y=0.1325, color='red', linestyle='--', alpha=0.7, linewidth=2, 
                  label='Water Stress Threshold (0.1325)')
        
        # Add vertical line at normal PDSI
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5, linewidth=1, 
                  label='Normal PDSI (0)')
        
        # Add statistics text box
        total_counties = month_data['County'].nunique()
        total_districts = month_data['District'].nunique()
        overall_corr = np.corrcoef(month_data['PDSI'], month_data['Avg_NDWI'])[0,1]
        
        stats_text = f'Statistics for {month}:\n'
        stats_text += f'Counties: {total_counties}\n'
        stats_text += f'Districts: {total_districts}\n'
        stats_text += f'Overall r: {overall_corr:.3f}\n'
        stats_text += f'Records: {len(month_data)}'
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=10)
        
        plt.tight_layout()
        
        # Save the plot
        filename = f'{output_dir}/{month}_NDWI_vs_PDSI_Correlation.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved: {filename}")
        
        plt.show()
        plt.close()

def create_precipitation_correlation_plots(merged_df):
    """Create plots showing correlation between NDWI and precipitation by month"""
    print("\n📊 Creating precipitation correlation plots...")
    
    # Create output directory
    output_dir = 'outputs/NDWIWaterStatistics'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate global axis limits for consistency
    ndwi_min = np.percentile(merged_df['Avg_NDWI'], 5) - 0.05
    ndwi_max = np.percentile(merged_df['Avg_NDWI'], 95) + 0.05
    ndwi_min = np.floor(ndwi_min * 10) / 10
    ndwi_max = np.ceil(ndwi_max * 10) / 10
    
    precip_min = np.percentile(merged_df['Precipitation'], 5) - 0.5
    precip_max = np.percentile(merged_df['Precipitation'], 95) + 0.5
    precip_min = np.floor(precip_min * 2) / 2  # Round to nearest 0.5
    precip_max = np.ceil(precip_max * 2) / 2
    
    print(f"   📏 Setting consistent axes - NDWI: {ndwi_min:.1f} to {ndwi_max:.1f}, Precipitation: {precip_min:.1f} to {precip_max:.1f}")
    
    for month in GROWING_SEASON_MONTHS:
        print(f"   📈 Creating precipitation correlation plot for {month}...")
        
        # Filter data for this month
        month_data = merged_df[merged_df['Month'] == month].copy()
        
        if len(month_data) == 0:
            print(f"   ⚠️  No data found for {month}")
            continue
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Plot data for each district
        correlations = []
        
        for district in sorted(month_data['District'].unique()):
            district_data = month_data[month_data['District'] == district]
            color = UNIVERSAL_DISTRICT_COLORS[district]
            
            # Calculate correlation
            correlation = np.corrcoef(district_data['Precipitation'], district_data['Avg_NDWI'])[0,1]
            correlations.append({'District': district, 'Correlation': correlation, 'Count': len(district_data)})
            
            # Plot scatter points
            ax.scatter(district_data['Precipitation'], district_data['Avg_NDWI'], 
                      color=color, label=f'{district} (r={correlation:.3f}, n={len(district_data)})', 
                      alpha=0.7, s=60, edgecolors='white', linewidth=0.5)
            
            # Add trend line
            if len(district_data) > 2:
                z = np.polyfit(district_data['Precipitation'], district_data['Avg_NDWI'], 1)
                p = np.poly1d(z)
                x_trend = np.linspace(district_data['Precipitation'].min(), district_data['Precipitation'].max(), 100)
                ax.plot(x_trend, p(x_trend), color=color, linestyle='--', alpha=0.8, linewidth=2)
        
        # Customize the plot
        ax.set_title(f'NDWI vs Precipitation Correlation in {month}\nby Agricultural District (2019-2024)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Precipitation (inches)', fontsize=12)
        ax.set_ylabel('NDWI (Normalized Difference Water Index)', fontsize=12)
        ax.set_xlim(precip_min, precip_max)  # Set consistent X-axis limits
        ax.set_ylim(ndwi_min, ndwi_max)  # Set consistent Y-axis limits
        ax.grid(True, alpha=0.3)
        ax.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Add horizontal line at water stress threshold
        ax.axhline(y=0.1325, color='red', linestyle='--', alpha=0.7, linewidth=2, 
                  label='Water Stress Threshold (0.1325)')
        
        # Add statistics text box
        total_counties = month_data['County'].nunique()
        total_districts = month_data['District'].nunique()
        overall_corr = np.corrcoef(month_data['Precipitation'], month_data['Avg_NDWI'])[0,1]
        avg_precip = month_data['Precipitation'].mean()
        
        stats_text = f'Statistics for {month}:\n'
        stats_text += f'Counties: {total_counties}\n'
        stats_text += f'Districts: {total_districts}\n'
        stats_text += f'Overall r: {overall_corr:.3f}\n'
        stats_text += f'Avg Precip: {avg_precip:.1f} in\n'
        stats_text += f'Records: {len(month_data)}'
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=10)
        
        plt.tight_layout()
        
        # Save the plot
        filename = f'{output_dir}/{month}_NDWI_vs_Precipitation_Correlation.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved: {filename}")
        
        plt.show()
        plt.close()

def create_comprehensive_correlation_plot(merged_df):
    """Create comprehensive plots showing all correlations"""
    print("\n📊 Creating comprehensive correlation plots...")
    
    output_dir = 'outputs/NDWIWaterStatistics'
    
    # Calculate monthly correlations
    monthly_correlations = []
    
    for month in GROWING_SEASON_MONTHS:
        month_data = merged_df[merged_df['Month'] == month]
        
        if len(month_data) > 2:
            pdsi_corr = np.corrcoef(month_data['PDSI'], month_data['Avg_NDWI'])[0,1]
            precip_corr = np.corrcoef(month_data['Precipitation'], month_data['Avg_NDWI'])[0,1]
            
            monthly_correlations.append({
                'Month': month,
                'PDSI_Correlation': pdsi_corr,
                'Precipitation_Correlation': precip_corr,
                'Records': len(month_data)
            })
    
    corr_df = pd.DataFrame(monthly_correlations)
    
    # Create comprehensive correlation plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12))
    
    # PDSI correlations over time
    ax1.plot(corr_df['Month'], corr_df['PDSI_Correlation'], 
             marker='o', linewidth=3, markersize=8, color='red', alpha=0.8)
    ax1.set_title('NDWI vs PDSI Correlation Throughout Growing Season\n(2019-2024)', 
                 fontsize=16, fontweight='bold')
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Correlation Coefficient (r)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    # Add correlation values on points
    for i, (month, corr) in enumerate(zip(corr_df['Month'], corr_df['PDSI_Correlation'])):
        ax1.text(i, corr + 0.02, f'{corr:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # Precipitation correlations over time
    ax2.plot(corr_df['Month'], corr_df['Precipitation_Correlation'], 
             marker='o', linewidth=3, markersize=8, color='blue', alpha=0.8)
    ax2.set_title('NDWI vs Precipitation Correlation Throughout Growing Season\n(2019-2024)', 
                 fontsize=16, fontweight='bold')
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Correlation Coefficient (r)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    # Add correlation values on points
    for i, (month, corr) in enumerate(zip(corr_df['Month'], corr_df['Precipitation_Correlation'])):
        ax2.text(i, corr + 0.02, f'{corr:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Comprehensive_Correlations_Overview.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def print_summary_statistics(merged_df):
    """Print summary statistics for the correlation analysis"""
    print("\n📊 NDWI vs WATER STATISTICS CORRELATION ANALYSIS SUMMARY")
    print("=" * 70)
    
    # Overall statistics
    print(f"\n📈 Overall Statistics:")
    print(f"   Total records: {len(merged_df):,}")
    print(f"   Counties: {merged_df['County'].nunique()}")
    print(f"   Districts: {merged_df['District'].nunique()}")
    print(f"   Years: {merged_df['Year'].nunique()} ({min(merged_df['Year'])}-{max(merged_df['Year'])})")
    print(f"   Months: {merged_df['Month'].nunique()}")
    
    # Overall correlations
    overall_pdsi_corr = np.corrcoef(merged_df['PDSI'], merged_df['Avg_NDWI'])[0,1]
    overall_precip_corr = np.corrcoef(merged_df['Precipitation'], merged_df['Avg_NDWI'])[0,1]
    
    print(f"\n🔗 Overall Correlations:")
    print(f"   NDWI vs PDSI: {overall_pdsi_corr:.3f}")
    print(f"   NDWI vs Precipitation: {overall_precip_corr:.3f}")
    
    # Monthly correlations
    print(f"\n📅 Monthly Correlations:")
    for month in GROWING_SEASON_MONTHS:
        month_data = merged_df[merged_df['Month'] == month]
        if len(month_data) > 2:
            pdsi_corr = np.corrcoef(month_data['PDSI'], month_data['Avg_NDWI'])[0,1]
            precip_corr = np.corrcoef(month_data['Precipitation'], month_data['Avg_NDWI'])[0,1]
            print(f"   {month:<12}: PDSI r={pdsi_corr:>6.3f}, Precip r={precip_corr:>6.3f} (n={len(month_data):>3})")
    
    # District correlations
    print(f"\n🏛️  District Correlations:")
    for district in sorted(merged_df['District'].unique()):
        district_data = merged_df[merged_df['District'] == district]
        if len(district_data) > 2:
            pdsi_corr = np.corrcoef(district_data['PDSI'], district_data['Avg_NDWI'])[0,1]
            precip_corr = np.corrcoef(district_data['Precipitation'], district_data['Avg_NDWI'])[0,1]
            print(f"   {district:<25}: PDSI r={pdsi_corr:>6.3f}, Precip r={precip_corr:>6.3f} (n={len(district_data):>3})")

def create_pdsi_by_year_plot(pdsi_df):
    """Create a plot showing PDSI by year to identify wet and drought years"""
    print("\n📊 Creating PDSI by year plot...")
    
    # Create output directory
    output_dir = 'outputs/DroughtIndices'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate yearly averages for PDSI
    yearly_pdsi = pdsi_df.groupby('Year')['PDSI'].agg(['mean', 'std', 'count']).reset_index()
    yearly_pdsi = yearly_pdsi.round(3)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Define drought condition colors
    condition_colors = {
        'Extremely Dry (PDSI<-2.0)': '#8B0000',      # Dark Red
        'Severely Dry (PDSI -2.0 to -1.1)': '#DC143C', # Crimson
        'Moderately Dry (PDSI -1.0 to -0.5)': '#FF6347', # Tomato
        'Near Normal (PDSI -0.5-0.5)': '#32CD32',     # Lime Green
        'Moderately Wet (PDSI 0.5-0.9)': '#1E90FF',   # Dodger Blue
        'Very Wet (PDSI 1.0-1.9)': '#4169E1',         # Royal Blue
        'Extremely Wet (PDSI≥2.0)': '#000080'         # Navy
    }
    
    # Classify each year's average PDSI
    def classify_drought_condition(pdsi_value):
        if pd.isna(pdsi_value):
            return 'Unknown'
        elif pdsi_value >= 2.0:
            return 'Extremely Wet (PDSI≥2.0)'
        elif pdsi_value >= 1.0:
            return 'Very Wet (PDSI 1.0-1.9)'
        elif pdsi_value >= 0.5:
            return 'Moderately Wet (PDSI 0.5-0.9)'
        elif pdsi_value >= -0.5:
            return 'Near Normal (PDSI -0.5-0.5)'
        elif pdsi_value >= -1.0:
            return 'Moderately Dry (PDSI -1.0 to -0.5)'
        elif pdsi_value >= -2.0:
            return 'Severely Dry (PDSI -2.0 to -1.1)'
        else:
            return 'Extremely Dry (PDSI<-2.0)'
    
    # Classify each year
    yearly_pdsi['Drought_Condition'] = yearly_pdsi['mean'].apply(classify_drought_condition)
    yearly_pdsi['Color'] = yearly_pdsi['Drought_Condition'].map(condition_colors)
    
    # Create bar plot
    bars = ax.bar(yearly_pdsi['Year'], yearly_pdsi['mean'], 
                  color=yearly_pdsi['Color'], alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Add error bars
    ax.errorbar(yearly_pdsi['Year'], yearly_pdsi['mean'], 
                yerr=yearly_pdsi['std'], fmt='none', color='black', capsize=3)
    
    # Add horizontal reference lines
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
    ax.axhline(y=2.0, color='blue', linestyle='--', alpha=0.5, label='Extremely Wet')
    ax.axhline(y=1.0, color='lightblue', linestyle='--', alpha=0.5, label='Very Wet')
    ax.axhline(y=0.5, color='lightgreen', linestyle='--', alpha=0.5, label='Moderately Wet')
    ax.axhline(y=-0.5, color='yellow', linestyle='--', alpha=0.5, label='Moderately Dry')
    ax.axhline(y=-1.0, color='orange', linestyle='--', alpha=0.5, label='Severely Dry')
    ax.axhline(y=-2.0, color='red', linestyle='--', alpha=0.5, label='Extremely Dry')
    
    # Customize the plot
    ax.set_title('PDSI by Year - Maryland Agricultural Districts\n(Wet Years vs Drought Years)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Average PDSI (Palmer Drought Severity Index)', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (year, pdsi_mean, condition) in enumerate(zip(yearly_pdsi['Year'], yearly_pdsi['mean'], yearly_pdsi['Drought_Condition'])):
        ax.text(year, pdsi_mean + (0.1 if pdsi_mean >= 0 else -0.1), 
                f'{pdsi_mean:.2f}\n{condition.split("(")[0].strip()}', 
                ha='center', va='bottom' if pdsi_mean >= 0 else 'top', 
                fontsize=9, fontweight='bold')
    
    # Create legend for drought conditions
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.8, label=condition) 
                      for condition, color in condition_colors.items()]
    ax.legend(handles=legend_elements, title='Drought Conditions', 
             bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add statistics text
    total_years = len(yearly_pdsi)
    avg_pdsi = yearly_pdsi['mean'].mean()
    driest_year = yearly_pdsi.loc[yearly_pdsi['mean'].idxmin()]
    wettest_year = yearly_pdsi.loc[yearly_pdsi['mean'].idxmax()]
    
    stats_text = f'Statistics:\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Avg PDSI: {avg_pdsi:.2f}\n'
    stats_text += f'Driest: {driest_year["Year"]} ({driest_year["mean"]:.2f})\n'
    stats_text += f'Wettest: {wettest_year["Year"]} ({wettest_year["mean"]:.2f})'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/PDSI_by_Year_Wet_Drought_Years.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_county_pdsi_analysis(pdsi_df):
    """Create a plot showing per-county PDSI analysis to identify drought-prone areas"""
    print("\n📊 Creating per-county PDSI analysis...")
    
    # Create output directory
    output_dir = 'outputs/DroughtIndices'
    os.makedirs(output_dir, exist_ok=True)
    
    # First, we need to add district information to PDSI data
    # Load the NDWI data to get district information
    ndwi_df = pd.read_csv('data/maryland_ndwi_10day_final_imputed.csv', index_col='NAME')
    
    # Create a mapping from county to district
    county_to_district = ndwi_df[['Ag_District']].to_dict()['Ag_District']
    
    # Add district information to PDSI data
    pdsi_df_with_district = pdsi_df.copy()
    pdsi_df_with_district['District'] = pdsi_df_with_district['County'].map(county_to_district)
    
    # Remove rows where district mapping failed
    pdsi_df_with_district = pdsi_df_with_district.dropna(subset=['District'])
    
    # Calculate county-level PDSI statistics with district information
    county_pdsi = pdsi_df_with_district.groupby(['County', 'District']).agg({
        'PDSI': ['mean', 'std', 'min', 'max', 'count']
    }).round(3)
    
    # Flatten column names
    county_pdsi.columns = ['Avg_PDSI', 'Std_PDSI', 'Min_PDSI', 'Max_PDSI', 'Data_Points']
    county_pdsi = county_pdsi.reset_index()
    
    # Sort by district first, then by average PDSI within each district
    county_pdsi = county_pdsi.sort_values(['District', 'Avg_PDSI'])
    
    # Create a combined label for counties showing both county and district
    county_pdsi['County_District_Label'] = county_pdsi['County'] + '\n(' + county_pdsi['District'] + ')'
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Define drought condition colors
    condition_colors = {
        'Extremely Dry': '#8B0000',      # Dark Red
        'Severely Dry': '#DC143C',       # Crimson
        'Moderately Dry': '#FF6347',     # Tomato
        'Near Normal': '#32CD32',        # Lime Green
        'Moderately Wet': '#1E90FF',     # Dodger Blue
        'Very Wet': '#4169E1',           # Royal Blue
        'Extremely Wet': '#000080'       # Navy
    }
    
    # Classify counties by average PDSI
    def classify_county_condition(pdsi_value):
        if pd.isna(pdsi_value):
            return 'Unknown'
        elif pdsi_value >= 2.0:
            return 'Extremely Wet'
        elif pdsi_value >= 1.0:
            return 'Very Wet'
        elif pdsi_value >= 0.5:
            return 'Moderately Wet'
        elif pdsi_value >= -0.5:
            return 'Near Normal'
        elif pdsi_value >= -1.0:
            return 'Moderately Dry'
        elif pdsi_value >= -2.0:
            return 'Severely Dry'
        else:
            return 'Extremely Dry'
    
    county_pdsi['Condition'] = county_pdsi['Avg_PDSI'].apply(classify_county_condition)
    county_pdsi['Color'] = county_pdsi['Condition'].map(condition_colors)
    
    # Create district separators for visualization
    district_boundaries = []
    current_district = None
    for i, district in enumerate(county_pdsi['District']):
        if district != current_district:
            if current_district is not None:
                district_boundaries.append(i)
            current_district = district
    district_boundaries.append(len(county_pdsi))  # Add final boundary
    
    # Plot 1: Average PDSI by County
    bars1 = ax1.bar(range(len(county_pdsi)), county_pdsi['Avg_PDSI'], 
                   color=county_pdsi['Color'], alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax1.set_title('Average PDSI by County (Grouped by Agricultural District)\n(Drought-Prone vs Wet Areas)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('County (Agricultural District)', fontsize=12)
    ax1.set_ylabel('Average PDSI', fontsize=12)
    ax1.set_xticks(range(len(county_pdsi)))
    ax1.set_xticklabels(county_pdsi['County_District_Label'], rotation=45, ha='right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add district separator lines
    for boundary in district_boundaries[:-1]:  # Exclude the last boundary
        ax1.axvline(x=boundary - 0.5, color='gray', linestyle='--', alpha=0.7, linewidth=1)
    
    # Add value labels
    for i, (county, pdsi_mean) in enumerate(zip(county_pdsi['County'], county_pdsi['Avg_PDSI'])):
        ax1.text(i, pdsi_mean + (0.05 if pdsi_mean >= 0 else -0.05), 
                f'{pdsi_mean:.2f}', ha='center', va='bottom' if pdsi_mean >= 0 else 'top', 
                fontsize=8, fontweight='bold')
    
    # Add district labels at the top
    district_labels = []
    district_positions = []
    for i in range(len(district_boundaries) - 1):
        start = district_boundaries[i] if i > 0 else 0
        end = district_boundaries[i + 1]
        mid_pos = (start + end - 1) / 2
        district_labels.append(county_pdsi.iloc[start]['District'])
        district_positions.append(mid_pos)
    
    # Add district labels above the plot
    for label, pos in zip(district_labels, district_positions):
        ax1.text(pos, ax1.get_ylim()[1] * 0.95, label, ha='center', va='center', 
                fontsize=10, fontweight='bold', 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.8))
    
    # Plot 2: PDSI Range by County (Min to Max)
    for i, row in county_pdsi.iterrows():
        ax2.bar(i, row['Max_PDSI'] - row['Min_PDSI'], 
               bottom=row['Min_PDSI'], color=row['Color'], alpha=0.6, 
               edgecolor='black', linewidth=0.5)
        
        # Add error bars showing std
        ax2.errorbar(i, row['Avg_PDSI'], yerr=row['Std_PDSI'], 
                    fmt='o', color='black', capsize=3, markersize=4)
    
    ax2.set_title('PDSI Range by County (Grouped by Agricultural District)\n(Min, Max, and Standard Deviation)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('County (Agricultural District)', fontsize=12)
    ax2.set_ylabel('PDSI Range', fontsize=12)
    ax2.set_xticks(range(len(county_pdsi)))
    ax2.set_xticklabels(county_pdsi['County_District_Label'], rotation=45, ha='right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Add district separator lines to second plot
    for boundary in district_boundaries[:-1]:  # Exclude the last boundary
        ax2.axvline(x=boundary - 0.5, color='gray', linestyle='--', alpha=0.7, linewidth=1)
    
    # Create legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.8, label=condition) 
                      for condition, color in condition_colors.items()]
    ax1.legend(handles=legend_elements, title='Drought Conditions', 
              bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add statistics
    driest_county = county_pdsi.loc[county_pdsi['Avg_PDSI'].idxmin()]
    wettest_county = county_pdsi.loc[county_pdsi['Avg_PDSI'].idxmax()]
    
    stats_text = f'County Statistics:\n'
    stats_text += f'Driest: {driest_county["County"]}\n'
    stats_text += f'PDSI: {driest_county["Avg_PDSI"]:.2f}\n'
    stats_text += f'Wettest: {wettest_county["County"]}\n'
    stats_text += f'PDSI: {wettest_county["Avg_PDSI"]:.2f}'
    
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/County_PDSI_Analysis_Drought_Areas.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_county_precipitation_analysis(precip_df):
    """Create a plot showing per-county precipitation analysis to identify wet/dry areas"""
    print("\n📊 Creating per-county precipitation analysis...")
    
    # Create output directory
    output_dir = 'outputs/NDWIWaterStatistics'
    os.makedirs(output_dir, exist_ok=True)
    
    # First, we need to add district information to precipitation data
    # Load the NDWI data to get district information
    ndwi_df = pd.read_csv('data/maryland_ndwi_10day_final_imputed.csv', index_col='NAME')
    
    # Create a mapping from county to district
    county_to_district = ndwi_df[['Ag_District']].to_dict()['Ag_District']
    
    # Add district information to precipitation data
    precip_df_with_district = precip_df.copy()
    precip_df_with_district['District'] = precip_df_with_district['County'].map(county_to_district)
    
    # Remove rows where district mapping failed
    precip_df_with_district = precip_df_with_district.dropna(subset=['District'])
    
    # Calculate county-level precipitation statistics with district information
    county_precip = precip_df_with_district.groupby(['County', 'District']).agg({
        'Precipitation': ['mean', 'std', 'min', 'max', 'count']
    }).round(3)
    
    # Flatten column names
    county_precip.columns = ['Avg_Precip', 'Std_Precip', 'Min_Precip', 'Max_Precip', 'Data_Points']
    county_precip = county_precip.reset_index()
    
    # Sort by district first, then by average precipitation within each district
    county_precip = county_precip.sort_values(['District', 'Avg_Precip'])
    
    # Create a combined label for counties showing both county and district
    county_precip['County_District_Label'] = county_precip['County'] + '\n(' + county_precip['District'] + ')'
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Define precipitation condition colors (based on precipitation levels)
    condition_colors = {
        'Very Dry': '#8B0000',        # Dark Red - Very low precipitation
        'Dry': '#DC143C',             # Crimson - Low precipitation
        'Moderately Dry': '#FF6347',  # Tomato - Below average precipitation
        'Normal': '#32CD32',          # Lime Green - Normal precipitation
        'Moderately Wet': '#1E90FF',  # Dodger Blue - Above average precipitation
        'Wet': '#4169E1',             # Royal Blue - High precipitation
        'Very Wet': '#000080'         # Navy - Very high precipitation
    }
    
    # Classify counties by average precipitation
    def classify_county_precipitation(precip_value):
        if pd.isna(precip_value):
            return 'Unknown'
        elif precip_value >= 5.0:
            return 'Very Wet'
        elif precip_value >= 4.5:
            return 'Wet'
        elif precip_value >= 4.0:
            return 'Moderately Wet'
        elif precip_value >= 3.5:
            return 'Normal'
        elif precip_value >= 3.0:
            return 'Moderately Dry'
        elif precip_value >= 2.5:
            return 'Dry'
        else:
            return 'Very Dry'
    
    county_precip['Condition'] = county_precip['Avg_Precip'].apply(classify_county_precipitation)
    county_precip['Color'] = county_precip['Condition'].map(condition_colors)
    
    # Create district separators for visualization
    district_boundaries = []
    current_district = None
    for i, district in enumerate(county_precip['District']):
        if district != current_district:
            if current_district is not None:
                district_boundaries.append(i)
            current_district = district
    district_boundaries.append(len(county_precip))  # Add final boundary
    
    # Plot 1: Average Precipitation by County
    bars1 = ax1.bar(range(len(county_precip)), county_precip['Avg_Precip'], 
                   color=county_precip['Color'], alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax1.set_title('Average Precipitation by County (Grouped by Agricultural District)\n(Dry vs Wet Areas)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('County (Agricultural District)', fontsize=12)
    ax1.set_ylabel('Average Precipitation (inches)', fontsize=12)
    ax1.set_xticks(range(len(county_precip)))
    ax1.set_xticklabels(county_precip['County_District_Label'], rotation=45, ha='right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=county_precip['Avg_Precip'].mean(), color='black', linestyle='--', alpha=0.5, label='State Average')
    
    # Add district separator lines
    for boundary in district_boundaries[:-1]:  # Exclude the last boundary
        ax1.axvline(x=boundary - 0.5, color='gray', linestyle='--', alpha=0.7, linewidth=1)
    
    # Add value labels
    for i, (county, precip_mean) in enumerate(zip(county_precip['County'], county_precip['Avg_Precip'])):
        ax1.text(i, precip_mean + 0.05, f'{precip_mean:.1f}', ha='center', va='bottom', 
                fontsize=8, fontweight='bold')
    
    # Add district labels at the top
    district_labels = []
    district_positions = []
    for i in range(len(district_boundaries) - 1):
        start = district_boundaries[i] if i > 0 else 0
        end = district_boundaries[i + 1]
        mid_pos = (start + end - 1) / 2
        district_labels.append(county_precip.iloc[start]['District'])
        district_positions.append(mid_pos)
    
    # Add district labels above the plot
    #for label, pos in zip(district_labels, district_positions):
    #    ax1.text(pos, ax1.get_ylim()[1] * 0.95, label, ha='center', va='center', 
    #            fontsize=10, fontweight='bold', 
    #            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.8))
    
    # Plot 2: Precipitation Range by County (Min to Max)
    for i, row in county_precip.iterrows():
        ax2.bar(i, row['Max_Precip'] - row['Min_Precip'], 
               bottom=row['Min_Precip'], color=row['Color'], alpha=0.6, 
               edgecolor='black', linewidth=0.5)
        
        # Add error bars showing std
        ax2.errorbar(i, row['Avg_Precip'], yerr=row['Std_Precip'], 
                    fmt='o', color='black', capsize=3, markersize=4)
    
    ax2.set_title('Precipitation Range by County (Grouped by Agricultural District)\n(Min, Max, and Standard Deviation)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('County (Agricultural District)', fontsize=12)
    ax2.set_ylabel('Precipitation Range (inches)', fontsize=12)
    ax2.set_xticks(range(len(county_precip)))
    ax2.set_xticklabels(county_precip['County_District_Label'], rotation=45, ha='right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=county_precip['Avg_Precip'].mean(), color='black', linestyle='--', alpha=0.5)
    
    # Add district separator lines to second plot
    for boundary in district_boundaries[:-1]:  # Exclude the last boundary
        ax2.axvline(x=boundary - 0.5, color='gray', linestyle='--', alpha=0.7, linewidth=1)
    
    # Create legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.8, label=condition) 
                      for condition, color in condition_colors.items()]
    ax1.legend(handles=legend_elements, title='Precipitation Conditions', 
               bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add statistics
    driest_county = county_precip.loc[county_precip['Avg_Precip'].idxmin()]
    wettest_county = county_precip.loc[county_precip['Avg_Precip'].idxmax()]
    
    stats_text = f'County Statistics:\n'
    stats_text += f'Driest: {driest_county["County"]}\n'
    stats_text += f'Precip: {driest_county["Avg_Precip"]:.1f} in\n'
    stats_text += f'Wettest: {wettest_county["County"]}\n'
    stats_text += f'Precip: {wettest_county["Avg_Precip"]:.1f} in'
    
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/AveragePrecipitationByCounty.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def main():
    """Main function to run the NDWI water statistics correlation analysis"""
    print("🌱 NDWI vs WATER STATISTICS CORRELATION ANALYSIS")
    print("=" * 60)
    
    # Load data
    ndwi_df, pdsi_df, precip_df = load_and_prepare_data()
    
    # Extract monthly data
    ndwi_monthly_df = extract_monthly_ndwi_data(ndwi_df)
    pdsi_monthly_df = extract_monthly_pdsi_data(pdsi_df)
    precip_monthly_df = extract_monthly_precipitation_data(precip_df)
    
    # Merge data
    merged_df = merge_data(ndwi_monthly_df, pdsi_monthly_df, precip_monthly_df)
    
    # Create correlation plots
    create_pdsi_correlation_plots(merged_df)
    create_precipitation_correlation_plots(merged_df)
    create_comprehensive_correlation_plot(merged_df)
    
    # Create drought analysis plots
    create_pdsi_by_year_plot(pdsi_monthly_df)
    create_county_pdsi_analysis(pdsi_monthly_df)
    
    # Create precipitation analysis plots
    create_county_precipitation_analysis(precip_monthly_df)
    
    # Print summary statistics
    print_summary_statistics(merged_df)
    
    print(f"\n✅ NDWI water statistics correlation analysis completed!")
    print(f"📁 Output directory: outputs/NDWIWaterStatistics/")

if __name__ == "__main__":
    main()
