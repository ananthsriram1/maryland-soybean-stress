#!/usr/bin/env python3
"""
Yield Time Series Analysis

This script creates time series plots of soybean yield by county over the 10-year period (2014-2024),
grouped by agricultural district with consistent color coding.

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

def load_and_prepare_yield_data():
    """Load and prepare yield data from NASS"""
    print("🔄 Loading yield data...")
    
    try:
        # Load yield data
        yield_df = pd.read_csv('data/nass/Soybean_Yield_BU:Acre_By_County.csv')
        
        # Clean up the data - remove header rows
        yield_df = yield_df[yield_df['Year'] != 'Year']
        
        # Convert Year to string first, then to int to handle any string values
        yield_df['Year'] = yield_df['Year'].astype(str).str.strip()
        yield_df = yield_df[yield_df['Year'].str.isdigit()]  # Keep only numeric years
        yield_df['Year'] = yield_df['Year'].astype(int)
        
        # Filter for years 2014-2024
        yield_df = yield_df[(yield_df['Year'] >= 2014) & (yield_df['Year'] <= 2024)]
        
        # Clean up county names and district names
        yield_df['County'] = yield_df['County'].astype(str).str.strip()
        yield_df['Ag District'] = yield_df['Ag District'].astype(str).str.strip()
        
        # Convert Value to numeric, handling any missing values
        yield_df['Value'] = pd.to_numeric(yield_df['Value'], errors='coerce')
        
        # Remove rows with missing values
        yield_df = yield_df.dropna(subset=['Value', 'County', 'Ag District'])
        
        print(f"   ✅ Yield data loaded: {len(yield_df)} records")
        print(f"   📅 Years: {sorted(yield_df['Year'].unique())}")
        print(f"   🏛️  Districts: {sorted(yield_df['Ag District'].unique())}")
        print(f"   📍 Counties: {len(yield_df['County'].unique())}")
        
        return yield_df
        
    except Exception as e:
        print(f"   ❌ Error loading yield data: {e}")
        return None

def create_yield_scatter_plots(yield_df):
    """Create separate scatter plots for each year showing yield points colored by district"""
    print("\n📊 Creating yield scatter plots by year...")
    
    # Create output directory
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a mapping from county to district
    county_to_district = {}
    for district, district_county_set in district_counties.items():
        for county in district_county_set:
            county_to_district[county] = district
    
    # Calculate global axis limits for consistency across all plots
    years = sorted(yield_df['Year'].unique())
    yield_min = yield_df['Value'].min() - 2
    yield_max = yield_df['Value'].max() + 2
    
    print(f"   📏 Setting consistent axis ranges across all plots:")
    print(f"      Yield: {yield_min:.1f} to {yield_max:.1f} Bu/Acre")
    
    # Create individual scatter plots for each year
    for year in years:
        year_data = yield_df[yield_df['Year'] == year]
        
        if len(year_data) == 0:
            continue
            
        # Create the plot for this year
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot each district's data with different colors
        for district in sorted(year_data['Ag District'].unique()):
            district_data = year_data[year_data['Ag District'] == district]
            color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')  # Gray for unknown districts
            
            if len(district_data) > 0:
                # Create scatter points for this district
                # Use random x positions to spread points horizontally
                np.random.seed(42)  # For consistent positioning
                x_positions = np.random.normal(0, 0.5, len(district_data))
                
                ax.scatter(x_positions, district_data['Value'], 
                          color=color, s=100, alpha=0.9, edgecolors='black', linewidth=1,
                          label=f'{district} (n={len(district_data)})')
        
        # Customize the plot
        ax.set_title(f'Soybean Yield Distribution - {year}\n(Color-Coded by Agricultural District)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Distribution of Counties', fontsize=12)
        ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
        
        # Set fixed axis limits for consistency
        ax.set_ylim(yield_min, yield_max)
        ax.set_xlim(-2, 2)  # Small range for horizontal spread
        
        # Hide x-axis ticks since they don't represent meaningful values
        ax.set_xticks([])
        
        ax.grid(True, alpha=0.3, axis='y')
        
        # Create legend
        ax.legend(title='Agricultural District', 
                  bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        
        # Add statistics text
        year_avg = year_data['Value'].mean()
        year_max = year_data['Value'].max()
        year_min = year_data['Value'].min()
        year_count = len(year_data)
        
        stats_text = f'{year} Statistics:\n'
        stats_text += f'Counties: {year_count}\n'
        stats_text += f'Avg Yield: {year_avg:.1f} Bu/Acre\n'
        stats_text += f'Max Yield: {year_max:.1f} Bu/Acre\n'
        stats_text += f'Min Yield: {year_min:.1f} Bu/Acre'
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
               fontsize=10)
        
        plt.tight_layout()
        
        # Save the plot
        filename = f'{output_dir}/Yield_Scatter_{year}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved: {filename}")
        
        plt.show()
        plt.close()

def create_combined_yield_scatter_plot(yield_df):
    """Create a single plot showing all years' yield data separated horizontally by year"""
    print("\n📊 Creating combined yield scatter plot by year...")
    
    # Create output directory
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate global axis limits for consistency
    years = sorted(yield_df['Year'].unique())
    yield_min = yield_df['Value'].min() - 2
    yield_max = yield_df['Value'].max() + 2
    
    print(f"   📏 Setting axis ranges:")
    print(f"      Years: {min(years)} to {max(years)}")
    print(f"      Yield: {yield_min:.1f} to {yield_max:.1f} Bu/Acre")
    
    # Create the combined plot
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Plot each year's data
    for i, year in enumerate(years):
        year_data = yield_df[yield_df['Year'] == year]
        
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
                x_positions = np.random.normal(year, 0.3, len(district_data))
                
                ax.scatter(x_positions, district_data['Value'], 
                          color=color, s=80, alpha=0.8, edgecolors='black', linewidth=0.5,
                          label=f'{district}' if i == 0 else "")  # Only label once
        
        # Add year label
        ax.text(year, yield_max + 1, str(year), ha='center', va='bottom', 
                fontsize=10, fontweight='bold')
    
    # Customize the plot
    ax.set_title('Soybean Yield Distribution by Year (2014-2024)\n(Color-Coded by Agricultural District)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    
    # Set axis limits
    ax.set_xlim(min(years) - 0.5, max(years) + 0.5)
    ax.set_ylim(yield_min, yield_max + 3)  # Extra space for year labels
    
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
    
    # Add overall statistics text
    total_counties = yield_df['County'].nunique()
    total_years = len(years)
    avg_yield = yield_df['Value'].mean()
    max_yield = yield_df['Value'].max()
    min_yield = yield_df['Value'].min()
    
    stats_text = f'Overall Statistics:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre\n'
    stats_text += f'Max Yield: {max_yield:.1f} Bu/Acre\n'
    stats_text += f'Min Yield: {min_yield:.1f} Bu/Acre'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Combined_Yield_Scatter_by_Year.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_combined_yield_scatter_with_averages(yield_df):
    """Create a combined scatter plot with colored dotted lines showing district averages for each year"""
    print("\n📊 Creating combined yield scatter plot with district averages...")
    
    # Create output directory
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate global axis limits for consistency
    years = sorted(yield_df['Year'].unique())
    yield_min = yield_df['Value'].min() - 2
    yield_max = yield_df['Value'].max() + 2
    
    print(f"   📏 Setting axis ranges:")
    print(f"      Years: {min(years)} to {max(years)}")
    print(f"      Yield: {yield_min:.1f} to {yield_max:.1f} Bu/Acre")
    
    # Create the combined plot
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # First, plot all the scatter points (same as before)
    for i, year in enumerate(years):
        year_data = yield_df[yield_df['Year'] == year]
        
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
                x_positions = np.random.normal(year, 0.3, len(district_data))
                
                ax.scatter(x_positions, district_data['Value'], 
                          color=color, s=80, alpha=0.8, edgecolors='black', linewidth=0.5,
                          label=f'{district}' if i == 0 else "")  # Only label once
    
    # Now add the district average lines for each year
    for i, year in enumerate(years):
        year_data = yield_df[yield_df['Year'] == year]
        
        if len(year_data) == 0:
            continue
        
        # Calculate district averages for this year
        district_averages = year_data.groupby('Ag District')['Value'].mean()
        
        # Plot average lines for each district
        for district, avg_yield in district_averages.items():
            color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
            
            # Draw a horizontal dotted line at the district average
            ax.axhline(y=avg_yield, xmin=(year - 0.4) / (max(years) - min(years) + 1), 
                      xmax=(year + 0.4) / (max(years) - min(years) + 1),
                      color=color, linestyle='--', linewidth=2, alpha=0.9)
            
            # Add a small marker at the center of the line
            ax.scatter(year, avg_yield, color=color, s=150, marker='D', 
                      edgecolors='black', linewidth=1, alpha=0.9, zorder=5)
        
        # Add year label
        ax.text(year, yield_max + 1, str(year), ha='center', va='bottom', 
                fontsize=10, fontweight='bold')
    
    # Customize the plot
    ax.set_title('Soybean Yield Distribution by Year (2014-2024)\n(Scatter Points + District Average Lines)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    
    # Set axis limits
    ax.set_xlim(min(years) - 0.5, max(years) + 0.5)
    ax.set_ylim(yield_min, yield_max + 3)  # Extra space for year labels
    
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
    
    # Add overall statistics text
    total_counties = yield_df['County'].nunique()
    total_years = len(years)
    avg_yield = yield_df['Value'].mean()
    max_yield = yield_df['Value'].max()
    min_yield = yield_df['Value'].min()
    
    stats_text = f'Plot Elements:\n'
    stats_text += f'• Points: Individual county yields\n'
    stats_text += f'• Dashed Lines: District averages\n'
    stats_text += f'• Diamonds: Average markers\n\n'
    stats_text += f'Overall Statistics:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre\n'
    stats_text += f'Max Yield: {max_yield:.1f} Bu/Acre\n'
    stats_text += f'Min Yield: {min_yield:.1f} Bu/Acre'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=9)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Combined_Yield_Scatter_with_District_Averages.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_yield_boxplot_by_year(yield_df):
    """Create a box and whisker plot showing yield distribution by county per year, grouped by agricultural district"""
    print("\n📊 Creating yield boxplot by year...")
    
    # Create output directory
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate global axis limits for consistency
    years = sorted(yield_df['Year'].unique())
    yield_min = yield_df['Value'].min() - 2
    yield_max = yield_df['Value'].max() + 2
    
    print(f"   📏 Setting axis ranges:")
    print(f"      Years: {min(years)} to {max(years)}")
    print(f"      Yield: {yield_min:.1f} to {yield_max:.1f} Bu/Acre")
    
    # Create the boxplot
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Prepare data for boxplot - we need to create separate data for each year-district combination
    boxplot_data = []
    boxplot_labels = []
    boxplot_colors = []
    
    for year in years:
        year_data = yield_df[yield_df['Year'] == year]
        
        if len(year_data) == 0:
            continue
        
        # For each district in this year, collect the yield values
        for district in sorted(year_data['Ag District'].unique()):
            district_data = year_data[year_data['Ag District'] == district]
            
            if len(district_data) > 0:
                boxplot_data.append(district_data['Value'].values)
                boxplot_labels.append(f'{year}\n{district}')
                color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
                boxplot_colors.append(color)
    
    # Create the boxplot
    bp = ax.boxplot(boxplot_data, labels=boxplot_labels, patch_artist=True, 
                   notch=True, showfliers=True, widths=0.6)
    
    # Color the boxes
    for patch, color in zip(bp['boxes'], boxplot_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Customize the plot
    ax.set_title('Soybean Yield Distribution by County per Year (2014-2024)\n(Boxplots Grouped by Agricultural District)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year and Agricultural District', fontsize=12)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    
    # Set axis limits
    ax.set_ylim(yield_min, yield_max)
    
    # Rotate x-axis labels for better readability
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Add grid
    ax.grid(True, alpha=0.3, axis='y')
    
    # Create legend for districts
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.7, label=district) 
                      for district, color in UNIVERSAL_DISTRICT_COLORS.items()]
    ax.legend(handles=legend_elements, title='Agricultural District', 
              bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Add statistics text
    total_counties = yield_df['County'].nunique()
    total_years = len(years)
    avg_yield = yield_df['Value'].mean()
    max_yield = yield_df['Value'].max()
    min_yield = yield_df['Value'].min()
    
    stats_text = f'Boxplot Statistics:\n'
    stats_text += f'Counties: {total_counties}\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre\n'
    stats_text += f'Max Yield: {max_yield:.1f} Bu/Acre\n'
    stats_text += f'Min Yield: {min_yield:.1f} Bu/Acre\n\n'
    stats_text += f'Box Elements:\n'
    stats_text += f'• Box: 25th-75th percentile\n'
    stats_text += f'• Line: Median (50th percentile)\n'
    stats_text += f'• Whiskers: Min/Max values\n'
    stats_text += f'• Points: Outliers'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=9)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Yield_Boxplot_by_Year_and_District.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def create_district_average_plots(yield_df):
    """Create plots showing district averages over time"""
    print("\n📊 Creating district average yield plots...")
    
    # Create output directory
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate district averages by year
    district_yearly = yield_df.groupby(['Ag District', 'Year'])['Value'].agg(['mean', 'std', 'count']).reset_index()
    
    # Calculate global axis limits
    years = sorted(district_yearly['Year'].unique())
    yield_min = district_yearly['mean'].min() - 2
    yield_max = district_yearly['mean'].max() + 2
    
    print(f"   📏 Setting axis ranges:")
    print(f"      Years: {min(years)} to {max(years)}")
    print(f"      Yield: {yield_min:.1f} to {yield_max:.1f} Bu/Acre")
    
    # Create the district average plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each district average
    for district in sorted(district_yearly['Ag District'].unique()):
        district_data = district_yearly[district_yearly['Ag District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        
        # Plot the district average line
        ax.plot(district_data['Year'], district_data['mean'], 
                marker='o', linewidth=3, markersize=8, 
                color=color, alpha=0.8, label=district)
        
        # Add error bars showing standard deviation
        ax.errorbar(district_data['Year'], district_data['mean'], 
                   yerr=district_data['std'], fmt='none', color=color, alpha=0.6, capsize=3)
    
    # Customize the plot
    ax.set_title('Average Soybean Yield by Agricultural District Over Time (2014-2024)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Average Yield (Bu/Acre)', fontsize=12)
    
    # Set fixed axis limits
    ax.set_xlim(min(years) - 0.5, max(years) + 0.5)
    ax.set_ylim(yield_min, yield_max)
    
    # Set x-axis ticks
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45)
    
    ax.grid(True, alpha=0.3)
    
    # Create legend
    ax.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Add statistics text
    total_districts = len(district_yearly['Ag District'].unique())
    total_years = len(years)
    avg_yield = district_yearly['mean'].mean()
    
    stats_text = f'District Statistics:\n'
    stats_text += f'Districts: {total_districts}\n'
    stats_text += f'Years: {total_years}\n'
    stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = f'{output_dir}/Yield_Time_Series_District_Averages.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    
    plt.show()
    plt.close()

def print_summary_statistics(yield_df):
    """Print summary statistics for the yield data"""
    print("\n📊 YIELD TIME SERIES ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Overall statistics
    total_records = len(yield_df)
    total_counties = yield_df['County'].nunique()
    total_districts = yield_df['Ag District'].nunique()
    years = sorted(yield_df['Year'].unique())
    
    print(f"\n📈 Overall Statistics:")
    print(f"   Total records: {total_records}")
    print(f"   Counties: {total_counties}")
    print(f"   Districts: {total_districts}")
    print(f"   Years: {len(years)} ({min(years)}-{max(years)})")
    
    # Yield statistics
    avg_yield = yield_df['Value'].mean()
    std_yield = yield_df['Value'].std()
    min_yield = yield_df['Value'].min()
    max_yield = yield_df['Value'].max()
    
    print(f"\n🌾 Yield Statistics:")
    print(f"   Average: {avg_yield:.1f} Bu/Acre")
    print(f"   Std Dev: {std_yield:.1f} Bu/Acre")
    print(f"   Range: {min_yield:.1f} - {max_yield:.1f} Bu/Acre")
    
    # District statistics
    print(f"\n🏛️  District Statistics:")
    district_stats = yield_df.groupby('Ag District')['Value'].agg(['mean', 'std', 'count']).round(1)
    for district, stats in district_stats.iterrows():
        print(f"   {district:20}: {stats['mean']:5.1f} ± {stats['std']:4.1f} Bu/Acre (n={stats['count']})")
    
    # Year statistics
    print(f"\n📅 Year Statistics:")
    year_stats = yield_df.groupby('Year')['Value'].agg(['mean', 'std']).round(1)
    for year, stats in year_stats.iterrows():
        print(f"   {year}: {stats['mean']:5.1f} ± {stats['std']:4.1f} Bu/Acre")

def main():
    """Main function to run the yield time series analysis"""
    print("🌾 YIELD TIME SERIES ANALYSIS")
    print("=" * 50)
    
    # Load data
    yield_df = load_and_prepare_yield_data()
    
    if yield_df is None:
        print("❌ Failed to load yield data. Exiting.")
        return
    
    # Create plots
    create_yield_scatter_plots(yield_df)
    create_combined_yield_scatter_plot(yield_df)
    create_combined_yield_scatter_with_averages(yield_df)
    create_yield_boxplot_by_year(yield_df)
    create_district_average_plots(yield_df)
    
    # Print summary statistics
    print_summary_statistics(yield_df)
    
    print(f"\n✅ Yield time series analysis completed!")
    print(f"📁 Output directory: outputs/YieldAnalysis/")

if __name__ == "__main__":
    main()
