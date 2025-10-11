#!/usr/bin/env python3
"""
PDSI Scatter Plot Analysis

This script creates a scatter plot of PDSI (Palmer Drought Severity Index) by county over the years (2014-2024),
grouped by agricultural district with consistent color coding, similar to the yield scatter plot.

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

# Agricultural district mapping (same as other scripts)
district_counties = {
    'WESTERN': {'Allegany', 'Garrett'},
    'UPPER EASTERN SHORE': {'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'},
    'SOUTHERN': {'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"},
    'NORTH CENTRAL': {'Baltimore', 'Baltimore City', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 'Washington'},
    'LOWER EASTERN SHORE': {'Dorchester', 'Somerset', 'Wicomico', 'Worcester'}
}

# Universal color scheme for all plots - consistent across the entire analysis
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFD700'             # Bright Gold - Lowest development (more visible)
}

def load_and_prepare_pdsi_data():
    """Load and prepare PDSI data from combined wide format"""
    print("🔄 Loading PDSI data...")
    
    try:
        # Load PDSI data
        pdsi_df = pd.read_csv('data/maryland_pdsi_combined_wide.csv', index_col='County')
        
        print(f"   ✅ PDSI data loaded: {len(pdsi_df)} counties")
        print(f"   📅 Date columns: {len(pdsi_df.columns)}")
        
        # Convert from wide to long format
        pdsi_long = pdsi_df.reset_index().melt(
            id_vars='County', 
            var_name='date_col', 
            value_name='PDSI'
        )
        
        # Clean up the date column
        pdsi_long['date'] = pdsi_long['date_col'].str.replace('PDSI_', '')
        pdsi_long['date'] = pd.to_datetime(pdsi_long['date'])
        pdsi_long['Year'] = pdsi_long['date'].dt.year
        
        # Filter for years 2014-2024
        pdsi_long = pdsi_long[(pdsi_long['Year'] >= 2014) & (pdsi_long['Year'] <= 2024)]
        
        # Filter for growing season months (April-October)
        pdsi_long = pdsi_long[pdsi_long['date'].dt.month.isin([4, 5, 6, 7, 8, 9, 10])]
        
        # Clean up county names
        pdsi_long['County'] = pdsi_long['County'].str.upper().str.strip()
        
        # Convert PDSI to numeric, handling any missing values
        pdsi_long['PDSI'] = pd.to_numeric(pdsi_long['PDSI'], errors='coerce')
        
        # Remove rows with missing values
        pdsi_long = pdsi_long.dropna(subset=['PDSI', 'County'])
        
        print(f"   ✅ PDSI data processed: {len(pdsi_long)} records")
        print(f"   📅 Years: {sorted(pdsi_long['Year'].unique())}")
        print(f"   📍 Counties: {len(pdsi_long['County'].unique())}")
        
        return pdsi_long
        
    except Exception as e:
        print(f"   ❌ Error loading PDSI data: {e}")
        return None

def map_counties_to_districts(pdsi_long):
    """Map counties to agricultural districts"""
    print("🔄 Mapping counties to agricultural districts...")
    
    # Create a mapping from county to district
    county_to_district = {}
    for district, district_county_set in district_counties.items():
        for county in district_county_set:
            county_to_district[county.upper()] = district
    
    # Add district information to the dataframe
    pdsi_long['Ag District'] = pdsi_long['County'].map(county_to_district)
    
    # Remove rows where district mapping failed
    pdsi_long = pdsi_long.dropna(subset=['Ag District'])
    
    print(f"   ✅ District mapping completed: {len(pdsi_long)} records with districts")
    print(f"   🏛️  Districts: {sorted(pdsi_long['Ag District'].unique())}")
    
    return pdsi_long

def create_pdsi_scatter_with_averages(pdsi_long, start_year, end_year, period_name):
    """Create a scatter plot with colored dotted lines showing district averages for specified years"""
    print(f"\n📊 Creating PDSI scatter plot for {period_name} ({start_year}-{end_year})...")
    
    # Create output directory
    output_dir = 'outputs/DroughtIndices'
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter data for the specified period
    period_data = pdsi_long[(pdsi_long['Year'] >= start_year) & (pdsi_long['Year'] <= end_year)]
    
    if len(period_data) == 0:
        print(f"   ⚠️  No data found for period {start_year}-{end_year}")
        return
    
    # Calculate axis limits for this period
    years = sorted(period_data['Year'].unique())
    pdsi_min = period_data['PDSI'].min() - 1
    pdsi_max = period_data['PDSI'].max() + 1
    
    print(f"   📏 Setting axis ranges:")
    print(f"      Years: {min(years)} to {max(years)}")
    print(f"      PDSI: {pdsi_min:.1f} to {pdsi_max:.1f}")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # First, plot all the scatter points
    for i, year in enumerate(years):
        year_data = period_data[period_data['Year'] == year]
        
        if len(year_data) == 0:
            continue
        
        # Plot each district's data with different colors
        for district in sorted(year_data['Ag District'].unique()):
            district_data = year_data[year_data['Ag District'] == district]
            color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')  # Gray for unknown districts
            
            if len(district_data) > 0:
                # Create scatter points for this district in this year
                # Use random x positions centered around the year
                np.random.seed(42 + i)  # Different seed for each year
                x_positions = np.random.normal(year, 0.25, len(district_data))
                
                ax.scatter(x_positions, district_data['PDSI'], 
                          color=color, s=60, alpha=0.8, edgecolors='black', linewidth=0.5,
                          label=f'{district}' if i == 0 else "")  # Only label once
    
    # Now add the district average lines for each year
    for i, year in enumerate(years):
        year_data = period_data[period_data['Year'] == year]
        
        if len(year_data) == 0:
            continue
        
        # Calculate district averages for this year
        district_averages = year_data.groupby('Ag District')['PDSI'].mean()
        
        # Plot average lines for each district
        for district, avg_pdsi in district_averages.items():
            color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
            
            # Draw a horizontal dotted line at the district average
            ax.axhline(y=avg_pdsi, xmin=(year - 0.35) / (max(years) - min(years) + 1), 
                      xmax=(year + 0.35) / (max(years) - min(years) + 1),
                      color=color, linestyle='--', linewidth=2, alpha=0.9)
            
            # Add a small marker at the center of the line
            ax.scatter(year, avg_pdsi, color=color, s=120, marker='D', 
                      edgecolors='black', linewidth=1, alpha=0.9, zorder=5)
        
        # Add year label
        ax.text(year, pdsi_max + 0.3, str(year), ha='center', va='bottom', 
                fontsize=10, fontweight='bold')
    
    # Add horizontal line at PDSI = 0 (drought threshold)
    ax.axhline(y=0, color='red', linestyle='-', linewidth=2, alpha=0.7, 
               label='Drought Threshold (0)')
    
    # Customize the plot
    ax.set_title(f'Growing Season PDSI Distribution by Year ({start_year}-{end_year})\n(April-October: Scatter Points + District Average Lines)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('PDSI Value', fontsize=12)
    
    # Set axis limits
    ax.set_xlim(min(years) - 0.4, max(years) + 0.4)
    ax.set_ylim(pdsi_min, pdsi_max + 1.0)  # Extra space for year labels
    
    # Set x-axis ticks
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # Create legend (only show each district once)
    handles, labels = ax.get_legend_handles_labels()
    unique_labels = []
    unique_handles = []
    for handle, label in zip(handles, labels):
        if label not in unique_labels and label != "":
            unique_labels.append(label)
            unique_handles.append(handle)
    
    ax.legend(unique_handles, unique_labels, title='Agricultural District', 
              bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Add period-specific statistics text
    total_counties = period_data['County'].nunique()
    total_years = len(years)
    avg_pdsi = period_data['PDSI'].mean()
    max_pdsi = period_data['PDSI'].max()
    min_pdsi = period_data['PDSI'].min()
    
    stats_text = f'Plot Elements:\n'
    stats_text += f'• Points: Individual county PDSI\n'
    stats_text += f'• Dashed Lines: District averages\n'
    stats_text += f'• Diamonds: Average markers\n\n'
    stats_text += f'{period_name} Growing Season Stats:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Months: April-October\n'
    stats_text += f'Avg PDSI: {avg_pdsi:.1f}\n'
    stats_text += f'Max PDSI: {max_pdsi:.1f}\n'
    stats_text += f'Min PDSI: {min_pdsi:.1f}\n\n'
    stats_text += f'PDSI Interpretation:\n'
    stats_text += f'• > 2.0: Extremely Wet\n'
    stats_text += f'• 1.0 to 2.0: Very Wet\n'
    stats_text += f'• 0.5 to 1.0: Moderately Wet\n'
    stats_text += f'• -0.5 to 0.5: Near Normal\n'
    stats_text += f'• -1.0 to -0.5: Moderately Dry\n'
    stats_text += f'• -2.0 to -1.0: Severely Dry\n'
    stats_text += f'• < -2.0: Extremely Dry'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=8)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Growing_Season_PDSI_Scatter_{start_year}_{end_year}_{period_name.replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_both_pdsi_scatter_plots(pdsi_long):
    """Create two separate PDSI scatter plots for different time periods"""
    print("\n📊 Creating separate PDSI scatter plots for different time periods...")
    
    # Create plot for 2014-2019
    create_pdsi_scatter_with_averages(pdsi_long, 2014, 2019, "Early Period")
    
    # Create plot for 2020-2024
    create_pdsi_scatter_with_averages(pdsi_long, 2020, 2024, "Recent Period")

def print_summary_statistics(pdsi_long):
    """Print summary statistics for the PDSI data"""
    print("\n📊 GROWING SEASON PDSI SCATTER PLOT ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Overall statistics
    total_records = len(pdsi_long)
    total_counties = pdsi_long['County'].nunique()
    total_districts = pdsi_long['Ag District'].nunique()
    years = sorted(pdsi_long['Year'].unique())
    
    print(f"\n📈 Overall Statistics:")
    print(f"   Total records: {total_records}")
    print(f"   Counties: {total_counties}")
    print(f"   Districts: {total_districts}")
    print(f"   Years: {len(years)} ({min(years)}-{max(years)})")
    
    # PDSI statistics
    avg_pdsi = pdsi_long['PDSI'].mean()
    std_pdsi = pdsi_long['PDSI'].std()
    min_pdsi = pdsi_long['PDSI'].min()
    max_pdsi = pdsi_long['PDSI'].max()
    
    print(f"\n🌡️  Growing Season PDSI Statistics:")
    print(f"   Average: {avg_pdsi:.1f}")
    print(f"   Std Dev: {std_pdsi:.1f}")
    print(f"   Range: {min_pdsi:.1f} - {max_pdsi:.1f}")
    print(f"   Months: April-October")
    
    # District statistics
    print(f"\n🏛️  District Statistics:")
    district_stats = pdsi_long.groupby('Ag District')['PDSI'].agg(['mean', 'std', 'count']).round(1)
    for district, stats in district_stats.iterrows():
        print(f"   {district:20}: {stats['mean']:5.1f} ± {stats['std']:4.1f} (n={stats['count']})")
    
    # Year statistics
    print(f"\n📅 Growing Season Year Statistics:")
    year_stats = pdsi_long.groupby('Year')['PDSI'].agg(['mean', 'std']).round(1)
    for year, stats in year_stats.iterrows():
        print(f"   {year}: {stats['mean']:5.1f} ± {stats['std']:4.1f}")

def main():
    """Main function to run the PDSI scatter plot analysis"""
    print("🌡️  GROWING SEASON PDSI SCATTER PLOT ANALYSIS")
    print("=" * 50)
    
    # Load data
    pdsi_long = load_and_prepare_pdsi_data()
    
    if pdsi_long is None:
        print("❌ Failed to load PDSI data. Exiting.")
        return
    
    # Map counties to districts
    pdsi_long = map_counties_to_districts(pdsi_long)
    
    # Create plots
    create_both_pdsi_scatter_plots(pdsi_long)
    
    # Print summary statistics
    print_summary_statistics(pdsi_long)
    
    print(f"\n✅ Growing season PDSI scatter plot analysis completed!")
    print(f"📁 Output directory: outputs/DroughtIndices/")

if __name__ == "__main__":
    main()
