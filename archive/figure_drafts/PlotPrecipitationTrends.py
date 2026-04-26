#!/usr/bin/env python3
"""
Growing Season Precipitation Analysis
Creates comprehensive precipitation visualizations by district and county.

Author: Maryland Soybean Stress Project
"""

import os
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

warnings.filterwarnings('ignore')

# Set plotting style
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    try:
        plt.style.use('seaborn')
    except OSError:
        plt.style.use('default')

sns.set_palette("husl")

UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',
    'SOUTHERN': '#90EE90',
    'LOWER EASTERN SHORE': '#4ECDC4',
    'UPPER EASTERN SHORE': '#9370DB',
    'WESTERN': '#FFD700'
}

district_counties = {
    'WESTERN': {'Allegany', 'Garrett'},
    'UPPER EASTERN SHORE': {'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'},
    'SOUTHERN': {'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"},
    'NORTH CENTRAL': {'Baltimore', 'Baltimore City', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 'Washington'},
    'LOWER EASTERN SHORE': {'Dorchester', 'Somerset', 'Wicomico', 'Worchester'}  # Note: precipitation data has 'Worchester' with 'h'
}


def load_precipitation_data(months=None):
    """Load and process precipitation data for specified months."""
    if months is None:
        months = [4, 5, 6, 7, 8, 9, 10]  # Growing season
    
    month_str = f"{min(months)}-{max(months)}" if len(months) > 1 else str(months[0])
    print(f"🔄 Loading precipitation data for months {months}...")
    
    # Load wide format
    precip_df = pd.read_csv('data/maryland_precipitation_combined_wide.csv', index_col='County')
    
    # Convert to long format
    precip_long = precip_df.reset_index().melt(
        id_vars='County',
        var_name='date_col',
        value_name='Precipitation'
    )
    
    precip_long['date'] = pd.to_datetime(precip_long['date_col'].str.replace('Precip_', ''))
    precip_long['Year'] = precip_long['date'].dt.year
    precip_long['Month'] = precip_long['date'].dt.month
    
    # Filter for selected months
    precip_long = precip_long[precip_long['Month'].isin(months)]
    
    # Clean county names
    precip_long['County'] = precip_long['County'].str.strip()
    precip_long['Precipitation'] = pd.to_numeric(precip_long['Precipitation'], errors='coerce')
    precip_long = precip_long.dropna(subset=['Precipitation'])
    
    # Map to districts
    county_to_district = {}
    for district, counties in district_counties.items():
        for county in counties:
            county_to_district[county] = district
            # Handle name variations
            if county == "Queen Anne's":
                county_to_district["Queen Annes"] = district
                county_to_district["Queen Anne's"] = district
            elif county == "Prince George's":
                county_to_district["Prince Georges"] = district
                county_to_district["Prince George's"] = district
            elif county == "St. Mary's":
                county_to_district["St Marys"] = district
                county_to_district["St. Mary's"] = district
    
    precip_long['District'] = precip_long['County'].map(county_to_district)
    precip_long = precip_long.dropna(subset=['District'])
    
    print(f"   ✅ Loaded {len(precip_long)} records")
    print(f"   📅 Years: {precip_long['Year'].min()}-{precip_long['Year'].max()}")
    print(f"   📍 Counties: {precip_long['County'].nunique()}")
    
    return precip_long, month_str


def plot_district_precipitation_trends(precip_long, month_str, output_dir):
    """Plot district-level precipitation trends."""
    print("\n📊 Creating district precipitation trends...")
    
    # Calculate growing season totals by district and year
    district_yearly = precip_long.groupby(['District', 'Year'])['Precipitation'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for district in sorted(district_yearly['District'].unique()):
        dist_data = district_yearly[district_yearly['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax.plot(dist_data['Year'], dist_data['Precipitation'], 
               marker='o', linewidth=2.5, markersize=8, label=district, 
               color=color, alpha=0.85)
    
    ax.set_title(f'Growing Season Total Precipitation by District (Months {month_str})', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Total Precipitation (inches)', fontsize=13)
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/District_Precipitation_Trends.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {os.path.basename(filename)}")
    plt.close()


def plot_county_precipitation_trends(precip_long, month_str, output_dir):
    """Plot county-level precipitation trends by district."""
    print("\n📊 Creating county precipitation trends (5 district plots)...")
    
    # Calculate yearly totals by county
    county_yearly = precip_long.groupby(['County', 'District', 'Year'])['Precipitation'].sum().reset_index()
    
    for district in sorted(county_yearly['District'].unique()):
        district_data = county_yearly[county_yearly['District'] == district]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        district_color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        
        # Plot each county
        counties = sorted(district_data['County'].unique())
        palette = sns.color_palette('tab10', n_colors=len(counties))
        
        for idx, county in enumerate(counties):
            county_data = district_data[district_data['County'] == county]
            ax.plot(county_data['Year'], county_data['Precipitation'], 
                   marker='o', linewidth=2, markersize=6, label=county, 
                   alpha=0.75)
        
        # Add district average
        dist_avg = district_data.groupby('Year')['Precipitation'].mean().reset_index()
        ax.plot(dist_avg['Year'], dist_avg['Precipitation'], 
               marker='s', linewidth=3.5, markersize=10, 
               label=f'{district} Average', 
               color=district_color, alpha=0.9, linestyle='--', zorder=10)
        
        ax.set_title(f'{district}\nGrowing Season Total Precipitation (Months {month_str})', 
                    fontsize=16, fontweight='bold')
        ax.set_xlabel('Year', fontsize=13)
        ax.set_ylabel('Total Precipitation (inches)', fontsize=13)
        ax.legend(loc='best', fontsize=10, ncol=2)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        filename = f"{output_dir}/{district.replace(' ', '_')}_County_Precipitation.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"      💾 Saved: {os.path.basename(filename)}")
        plt.close()


def plot_county_precipitation_heatmap(precip_long, month_str, output_dir):
    """Create county-level heatmap of precipitation by county and year."""
    print("\n📊 Creating county precipitation heatmap...")
    
    # Calculate yearly totals
    county_yearly = precip_long.groupby(['County', 'Year'])['Precipitation'].sum().reset_index()
    
    # Pivot to wide format
    heatmap_data = county_yearly.pivot(index='County', columns='Year', values='Precipitation')
    
    # Use standardized county ordering to match yield heatmaps
    # Map precipitation county names to yield county names for consistent ordering
    county_name_mapping = {
        'Somerset': 'SOMERSET',
        'Dorchester': 'DORCHESTER', 
        'Wicomico': 'WICOMICO',
        'Worchester': 'WORCESTER',  # Note: precipitation data has 'Worchester' with 'h'
        'Harford': 'HARFORD',
        'Baltimore': 'BALTIMORE',
        'Frederick': 'FREDERICK',
        'Carroll': 'CARROLL',
        'Washington': 'WASHINGTON',
        'Howard': 'HOWARD',
        'Montgomery': 'MONTGOMERY',
        'Anne Arundel': 'ANNE ARUNDEL',
        "Prince George's": "PRINCE GEORGE'S",
        'Calvert': 'CALVERT',
        "St. Mary's": "ST. MARY'S",
        'Charles': 'CHARLES',
        'Kent': 'KENT',
        'Cecil': 'CECIL',
        "Queen Anne's": "QUEEN ANNE'S",
        'Talbot': 'TALBOT',
        'Caroline': 'CAROLINE',
        'Garrett': 'GARRETT'
    }
    
    # Create standardized order based on processed yield data format
    standardized_county_order = [
        # LOWER EASTERN SHORE
        'SOMERSET', 'DORCHESTER', 'WICOMICO', 'WORCESTER',
        # NORTH CENTRAL  
        'HARFORD', 'BALTIMORE', 'FREDERICK', 'CARROLL', 'WASHINGTON', 'HOWARD', 'MONTGOMERY', 'ANNE ARUNDEL',
        # SOUTHERN
        "PRINCE GEORGE'S", 'CALVERT', "ST. MARY'S", 'CHARLES',
        # UPPER EASTERN SHORE
        'KENT', 'CECIL', "QUEEN ANNE'S", 'TALBOT', 'CAROLINE',
        # WESTERN
        'GARRETT'
    ]
    
    # Map precipitation county names to yield format and reorder
    heatmap_data.index = heatmap_data.index.map(lambda x: county_name_mapping.get(x, x))
    available_counties = [county for county in standardized_county_order if county in heatmap_data.index]
    heatmap_data = heatmap_data.reindex(available_counties)
    
    fig, ax = plt.subplots(figsize=(18, 10))
    
    # Create heatmap with annotations, handling NaN values
    # Replace NaN with "N/A" for display, format numbers to 2 decimal places
    heatmap_display = heatmap_data.copy()
    heatmap_display = heatmap_display.fillna('N/A')
    
    # Format numeric values to 2 decimal places
    for col in heatmap_display.columns:
        for idx in heatmap_display.index:
            if heatmap_display.loc[idx, col] != 'N/A':
                try:
                    heatmap_display.loc[idx, col] = f"{heatmap_display.loc[idx, col]:.2f}"
                except (ValueError, TypeError):
                    pass
    
    sns.heatmap(heatmap_data, cmap='Blues', annot=heatmap_display, fmt='',
               cbar_kws={'label': 'Total Precipitation (inches)'},
               linewidths=0.5, ax=ax,
               annot_kws={'fontsize': 8, 'fontweight': 'bold'})
    
    # Adjust text colors based on background
    heatmap_obj = ax.collections[0]
    vmin, vmax = heatmap_obj.get_clim()
    threshold = (vmin + vmax) / 2
    
    # Adjust text colors for better readability
    for text in ax.texts:
        text_content = text.get_text()
        if text_content == 'N/A':
            text.set_color('red')
            text.set_fontweight('bold')
        else:
            try:
                value = float(text_content)
                if value > threshold:
                    text.set_color('white')
                else:
                    text.set_color('black')
            except ValueError:
                continue
    
    ax.set_title(f'Growing Season Total Precipitation by County and Year (Months {month_str})', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('County', fontsize=13)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/County_Precipitation_Heatmap.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {os.path.basename(filename)}")
    plt.close()


def plot_district_precipitation_heatmap(precip_long, month_str, output_dir):
    """Create district-level heatmap of precipitation by district and year."""
    print("\n📊 Creating district precipitation heatmap...")
    
    # Calculate yearly totals by district
    district_yearly = precip_long.groupby(['District', 'Year'])['Precipitation'].sum().reset_index()
    
    # Pivot to wide format
    heatmap_data = district_yearly.pivot(index='District', columns='Year', values='Precipitation')
    
    # Sort districts in specific order
    district_order = ['WESTERN', 'NORTH CENTRAL', 'SOUTHERN', 
                     'LOWER EASTERN SHORE', 'UPPER EASTERN SHORE']
    heatmap_data = heatmap_data.reindex([d for d in district_order if d in heatmap_data.index])
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    # Create heatmap with annotations, handling NaN values
    # Replace NaN with "N/A" for display, format numbers to 2 decimal places
    heatmap_display = heatmap_data.copy()
    heatmap_display = heatmap_display.fillna('N/A')
    
    # Format numeric values to 2 decimal places
    for col in heatmap_display.columns:
        for idx in heatmap_display.index:
            if heatmap_display.loc[idx, col] != 'N/A':
                try:
                    heatmap_display.loc[idx, col] = f"{heatmap_display.loc[idx, col]:.2f}"
                except (ValueError, TypeError):
                    pass
    
    sns.heatmap(heatmap_data, cmap='Blues', annot=heatmap_display, fmt='',
               cbar_kws={'label': 'Total Precipitation (inches)'},
               linewidths=1, ax=ax,
               annot_kws={'fontsize': 10, 'fontweight': 'bold'})
    
    # Adjust text colors based on background
    heatmap_obj = ax.collections[0]
    vmin, vmax = heatmap_obj.get_clim()
    threshold = (vmin + vmax) / 2
    
    # Adjust text colors for better readability
    for text in ax.texts:
        text_content = text.get_text()
        if text_content == 'N/A':
            text.set_color('red')
            text.set_fontweight('bold')
        else:
            try:
                value = float(text_content)
                if value > threshold:
                    text.set_color('white')
                else:
                    text.set_color('black')
            except ValueError:
                continue
    
    ax.set_title(f'Average Growing Season Precipitation by District and Year (Months {month_str})', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Agricultural District', fontsize=13)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/District_Precipitation_Heatmap.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {os.path.basename(filename)}")
    plt.close()


def plot_district_precipitation_distribution(precip_long, month_str, output_dir):
    """Box plot comparison of precipitation distributions."""
    print("\n📊 Creating precipitation distribution plots...")
    
    # Calculate yearly totals
    data_for_plot = precip_long.groupby(['County', 'District', 'Year'])['Precipitation'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    districts = ['WESTERN', 'SOUTHERN', 'LOWER EASTERN SHORE', 
                'UPPER EASTERN SHORE', 'NORTH CENTRAL']
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in districts]
    
    bp_data = [data_for_plot[data_for_plot['District']==d]['Precipitation'].values for d in districts]
    bp = ax.boxplot(bp_data, labels=districts, patch_artist=True, widths=0.6)
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor('black')
        patch.set_linewidth(1.5)
    
    ax.set_title(f'Growing Season Precipitation Distribution by District (Months {month_str})', 
                fontsize=16, fontweight='bold')
    ax.set_ylabel('Total Precipitation (inches)', fontsize=13)
    ax.grid(axis='y', alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=15, ha='right')
    
    plt.tight_layout()
    
    filename = f'{output_dir}/District_Precipitation_Distribution.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {os.path.basename(filename)}")
    plt.close()


def plot_precipitation_variability(precip_long, month_str, output_dir):
    """Analyze precipitation variability across counties."""
    print("\n📊 Creating precipitation variability analysis...")
    
    # Calculate county statistics
    county_yearly = precip_long.groupby(['County', 'District', 'Year'])['Precipitation'].sum().reset_index()
    county_stats = county_yearly.groupby(['County', 'District']).agg({
        'Precipitation': ['mean', 'std', 'min', 'max', 'count']
    }).reset_index()
    county_stats.columns = ['County', 'District', 'Mean', 'Std', 'Min', 'Max', 'Count']
    county_stats['CV'] = (county_stats['Std'] / county_stats['Mean'] * 100)
    county_stats = county_stats.sort_values('Mean')
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Mean precipitation by county
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in county_stats['District']]
    
    ax1.barh(range(len(county_stats)), county_stats['Mean'], 
            color=colors, edgecolor='black', linewidth=0.5, alpha=0.8)
    ax1.set_yticks(range(len(county_stats)))
    ax1.set_yticklabels(county_stats['County'], fontsize=9)
    ax1.set_title(f'Average Growing Season Precipitation by County\n(Months {month_str})', 
                 fontsize=14, fontweight='bold')
    ax1.set_xlabel('Average Total Precipitation (inches)', fontsize=12)
    ax1.grid(axis='x', alpha=0.3)
    
    # Add district legend
    legend_elements = [plt.Rectangle((0,0),1,1, fc=color, ec='black', alpha=0.8, label=district) 
                      for district, color in UNIVERSAL_DISTRICT_COLORS.items()]
    ax1.legend(handles=legend_elements, loc='lower right', fontsize=9)
    
    # Plot 2: Variability (CV)
    ax2.barh(range(len(county_stats)), county_stats['CV'], 
            color=colors, edgecolor='black', linewidth=0.5, alpha=0.8)
    ax2.set_yticks(range(len(county_stats)))
    ax2.set_yticklabels(county_stats['County'], fontsize=9)
    ax2.set_title('Precipitation Variability (Coefficient of Variation)', 
                 fontsize=14, fontweight='bold')
    ax2.set_xlabel('CV (%)', fontsize=12)
    ax2.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/County_Precipitation_Variability.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {os.path.basename(filename)}")
    plt.close()


def plot_dry_vs_wet_years(precip_long, month_str, output_dir):
    """Compare wettest vs driest years by district."""
    print("\n📊 Creating wet vs dry year comparison...")
    
    # Calculate district yearly totals
    district_yearly = precip_long.groupby(['District', 'Year'])['Precipitation'].sum().reset_index()
    
    # Identify wettest and driest years statewide
    statewide_yearly = precip_long.groupby('Year')['Precipitation'].sum().reset_index()
    statewide_yearly = statewide_yearly.sort_values('Precipitation')
    
    driest_5 = statewide_yearly.head(5)['Year'].tolist()
    wettest_5 = statewide_yearly.tail(5)['Year'].tolist()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Driest years
    dry_data = district_yearly[district_yearly['Year'].isin(driest_5)]
    
    for district in sorted(dry_data['District'].unique()):
        dist_data = dry_data[dry_data['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax1.plot(dist_data['Year'], dist_data['Precipitation'], 
                marker='o', linewidth=2.5, markersize=9, label=district, 
                color=color, alpha=0.85)
    
    ax1.set_title(f'5 Driest Growing Seasons (Statewide)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Total Precipitation (inches)', fontsize=12)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Wettest years
    wet_data = district_yearly[district_yearly['Year'].isin(wettest_5)]
    
    for district in sorted(wet_data['District'].unique()):
        dist_data = wet_data[wet_data['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax2.plot(dist_data['Year'], dist_data['Precipitation'], 
                marker='o', linewidth=2.5, markersize=9, label=district, 
                color=color, alpha=0.85)
    
    ax2.set_title(f'5 Wettest Growing Seasons (Statewide)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Total Precipitation (inches)', fontsize=12)
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/Dry_vs_Wet_Years_Districts.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {os.path.basename(filename)}")
    plt.close()


def generate_precipitation_summary(precip_long, month_str):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print(f"PRECIPITATION SUMMARY (MONTHS {month_str})")
    print("=" * 80)
    
    # Overall stats
    county_yearly = precip_long.groupby(['County', 'District', 'Year'])['Precipitation'].sum().reset_index()
    
    print(f"\nOVERALL STATISTICS:")
    print(f"  Years covered: {county_yearly['Year'].min()}-{county_yearly['Year'].max()}")
    print(f"  Average total precipitation: {county_yearly['Precipitation'].mean():.1f} inches")
    print(f"  Min (driest county-year): {county_yearly['Precipitation'].min():.1f} inches")
    print(f"  Max (wettest county-year): {county_yearly['Precipitation'].max():.1f} inches")
    
    print(f"\nBY DISTRICT:")
    for district in sorted(county_yearly['District'].unique()):
        dist_data = county_yearly[county_yearly['District'] == district]
        print(f"\n  {district}:")
        print(f"    Mean: {dist_data['Precipitation'].mean():.1f} inches")
        print(f"    Std:  {dist_data['Precipitation'].std():.1f} inches")
        print(f"    Range: {dist_data['Precipitation'].min():.1f} - {dist_data['Precipitation'].max():.1f} inches")
        print(f"    CV: {(dist_data['Precipitation'].std() / dist_data['Precipitation'].mean() * 100):.1f}%")


def main():
    """Run precipitation analysis for multiple time windows."""
    print("=" * 80)
    print("GROWING SEASON PRECIPITATION ANALYSIS")
    print("=" * 80)
    
    output_dir = 'outputs/Precipitation'
    os.makedirs(output_dir, exist_ok=True)
    
    # Full growing season (April-October)
    print("\n" + "=" * 80)
    print("FULL GROWING SEASON (April-October)")
    print("=" * 80)
    
    precip_full, month_str_full = load_precipitation_data(months=[4, 5, 6, 7, 8, 9, 10])
    
    plot_district_precipitation_trends(precip_full, month_str_full, output_dir)
    plot_county_precipitation_trends(precip_full, month_str_full, output_dir)
    plot_county_precipitation_heatmap(precip_full, month_str_full, output_dir)
    plot_district_precipitation_heatmap(precip_full, month_str_full, output_dir)
    plot_district_precipitation_distribution(precip_full, month_str_full, output_dir)
    plot_dry_vs_wet_years(precip_full, month_str_full, output_dir)
    plot_precipitation_variability(precip_full, month_str_full, output_dir)
    
    generate_precipitation_summary(precip_full, month_str_full)
    
    # Critical period (July-September / R4-R6)
    print("\n\n" + "=" * 80)
    print("CRITICAL PERIOD (July-September / R4-R6)")
    print("=" * 80)
    
    precip_r46, month_str_r46 = load_precipitation_data(months=[7, 8, 9])
    
    # Create R4-R6 specific plots
    output_r46 = f'{output_dir}/R4-R6'
    os.makedirs(output_r46, exist_ok=True)
    
    plot_district_precipitation_trends(precip_r46, month_str_r46, output_r46)
    plot_county_precipitation_trends(precip_r46, month_str_r46, output_r46)
    plot_county_precipitation_heatmap(precip_r46, month_str_r46, output_r46)
    plot_district_precipitation_heatmap(precip_r46, month_str_r46, output_r46)
    plot_district_precipitation_distribution(precip_r46, month_str_r46, output_r46)
    plot_dry_vs_wet_years(precip_r46, month_str_r46, output_r46)
    plot_precipitation_variability(precip_r46, month_str_r46, output_r46)
    
    generate_precipitation_summary(precip_r46, month_str_r46)
    
    print("\n" + "=" * 80)
    print("✅ Precipitation analysis complete!")
    print(f"📁 Main output: {output_dir}/")
    print(f"📁 R4-R6 output: {output_r46}/")
    print("=" * 80)


if __name__ == "__main__":
    main()

