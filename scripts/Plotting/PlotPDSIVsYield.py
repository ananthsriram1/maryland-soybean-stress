#!/usr/bin/env python3
"""
PDSI vs Yield Correlation Analysis by Agricultural District

This script creates separate scatter plots for each agricultural district showing the 
correlation between growing season PDSI (Palmer Drought Severity Index) and soybean yield.

Author: Analysis for Maryland Soybean Stress Project
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
import os
from calendar import month_abbr
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

# Agricultural district codes mapping
district_codes = {
    10: 'WESTERN',
    20: 'NORTH CENTRAL', 
    30: 'UPPER EASTERN SHORE',
    80: 'SOUTHERN',
    90: 'LOWER EASTERN SHORE'
}

# Universal color scheme for all plots - consistent across the entire analysis
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFD700'             # Bright Gold - Lowest development (more visible)
}

def format_month_range(months):
    """Return a human-friendly month range label (e.g., 'Apr-Oct' or 'Jul, Sep')."""
    months = sorted(set(months))
    if not months:
        return ""

    consecutive = all(b - a == 1 for a, b in zip(months, months[1:]))
    month_names = [month_abbr[m] for m in months]

    if consecutive:
        return f"{month_names[0]}-{month_names[-1]}"
    return ", ".join(month_names)


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

        # Exclude aggregated "OTHER (COMBINED) COUNTIES" entries
        other_mask = yield_df['County'].str.contains('OTHER', case=False, na=False)
        if other_mask.any():
            print(f"   🚫 Removing {other_mask.sum()} 'Other (Combined)' county records")
            yield_df = yield_df[~other_mask]
        
        print(f"   ✅ Yield data loaded: {len(yield_df)} records")
        print(f"   📅 Years: {sorted(yield_df['Year'].unique())}")
        print(f"   🏛️  Districts: {sorted(yield_df['Ag District'].unique())}")
        print(f"   📍 Counties: {len(yield_df['County'].unique())}")
        
        return yield_df
        
    except Exception as e:
        print(f"   ❌ Error loading yield data: {e}")
        return None

def load_and_prepare_pdsi_data(months=None, label_suffix=""):
    """Load and prepare PDSI data for specified months."""
    if months is None:
        months = [4, 5, 6, 7, 8, 9, 10]

    month_label = "-".join(str(m) for m in sorted(months))
    if label_suffix:
        month_label = label_suffix

    print(f"🔄 Loading PDSI data for months: {sorted(months)} ({month_label})")

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
        
        # Filter for selected months
        pdsi_long = pdsi_long[pdsi_long['date'].dt.month.isin(months)]
        
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

def map_counties_to_districts(df, county_col='County'):
    """Map counties to agricultural districts using both county names and district codes"""
    print("🔄 Mapping counties to agricultural districts...")
    
    # First, try to use existing Ag District column if it exists
    if 'Ag District' in df.columns and 'Ag District Code' in df.columns:
        print("   📊 Using existing Ag District and Ag District Code columns...")
        
        # Convert district codes to district names
        df['Ag District Code'] = pd.to_numeric(df['Ag District Code'], errors='coerce')
        df['Ag District'] = df['Ag District Code'].map(district_codes)
        
        # Handle cases where we have district codes but missing district names
        missing_districts = df['Ag District'].isna() & df['Ag District Code'].notna()
        if missing_districts.any():
            print(f"   ⚠️  Found {missing_districts.sum()} records with district codes but missing district names")
    
    else:
        # Fallback to county name mapping
        print("   📊 Using county name mapping...")
        county_to_district = {}
        for district, district_county_set in district_counties.items():
            for county in district_county_set:
                # Handle both exact matches and variations
                county_to_district[county.upper()] = district
                # Also map common variations
                if county == "Queen Anne's":
                    county_to_district["QUEEN ANNES"] = district
                elif county == "Prince George's":
                    county_to_district["PRINCE GEORGES"] = district
                elif county == "St. Mary's":
                    county_to_district["ST MARYS"] = district
        
        # Add district information to the dataframe
        df['Ag District'] = df[county_col].str.upper().map(county_to_district)
    
    # Remove rows where district mapping failed
    df = df.dropna(subset=['Ag District'])
    
    print(f"   ✅ District mapping completed: {len(df)} records with districts")
    print(f"   🏛️  Districts: {sorted(df['Ag District'].unique())}")
    
    # Print mapping details for debugging
    print(f"   📍 Counties per district:")
    for district in sorted(df['Ag District'].unique()):
        district_counties_found = df[df['Ag District'] == district][county_col].unique()
        print(f"      {district}: {len(district_counties_found)} counties")
        for county in sorted(district_counties_found):
            print(f"        - {county}")
    
    return df

def prepare_combined_data(yield_df, pdsi_long, label_suffix=""):
    """Combine yield and PDSI data for analysis"""
    print("🔄 Combining yield and PDSI data...")
    
    # Calculate average growing season PDSI by county and year
    pdsi_avg = pdsi_long.groupby(['County', 'Year'])['PDSI'].mean().reset_index()
    pdsi_avg = pdsi_avg.rename(columns={'PDSI': 'Avg_Growing_Season_PDSI'})
    
    # Handle "OTHER (COMBINED) COUNTIES" by assigning them district average PDSI values
    # Merge yield and PDSI data
    combined_df = pd.merge(yield_df, pdsi_avg, on=['County', 'Year'], how='inner')
    
    if label_suffix:
        print(f"   ✅ Combined data prepared ({label_suffix}): {len(combined_df)} records")
    else:
        print(f"   ✅ Combined data prepared: {len(combined_df)} records")
    print(f"   📅 Years: {sorted(combined_df['Year'].unique())}")
    print(f"   🏛️  Districts: {sorted(combined_df['Ag District'].unique())}")
    
    # Print district breakdown
    print(f"   📍 Records per district:")
    for district in sorted(combined_df['Ag District'].unique()):
        district_data = combined_df[combined_df['Ag District'] == district]
        print(f"      {district}: {len(district_data)} records")
        # Show which counties are in each district
        counties_in_district = district_data['County'].unique()
        for county in sorted(counties_in_district):
            county_records = len(district_data[district_data['County'] == county])
            print(f"        - {county}: {county_records} records")
    
    return combined_df

def create_pdsi_vs_yield_plots(combined_df, months, label_suffix=""):
    """Create separate PDSI vs Yield scatter plots for each agricultural district"""
    if label_suffix:
        print(f"\n📊 Creating PDSI vs Yield plots ({label_suffix}) by district...")
    else:
        print("\n📊 Creating PDSI vs Yield correlation plots by district...")
    
    # Create output directory
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate global axis limits for consistency
    pdsi_min = combined_df['Avg_Growing_Season_PDSI'].min() - 0.5
    pdsi_max = combined_df['Avg_Growing_Season_PDSI'].max() + 0.5
    yield_min = combined_df['Value'].min() - 2
    yield_max = combined_df['Value'].max() + 2
    
    print(f"   📏 Setting consistent axis ranges:")
    print(f"      PDSI: {pdsi_min:.1f} to {pdsi_max:.1f}")
    print(f"      Yield: {yield_min:.1f} to {yield_max:.1f} Bu/Acre")
    
    # Create separate plots for each district
    districts = sorted(combined_df['Ag District'].unique())
    
    month_label = format_month_range(months)

    for district in districts:
        district_data = combined_df[combined_df['Ag District'] == district]
        
        if len(district_data) == 0:
            continue
        
        # Create the plot for this district
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Get district color (used for regression line and annotations)
        district_color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        
        # Plot each county with its own color so individual locations are clear
        counties = sorted(district_data['County'].unique())
        palette_name = 'tab20' if len(counties) <= 20 else 'husl'
        county_colors = sns.color_palette(palette_name, n_colors=len(counties))
        county_color_map = dict(zip(counties, county_colors))

        labels_added = set()

        for county in counties:
            county_data = district_data[district_data['County'] == county]
            county_color = county_color_map[county]
            label = county if county not in labels_added else None
            ax.scatter(
                county_data['Avg_Growing_Season_PDSI'],
                county_data['Value'],
                s=110,
                alpha=0.85,
                edgecolors='black',
                linewidth=0.9,
                color=county_color,
                label=label
            )

            if label is not None:
                labels_added.add(county)

            # Label the most recent observation for each county for quick identification
            if not county_data.empty:
                latest_idx = county_data['Year'].idxmax()
                latest_point = county_data.loc[latest_idx]
                ax.annotate(
                    county,
                    xy=(latest_point['Avg_Growing_Season_PDSI'], latest_point['Value']),
                    xytext=(6, 6),
                    textcoords='offset points',
                    fontsize=9,
                    fontweight='semibold',
                    color=county_color,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.7)
                )

        # Calculate correlation coefficient where possible
        if (
            len(district_data) >= 2 and
            district_data['Avg_Growing_Season_PDSI'].nunique() > 1 and
            district_data['Value'].nunique() > 1
        ):
            correlation, p_value = stats.pearsonr(
                district_data['Avg_Growing_Season_PDSI'],
                district_data['Value']
            )
        else:
            correlation, p_value = (np.nan, np.nan)

        # Add trend line if we have enough variation
        if not np.isnan(correlation):
            z = np.polyfit(
                district_data['Avg_Growing_Season_PDSI'],
                district_data['Value'],
                1
            )
            trend_fn = np.poly1d(z)
            x_vals = np.linspace(pdsi_min, pdsi_max, 200)
            ax.plot(
                x_vals,
                trend_fn(x_vals),
                color=district_color,
                linestyle='--',
                linewidth=2.2,
                alpha=0.9,
                label='Trend line'
            )
        
        # Customize the plot
        title_suffix = f" ({label_suffix})" if label_suffix else ""
        timeframe = f"{month_label}"
        ax.set_title(f'PDSI vs Soybean Yield{title_suffix}\n{district} Agricultural District', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(f'Average PDSI ({timeframe})', fontsize=12)
        ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
        
        # Set fixed axis limits for consistency
        ax.set_xlim(pdsi_min, pdsi_max)
        ax.set_ylim(yield_min, yield_max)
        
        ax.grid(True, alpha=0.3)
        
        # Add statistics text
        n_counties = district_data['County'].nunique()
        n_years = district_data['Year'].nunique()
        avg_pdsi = district_data['Avg_Growing_Season_PDSI'].mean()
        avg_yield = district_data['Value'].mean()
        
        stats_text = f'District Statistics:\n'
        stats_text += f'Counties: {n_counties}\n'
        stats_text += f'Years: {n_years}\n'
        stats_text += f'Data Points: {len(district_data)}\n'
        stats_text += f'Avg PDSI: {avg_pdsi:.1f}\n'
        stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre\n\n'
        stats_text += f'Correlation Analysis:\n'

        if np.isnan(correlation):
            stats_text += 'Correlation: N/A\n'
            stats_text += 'P-value: N/A\n'
            stats_text += 'R²: N/A'
            interpretation = 'Insufficient variation\n(Correlation not available)'
        else:
            stats_text += f'Correlation: {correlation:.3f}\n'
            stats_text += f'P-value: {p_value:.3f}\n'
            stats_text += f'R²: {correlation**2:.3f}'

            # Add interpretation
            if correlation > 0.3:
                interpretation = "Strong positive correlation\n(Higher PDSI = Higher Yield)"
            elif correlation > 0.1:
                interpretation = "Moderate positive correlation\n(Higher PDSI = Higher Yield)"
            elif correlation > -0.1:
                interpretation = "Weak correlation\n(Little relationship)"
            elif correlation > -0.3:
                interpretation = "Moderate negative correlation\n(Higher PDSI = Lower Yield)"
            else:
                interpretation = "Strong negative correlation\n(Higher PDSI = Lower Yield)"
        
        stats_text += f'\n\nInterpretation:\n{interpretation}'
        
        ax.text(
            0.02,
            0.98,
            stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            fontsize=9
        )
        
        # Add drought threshold line
        ax.axvline(x=0, color='red', linestyle='-', linewidth=2, alpha=0.7, 
                   label='Drought Threshold (PDSI = 0)')

        # Add legend when manageable number of counties
        if len(counties) <= 15:
            ax.legend(loc='lower left', bbox_to_anchor=(0, -0.25), ncol=3, fontsize=9)
        
        plt.tight_layout()
        
        # Save the plot
        filename_suffix = f'_{label_suffix}' if label_suffix else ''
        filename = f'{output_dir}/PDSI_vs_Yield_{district.replace(" ", "_")}{filename_suffix}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved: {filename}")
        
        plt.show()
        plt.close()

def print_summary_statistics(combined_df, label_suffix=""):
    """Print summary statistics for the combined data"""
    if label_suffix:
        print(f"\n📊 PDSI VS YIELD CORRELATION ANALYSIS SUMMARY ({label_suffix})")
    else:
        print("\n📊 PDSI VS YIELD CORRELATION ANALYSIS SUMMARY")
    print("=" * 60)
    
    # Overall statistics
    total_records = len(combined_df)
    total_counties = combined_df['County'].nunique()
    total_districts = combined_df['Ag District'].nunique()
    years = sorted(combined_df['Year'].unique())
    
    print(f"\n📈 Overall Statistics:")
    print(f"   Total records: {total_records}")
    print(f"   Counties: {total_counties}")
    print(f"   Districts: {total_districts}")
    print(f"   Years: {len(years)} ({min(years)}-{max(years)})")
    
    # Correlation statistics by district
    print(f"\n🔗 District Correlation Statistics:")
    for district in sorted(combined_df['Ag District'].unique()):
        district_data = combined_df[combined_df['Ag District'] == district]
        correlation, p_value = stats.pearsonr(district_data['Avg_Growing_Season_PDSI'], 
                                            district_data['Value'])
        print(f"   {district:20}: r={correlation:5.3f}, p={p_value:.3f}, R²={correlation**2:.3f}")

def run_analysis(months=None, label_suffix=""):
    """Run the PDSI vs Yield correlation analysis for specified months."""
    if months is None:
        months = [4, 5, 6, 7, 8, 9, 10]

    if label_suffix:
        print(f"🌡️  PDSI VS YIELD CORRELATION ANALYSIS ({label_suffix})")
    else:
        print("🌡️  PDSI VS YIELD CORRELATION ANALYSIS")
    print("=" * 50)
    
    # Load data
    yield_df = load_and_prepare_yield_data()
    pdsi_long = load_and_prepare_pdsi_data(months=months, label_suffix=label_suffix)
    
    if yield_df is None or pdsi_long is None:
        print("❌ Failed to load data. Exiting.")
        return
    
    # Map counties to districts for both datasets
    yield_df = map_counties_to_districts(yield_df)
    pdsi_long = map_counties_to_districts(pdsi_long)
    
    # Combine data
    combined_df = prepare_combined_data(yield_df, pdsi_long, label_suffix=label_suffix)
    
    # Create plots
    create_pdsi_vs_yield_plots(combined_df, months=months, label_suffix=label_suffix)
    
    # Print summary statistics
    print_summary_statistics(combined_df, label_suffix=label_suffix)
    
    print("\n✅ PDSI vs Yield correlation analysis completed!")
    print("📁 Output directory: outputs/YieldAnalysis/")


def main():
    run_analysis()


if __name__ == "__main__":
    main()
