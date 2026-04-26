#!/usr/bin/env python3
"""
Monthly NDWI Analysis by Agricultural District

This script creates separate plots for each month showing NDWI values by agricultural district
with counties color-coded by their district affiliation.

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

# Universal color scheme for agricultural districts (same as PlotIntervalNDWI)
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFEAA7'             # Yellow - Lowest development
}

# Month names for plotting
MONTH_NAMES = {
    'April': 'April',
    'May': 'May', 
    'June': 'June',
    'July': 'July',
    'August': 'August',
    'September': 'September',
    'October': 'October'
}

# Growing season months
GROWING_SEASON_MONTHS = ['April', 'May', 'June', 'July', 'August', 'September', 'October']

def load_and_prepare_data():
    """Load and prepare NDWI data for monthly analysis"""
    print("🔄 Loading NDWI data...")
    
    try:
        ndwi_df = pd.read_csv('data/maryland_ndwi_10day_final_imputed.csv', index_col='NAME')
        print(f"   ✅ NDWI data loaded successfully: {ndwi_df.shape}")
        print(f"   🏛️  Agricultural districts: {ndwi_df['Ag_District'].unique()}")
        print(f"   📍 Counties: {len(ndwi_df.index)}")
        return ndwi_df
    except Exception as e:
        print(f"   ❌ Error loading NDWI data: {e}")
        raise

def extract_monthly_data(ndwi_df):
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
                        if pd.notna(value) and value != 0:  # Skip NaN and zero values
                            ndwi_values.append(value)
                    
                    if ndwi_values:
                        avg_ndwi = np.mean(ndwi_values)
                        min_ndwi = np.min(ndwi_values)
                        max_ndwi = np.max(ndwi_values)
                        
                        monthly_data.append({
                            'County': county,
                            'District': district,
                            'Year': year,
                            'Month': month,
                            'Avg_NDWI': avg_ndwi,
                            'Min_NDWI': min_ndwi,
                            'Max_NDWI': max_ndwi,
                            'Data_Points': len(ndwi_values)
                        })
    
    monthly_df = pd.DataFrame(monthly_data)
    print(f"   ✅ Monthly data extracted: {len(monthly_df)} records")
    print(f"   📅 Years: {sorted(monthly_df['Year'].unique())}")
    print(f"   📆 Months: {sorted(monthly_df['Month'].unique())}")
    print(f"   🏛️  Districts: {sorted(monthly_df['District'].unique())}")
    
    return monthly_df

def create_monthly_plots(monthly_df):
    """Create separate plots for each month showing NDWI by agricultural district"""
    print("\n📊 Creating monthly NDWI plots...")
    
    # Create output directory
    output_dir = 'outputs/MonthlyNDWI'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate global axis limits for consistency across all plots
    all_ndwi_values = monthly_df['Avg_NDWI'].values
    y_min = np.percentile(all_ndwi_values, 5) - 0.05  # 5th percentile minus buffer
    y_max = np.percentile(all_ndwi_values, 95) + 0.05  # 95th percentile plus buffer
    
    # Round to nice numbers
    y_min = np.floor(y_min * 10) / 10
    y_max = np.ceil(y_max * 10) / 10
    
    print(f"   📏 Setting consistent Y-axis range: {y_min:.1f} to {y_max:.1f}")
    
    for month in GROWING_SEASON_MONTHS:
        print(f"   📈 Creating plot for {month}...")
        
        # Filter data for this month
        month_data = monthly_df[monthly_df['Month'] == month].copy()
        
        if len(month_data) == 0:
            print(f"   ⚠️  No data found for {month}")
            continue
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Get unique years and sort them
        years = sorted(month_data['Year'].unique())
        
        # Create x-axis positions for each year
        x_positions = {}
        year_pos = 0
        for year in years:
            x_positions[year] = year_pos
            year_pos += 1
        
        # Plot data for each district
        for district in sorted(month_data['District'].unique()):
            district_data = month_data[month_data['District'] == district]
            color = UNIVERSAL_DISTRICT_COLORS[district]
            
            # Group by year and calculate district averages
            yearly_avg = district_data.groupby('Year')['Avg_NDWI'].agg(['mean', 'std', 'count']).reset_index()
            
            # Plot the main line
            ax.plot([x_positions[year] for year in yearly_avg['Year']], 
                   yearly_avg['mean'], 
                   marker='o', linewidth=3, markersize=8, 
                   color=color, label=f'{district} (n={district_data["County"].nunique()})', 
                   alpha=0.8)
            
            # Add error bars for standard deviation
            ax.errorbar([x_positions[year] for year in yearly_avg['Year']], 
                       yearly_avg['mean'], 
                       yerr=yearly_avg['std'], 
                       color=color, alpha=0.3, capsize=5)
            
            # Add individual county data points (more visible)
            for year in years:
                year_district_data = district_data[district_data['Year'] == year]
                if len(year_district_data) > 0:
                    x_jittered = np.random.normal(x_positions[year], 0.05, len(year_district_data))
                    ax.scatter(x_jittered, year_district_data['Avg_NDWI'], 
                             color=color, alpha=0.7, s=40, zorder=1, edgecolors='white', linewidth=0.5)
        
        # Customize the plot
        ax.set_title(f'Soybean Water Content (NDWI) in {month}\nby Agricultural District (2019-2024)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('NDWI (Normalized Difference Water Index)', fontsize=12)
        ax.set_xticks(list(x_positions.values()))
        ax.set_xticklabels(list(x_positions.keys()))
        ax.set_ylim(y_min, y_max)  # Set consistent Y-axis limits
        ax.grid(True, alpha=0.3)
        ax.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Add horizontal line at water stress threshold
        ax.axhline(y=0.1325, color='red', linestyle='--', alpha=0.7, linewidth=2, 
                  label='Water Stress Threshold (0.1325)')
        
        # Add statistics text box
        total_counties = month_data['County'].nunique()
        total_districts = month_data['District'].nunique()
        avg_ndwi = month_data['Avg_NDWI'].mean()
        min_ndwi = month_data['Avg_NDWI'].min()
        max_ndwi = month_data['Avg_NDWI'].max()
        
        stats_text = f'Statistics for {month}:\n'
        stats_text += f'Counties: {total_counties}\n'
        stats_text += f'Districts: {total_districts}\n'
        stats_text += f'Avg NDWI: {avg_ndwi:.3f}\n'
        stats_text += f'Range: {min_ndwi:.3f} - {max_ndwi:.3f}'
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=10)
        
        plt.tight_layout()
        
        # Save the plot
        filename = f'{output_dir}/{month}_NDWI_by_District.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved: {filename}")
        
        plt.show()
        plt.close()

def create_district_comparison_plot(monthly_df):
    """Create a comprehensive comparison plot showing all months"""
    print("\n📊 Creating comprehensive district comparison plot...")
    
    # Calculate district averages for each month
    district_monthly_avg = monthly_df.groupby(['District', 'Month'])['Avg_NDWI'].agg(['mean', 'std', 'count']).reset_index()
    
    # Calculate global axis limits for consistency
    all_ndwi_values = monthly_df['Avg_NDWI'].values
    y_min = np.percentile(all_ndwi_values, 5) - 0.05
    y_max = np.percentile(all_ndwi_values, 95) + 0.05
    y_min = np.floor(y_min * 10) / 10
    y_max = np.ceil(y_max * 10) / 10
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(18, 12))
    
    # Plot each district
    for district in sorted(district_monthly_avg['District'].unique()):
        district_data = district_monthly_avg[district_monthly_avg['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        # Sort by month order
        month_order = ['April', 'May', 'June', 'July', 'August', 'September', 'October']
        district_data = district_data.set_index('Month').reindex(month_order).reset_index()
        
        ax.plot(district_data['Month'], district_data['mean'], 
               marker='o', linewidth=3, markersize=8, 
               color=color, label=district, alpha=0.8)
        
        # Add error bars
        ax.errorbar(district_data['Month'], district_data['mean'], 
                   yerr=district_data['std'], 
                   color=color, alpha=0.3, capsize=5)
    
    # Customize the plot
    ax.set_title('Soybean Water Content (NDWI) Throughout Growing Season\nby Agricultural District (2019-2024 Average)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('NDWI (Normalized Difference Water Index)', fontsize=12)
    ax.set_ylim(y_min, y_max)  # Set consistent Y-axis limits
    ax.grid(True, alpha=0.3)
    ax.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add horizontal line at water stress threshold
    ax.axhline(y=0.1325, color='red', linestyle='--', alpha=0.7, linewidth=2, 
              label='Water Stress Threshold (0.1325)')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    output_dir = 'outputs/MonthlyNDWI'
    filename = f'{output_dir}/Growing_Season_NDWI_Comparison.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def print_summary_statistics(monthly_df):
    """Print summary statistics for the monthly NDWI analysis"""
    print("\n📊 MONTHLY NDWI ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Overall statistics
    print(f"\n📈 Overall Statistics:")
    print(f"   Total records: {len(monthly_df):,}")
    print(f"   Counties: {monthly_df['County'].nunique()}")
    print(f"   Districts: {monthly_df['District'].nunique()}")
    print(f"   Years: {monthly_df['Year'].nunique()} ({min(monthly_df['Year'])}-{max(monthly_df['Year'])})")
    print(f"   Months: {monthly_df['Month'].nunique()}")
    
    # Average NDWI by district
    print(f"\n🏛️  Average NDWI by District:")
    district_avg = monthly_df.groupby('District')['Avg_NDWI'].agg(['mean', 'std', 'count']).round(3)
    district_avg = district_avg.sort_values('mean', ascending=False)
    
    for district, row in district_avg.iterrows():
        print(f"   {district:<25}: {row['mean']:>6.3f} ± {row['std']:>5.3f} (n={row['count']:>3})")
    
    # Average NDWI by month
    print(f"\n📅 Average NDWI by Month:")
    month_avg = monthly_df.groupby('Month')['Avg_NDWI'].agg(['mean', 'std', 'count']).round(3)
    month_order = ['April', 'May', 'June', 'July', 'August', 'September', 'October']
    month_avg = month_avg.reindex(month_order)
    
    for month, row in month_avg.iterrows():
        print(f"   {month:<12}: {row['mean']:>6.3f} ± {row['std']:>5.3f} (n={row['count']:>3})")
    
    # Water stress analysis
    print(f"\n💧 Water Stress Analysis (NDWI < 0.1325):")
    stress_data = monthly_df[monthly_df['Avg_NDWI'] < 0.1325]
    total_records = len(monthly_df)
    stress_records = len(stress_data)
    stress_percentage = (stress_records / total_records) * 100
    
    print(f"   Stress records: {stress_records:,} / {total_records:,} ({stress_percentage:.1f}%)")
    
    # Stress by district
    print(f"   Stress by District:")
    district_stress = stress_data.groupby('District').size()
    district_total = monthly_df.groupby('District').size()
    
    for district in sorted(district_stress.index):
        stress_count = district_stress[district]
        total_count = district_total[district]
        stress_pct = (stress_count / total_count) * 100
        print(f"     {district:<25}: {stress_count:>3} / {total_count:>3} ({stress_pct:>5.1f}%)")

def main():
    """Main function to run the monthly NDWI analysis"""
    print("🌱 MONTHLY NDWI ANALYSIS BY AGRICULTURAL DISTRICT")
    print("=" * 60)
    
    # Load data
    ndwi_df = load_and_prepare_data()
    
    # Extract monthly data
    monthly_df = extract_monthly_data(ndwi_df)
    
    # Create individual monthly plots
    create_monthly_plots(monthly_df)
    
    # Create comprehensive comparison plot
    create_district_comparison_plot(monthly_df)
    
    # Print summary statistics
    print_summary_statistics(monthly_df)
    
    print(f"\n✅ Monthly NDWI analysis completed!")
    print(f"📁 Output directory: outputs/MonthlyNDWI/")

if __name__ == "__main__":
    main()
