#!/usr/bin/env python3
"""
Comprehensive Yield Visualization Suite
Generates extensive set of plots from processed yield data (1997-2024).

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


def load_datasets():
    """Load all processed yield datasets."""
    print("🔄 Loading processed yield datasets...")
    
    base = 'data/processed_yield'
    
    datasets = {
        'long': pd.read_csv(f'{base}/yield_clean_long_format.csv'),
        'wide_county': pd.read_csv(f'{base}/yield_wide_by_county.csv', index_col='County'),
        'district_avg': pd.read_csv(f'{base}/yield_district_averages_by_year.csv'),
        'wide_district': pd.read_csv(f'{base}/yield_district_wide.csv', index_col='District'),
        'summary': pd.read_csv(f'{base}/yield_summary_by_county.csv'),
        'quality': pd.read_csv(f'{base}/yield_data_quality_report.csv'),
        'recent': pd.read_csv(f'{base}/yield_2014_2024.csv'),
        'census': pd.read_csv(f'{base}/yield_census_years.csv')
    }
    
    print(f"   ✅ Loaded {len(datasets)} datasets")
    return datasets


def plot_1_district_time_series(data, output_dir):
    """Plot 1: District average yields over time."""
    print("\n📊 Plot 1: District time series...")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for district in sorted(data['district_avg']['District'].unique()):
        district_data = data['district_avg'][data['district_avg']['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax.plot(district_data['Year'], district_data['Yield_mean'], 
               marker='o', linewidth=2.5, markersize=8, label=district, 
               color=color, alpha=0.85)
        ax.fill_between(district_data['Year'],
                       district_data['Yield_mean'] - district_data['Yield_std'],
                       district_data['Yield_mean'] + district_data['Yield_std'],
                       color=color, alpha=0.15)
    
    ax.set_title('Soybean Yield by Agricultural District (1997-2024)\nWith Standard Deviation Bands', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=13)
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_District_Yield_Time_Series.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 01_District_Yield_Time_Series.png")
    plt.close()


def plot_2_county_heatmap(data, output_dir):
    """Plot 2: County x Year heatmap."""
    print("\n📊 Plot 2: County x Year heatmap...")
    
    fig, ax = plt.subplots(figsize=(18, 10))
    
    # Use standardized county ordering based on what's actually available in yield data
    # Yield data has different county names (all caps, different formatting)
    standardized_county_order = [
        # LOWER EASTERN SHORE
        'SOMERSET', 'DORCHESTER', 'WICOMICO', 'WORCESTER',
        # NORTH CENTRAL  
        'HARFORD', 'BALTIMORE', 'FREDERICK', 'CARROLL', 'WASHINGTON', 'HOWARD', 'MONTGOMERY', 'ANNE ARUNDEL',
        # SOUTHERN
        'PRINCE GEORGES', 'CALVERT', 'ST MARYS', 'CHARLES',
        # UPPER EASTERN SHORE
        'KENT', 'CECIL', 'QUEEN ANNES', 'TALBOT', 'CAROLINE',
        # WESTERN
        'GARRETT'
    ]
    
    # Reorder the heatmap data to match standardized order
    available_counties = [county for county in standardized_county_order if county in data['wide_county'].index]
    wide_sorted = data['wide_county'].reindex(available_counties)
    
    # Create display version with 2 decimal places and N/A for missing data
    heatmap_display = wide_sorted.copy()
    heatmap_display = heatmap_display.fillna('N/A')
    
    # Format numeric values to 2 decimal places
    for col in heatmap_display.columns:
        for idx in heatmap_display.index:
            if heatmap_display.loc[idx, col] != 'N/A':
                try:
                    heatmap_display.loc[idx, col] = f"{heatmap_display.loc[idx, col]:.2f}"
                except (ValueError, TypeError):
                    pass
    
    sns.heatmap(wide_sorted, cmap='RdYlGn', center=45, annot=heatmap_display, 
               fmt='', cbar_kws={'label': 'Yield (Bu/Acre)'}, 
               linewidths=0.5, ax=ax, vmin=20, vmax=60,
               annot_kws={'fontsize': 8, 'fontweight': 'bold'})
    
    # Adjust text colors for better readability - use higher threshold for white text
    for text in ax.texts:
        text_content = text.get_text()
        if text_content == 'N/A':
            text.set_color('red')
            text.set_fontweight('bold')
        else:
            try:
                value = float(text_content)
                # Use higher threshold - only use white text for very high yields (green cells)
                # Use black text for everything else (red, orange, yellow, light green)
                if value >= 52:
                    text.set_color('white')
                    text.set_fontweight('bold')
                else:
                    text.set_color('black')
                    text.set_fontweight('bold')
            except ValueError:
                continue
    
    # Add note about NASS data availability - position it below the plot area
    ax.text(0.5, -0.08, 'Note: N/A indicates data not available in NASS', 
            transform=ax.transAxes, fontsize=8, 
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9),
            verticalalignment='top', horizontalalignment='center')
    
    ax.set_title('Soybean Yield by County and Year (1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('County', fontsize=13)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_County_Year_Heatmap.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 02_County_Year_Heatmap.png")
    plt.close()


def plot_2b_county_heatmap_2012plus(data, output_dir):
    """Plot 2B: County x Year heatmap (2012 onwards)."""
    print("\n📊 Plot 2B: County x Year heatmap (2012+)...")
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Use standardized county ordering based on what's actually available in yield data
    # Yield data has different county names (all caps, different formatting)
    standardized_county_order = [
        # LOWER EASTERN SHORE
        'SOMERSET', 'DORCHESTER', 'WICOMICO', 'WORCESTER',
        # NORTH CENTRAL  
        'HARFORD', 'BALTIMORE', 'FREDERICK', 'CARROLL', 'WASHINGTON', 'HOWARD', 'MONTGOMERY', 'ANNE ARUNDEL',
        # SOUTHERN
        'PRINCE GEORGES', 'CALVERT', 'ST MARYS', 'CHARLES',
        # UPPER EASTERN SHORE
        'KENT', 'CECIL', 'QUEEN ANNES', 'TALBOT', 'CAROLINE',
        # WESTERN
        'GARRETT'
    ]
    
    # Reorder the heatmap data to match standardized order
    available_counties = [county for county in standardized_county_order if county in data['wide_county'].index]
    wide_sorted = data['wide_county'].reindex(available_counties)
    
    # Filter to 2012 onwards
    years_2012plus = [col for col in wide_sorted.columns if int(col) >= 2012]
    wide_2012plus = wide_sorted[years_2012plus]
    
    # Create display version with 2 decimal places and N/A for missing data
    heatmap_display = wide_2012plus.copy()
    heatmap_display = heatmap_display.fillna('N/A')
    
    # Format numeric values to 2 decimal places
    for col in heatmap_display.columns:
        for idx in heatmap_display.index:
            if heatmap_display.loc[idx, col] != 'N/A':
                try:
                    heatmap_display.loc[idx, col] = f"{heatmap_display.loc[idx, col]:.2f}"
                except (ValueError, TypeError):
                    pass
    
    sns.heatmap(wide_2012plus, cmap='RdYlGn', center=45, annot=heatmap_display, 
               fmt='', cbar_kws={'label': 'Yield (Bu/Acre)'}, 
               linewidths=0.5, ax=ax, vmin=20, vmax=60,
               annot_kws={'fontsize': 8, 'fontweight': 'bold'})
    
    # Adjust text colors for better readability - use higher threshold for white text
    for text in ax.texts:
        text_content = text.get_text()
        if text_content == 'N/A':
            text.set_color('red')
            text.set_fontweight('bold')
        else:
            try:
                value = float(text_content)
                # Use higher threshold - only use white text for very high yields (green cells)
                # Use black text for everything else (red, orange, yellow, light green)
                if value >= 52:
                    text.set_color('white')
                    text.set_fontweight('bold')
                else:
                    text.set_color('black')
                    text.set_fontweight('bold')
            except ValueError:
                continue
    
    # Add note about NASS data availability - position it below the plot area
    ax.text(0.5, -0.08, 'Note: N/A indicates data not available in NASS', 
            transform=ax.transAxes, fontsize=8, 
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9),
            verticalalignment='top', horizontalalignment='center')
    
    ax.set_title('Soybean Yield by County and Year (2012-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('County', fontsize=13)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/02B_County_Year_Heatmap_2012plus.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 02B_County_Year_Heatmap_2012plus.png")
    plt.close()


def plot_3_district_heatmap(data, output_dir):
    """Plot 3: District x Year heatmap."""
    print("\n📊 Plot 3: District x Year heatmap...")
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    # Create custom color list for y-axis
    district_order = ['WESTERN', 'NORTH CENTRAL', 'SOUTHERN', 
                     'LOWER EASTERN SHORE', 'UPPER EASTERN SHORE']
    wide_sorted = data['wide_district'].reindex([d for d in district_order if d in data['wide_district'].index])
    
    sns.heatmap(wide_sorted, cmap='RdYlGn', center=45, annot=True, 
               fmt='.1f', cbar_kws={'label': 'Avg Yield (Bu/Acre)'}, 
               linewidths=1, ax=ax, vmin=20, vmax=60)
    
    ax.set_title('Average Soybean Yield by District and Year (1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Agricultural District', fontsize=13)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_District_Year_Heatmap.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 03_District_Year_Heatmap.png")
    plt.close()


def plot_4_box_plots_by_district(data, output_dir):
    """Plot 4: Box plots comparing districts."""
    print("\n📊 Plot 4: Yield distribution by district...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    districts = ['WESTERN', 'SOUTHERN', 'LOWER EASTERN SHORE', 
                'UPPER EASTERN SHORE', 'NORTH CENTRAL']
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in districts]
    
    df_plot = data['long'].copy()
    df_plot = df_plot[df_plot['District'].isin(districts)]
    
    bp_data = [df_plot[df_plot['District']==d]['Yield'].values for d in districts]
    bp = ax.boxplot(bp_data, labels=districts, patch_artist=True, widths=0.6)
    
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor('black')
        patch.set_linewidth(1.5)
    
    ax.set_title('Soybean Yield Distribution by District (1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=13)
    ax.grid(axis='y', alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=15, ha='right')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_District_Yield_Distribution.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 04_District_Yield_Distribution.png")
    plt.close()


def plot_5_top_counties_time_series(data, output_dir):
    """Plot 5: Top performing counties over time."""
    print("\n📊 Plot 5: Top counties time series...")
    
    # Get top 10 counties by average yield
    top10 = data['summary'].nlargest(10, 'Yield_mean')['County'].tolist()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for county in top10:
        county_data = data['long'][data['long']['County'] == county]
        district = county_data['District'].iloc[0] if len(county_data) > 0 else None
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax.plot(county_data['Year'], county_data['Yield'], 
               marker='o', linewidth=2, markersize=6, label=county, 
               color=color, alpha=0.75)
    
    ax.set_title('Top 10 Highest-Yielding Counties (1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=13)
    ax.legend(loc='upper left', ncol=2, fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_Top_Counties_Time_Series.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 05_Top_Counties_Time_Series.png")
    plt.close()


def plot_6_yield_variability_cv(data, output_dir):
    """Plot 6: Coefficient of variation trends."""
    print("\n📊 Plot 6: Yield variability (CV) trends...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # District-level CV over time
    for district in sorted(data['district_avg']['District'].unique()):
        district_data = data['district_avg'][data['district_avg']['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax1.plot(district_data['Year'], district_data['CV_mean'], 
                marker='o', linewidth=2, markersize=7, label=district, 
                color=color, alpha=0.85)
    
    ax1.set_title('Yield Coefficient of Variation by District', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Average CV (%)', fontsize=12)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # County-level CV comparison
    summary_sorted = data['summary'].sort_values('CV_mean')
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in summary_sorted['District']]
    
    ax2.barh(range(len(summary_sorted)), summary_sorted['CV_mean'], 
            color=colors, edgecolor='black', linewidth=0.5, alpha=0.8)
    ax2.set_yticks(range(len(summary_sorted)))
    ax2.set_yticklabels(summary_sorted['County'], fontsize=9)
    ax2.set_title('Average Yield Variability by County (1997-2024)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Average CV (%)', fontsize=12)
    ax2.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/06_Yield_Variability_CV.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 06_Yield_Variability_CV.png")
    plt.close()


def plot_7_year_to_year_change(data, output_dir):
    """Plot 7: Year-over-year yield changes."""
    print("\n📊 Plot 7: Year-to-year changes...")
    
    df = data['long'].copy()
    df = df.sort_values(['County', 'Year'])
    df['Yield_Change'] = df.groupby('County')['Yield'].diff()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # District averages
    district_changes = df.groupby(['District', 'Year'])['Yield_Change'].mean().reset_index()
    
    for district in sorted(district_changes['District'].dropna().unique()):
        dist_data = district_changes[district_changes['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax1.plot(dist_data['Year'], dist_data['Yield_Change'], 
                marker='o', linewidth=2, markersize=7, label=district, 
                color=color, alpha=0.85)
    
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_title('Year-over-Year Yield Change by District', fontsize=15, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Yield Change (Bu/Acre)', fontsize=12)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Histogram of all changes
    ax2.hist(df['Yield_Change'].dropna(), bins=40, edgecolor='black', 
            alpha=0.7, color='steelblue')
    ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='No change')
    ax2.axvline(x=df['Yield_Change'].median(), color='orange', linestyle='--', 
               linewidth=2, label=f'Median: {df["Yield_Change"].median():.1f}')
    ax2.set_title('Distribution of Year-over-Year Yield Changes', fontsize=15, fontweight='bold')
    ax2.set_xlabel('Yield Change (Bu/Acre)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/07_Year_to_Year_Changes.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 07_Year_to_Year_Changes.png")
    plt.close()


def plot_8_yield_trends_with_regression(data, output_dir):
    """Plot 8: Long-term trends with regression lines."""
    print("\n📊 Plot 8: Long-term trends with regression...")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for district in sorted(data['district_avg']['District'].unique()):
        district_data = data['district_avg'][data['district_avg']['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        
        # Scatter
        ax.scatter(district_data['Year'], district_data['Yield_mean'], 
                  s=80, color=color, alpha=0.6, edgecolors='black', linewidth=0.5)
        
        # Regression line
        if len(district_data) >= 2:
            z = np.polyfit(district_data['Year'], district_data['Yield_mean'], 1)
            p = np.poly1d(z)
            ax.plot(district_data['Year'], p(district_data['Year']), 
                   linestyle='--', linewidth=2.5, color=color, alpha=0.9,
                   label=f'{district} (slope: {z[0]:.2f} bu/yr)')
    
    ax.set_title('Long-Term Yield Trends by District with Linear Regression (1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Average Yield (Bu/Acre)', fontsize=13)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/08_Yield_Trends_With_Regression.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 08_Yield_Trends_With_Regression.png")
    plt.close()


def plot_9_county_rankings(data, output_dir):
    """Plot 9: County rankings for recent years."""
    print("\n📊 Plot 9: County rankings...")
    
    recent_years = [2020, 2021, 2022, 2023, 2024]
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for idx, year in enumerate(recent_years):
        ax = axes[idx]
        year_data = data['long'][data['long']['Year'] == year].copy()
        year_data = year_data.sort_values('Yield', ascending=True)
        
        colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in year_data['District']]
        
        ax.barh(range(len(year_data)), year_data['Yield'], 
               color=colors, edgecolor='black', linewidth=0.5, alpha=0.8)
        ax.set_yticks(range(len(year_data)))
        ax.set_yticklabels(year_data['County'], fontsize=8)
        ax.set_title(f'{year}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Yield (Bu/Acre)', fontsize=11)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (val, county) in enumerate(zip(year_data['Yield'], year_data['County'])):
            ax.text(val, i, f' {val:.1f}', va='center', fontsize=7)
    
    # Remove last empty subplot
    fig.delaxes(axes[5])
    
    plt.suptitle('County Yield Rankings (2020-2024)', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/09_County_Rankings_Recent_Years.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 09_County_Rankings_Recent_Years.png")
    plt.close()


def plot_10_yield_stability(data, output_dir):
    """Plot 10: Yield stability analysis (mean vs std)."""
    print("\n📊 Plot 10: Yield stability scatter...")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    summary = data['summary'].copy()
    
    for district in sorted(summary['District'].unique()):
        dist_data = summary[summary['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax.scatter(dist_data['Yield_mean'], dist_data['Yield_std'], 
                  s=120, color=color, alpha=0.7, edgecolors='black', 
                  linewidth=1, label=district)
        
        # Add county labels
        for _, row in dist_data.iterrows():
            ax.annotate(row['County'], 
                       xy=(row['Yield_mean'], row['Yield_std']),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.8)
    
    ax.set_title('Yield Stability Analysis: Mean vs Standard Deviation (1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Average Yield (Bu/Acre)', fontsize=13)
    ax.set_ylabel('Yield Standard Deviation (Bu/Acre)', fontsize=13)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Add interpretation regions
    median_yield = summary['Yield_mean'].median()
    median_std = summary['Yield_std'].median()
    ax.axvline(x=median_yield, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(y=median_std, color='gray', linestyle=':', alpha=0.5)
    
    ax.text(0.98, 0.98, 'High yield,\nHigh variability', transform=ax.transAxes,
           ha='right', va='top', fontsize=9, style='italic', alpha=0.6)
    ax.text(0.02, 0.98, 'Low yield,\nHigh variability', transform=ax.transAxes,
           ha='left', va='top', fontsize=9, style='italic', alpha=0.6)
    ax.text(0.98, 0.02, 'High yield,\nLow variability\n(Most stable)', transform=ax.transAxes,
           ha='right', va='bottom', fontsize=9, style='italic', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/10_Yield_Stability_Analysis.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 10_Yield_Stability_Analysis.png")
    plt.close()


def plot_11_decade_comparison(data, output_dir):
    """Plot 11: Yield comparison by decade."""
    print("\n📊 Plot 11: Decade comparison...")
    
    df = data['long'].copy()
    df['Decade'] = (df['Year'] // 10) * 10
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    decades = sorted(df['Decade'].unique())
    districts = ['WESTERN', 'SOUTHERN', 'LOWER EASTERN SHORE', 
                'UPPER EASTERN SHORE', 'NORTH CENTRAL']
    
    x = np.arange(len(decades))
    width = 0.17
    
    for idx, district in enumerate(districts):
        dist_data = df[df['District'] == district]
        decade_means = [dist_data[dist_data['Decade']==d]['Yield'].mean() 
                       for d in decades]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        offset = width * (idx - len(districts)/2)
        ax.bar(x + offset, decade_means, width, label=district, 
              color=color, edgecolor='black', linewidth=0.7, alpha=0.85)
    
    ax.set_xlabel('Decade', fontsize=13)
    ax.set_ylabel('Average Yield (Bu/Acre)', fontsize=13)
    ax.set_title('Average Soybean Yield by District and Decade', 
                fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{d}s' for d in decades])
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/11_Yield_By_Decade.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 11_Yield_By_Decade.png")
    plt.close()


def plot_12_best_worst_years(data, output_dir):
    """Plot 12: Best and worst years analysis."""
    print("\n📊 Plot 12: Best vs worst years...")
    
    # Calculate statewide average by year
    yearly_avg = data['long'].groupby('Year')['Yield'].mean().reset_index()
    yearly_avg = yearly_avg.sort_values('Yield')
    
    best_5 = yearly_avg.tail(5)['Year'].tolist()
    worst_5 = yearly_avg.head(5)['Year'].tolist()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Worst years
    worst_data = data['long'][data['long']['Year'].isin(worst_5)]
    worst_by_dist = worst_data.groupby(['District', 'Year'])['Yield'].mean().reset_index()
    
    for district in sorted(worst_by_dist['District'].unique()):
        dist_data = worst_by_dist[worst_by_dist['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax1.plot(dist_data['Year'], dist_data['Yield'], 
                marker='o', linewidth=2.5, markersize=10, label=district, 
                color=color, alpha=0.85)
    
    ax1.set_title('5 Lowest-Yielding Years (Statewide)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Average Yield (Bu/Acre)', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Best years
    best_data = data['long'][data['long']['Year'].isin(best_5)]
    best_by_dist = best_data.groupby(['District', 'Year'])['Yield'].mean().reset_index()
    
    for district in sorted(best_by_dist['District'].unique()):
        dist_data = best_by_dist[best_by_dist['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax2.plot(dist_data['Year'], dist_data['Yield'], 
                marker='o', linewidth=2.5, markersize=10, label=district, 
                color=color, alpha=0.85)
    
    ax2.set_title('5 Highest-Yielding Years (Statewide)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Average Yield (Bu/Acre)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/12_Best_Worst_Years.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 12_Best_Worst_Years.png")
    plt.close()


def plot_13_county_correlation_matrix(data, output_dir):
    """Plot 13: Inter-county yield correlation."""
    print("\n📊 Plot 13: County correlation matrix...")
    
    # Use wide format for correlation
    wide = data['wide_county'].copy()
    
    # Only include counties with sufficient data
    wide = wide.dropna(thresh=15, axis=0)  # At least 15 years of data
    
    corr = wide.T.corr()
    
    fig, ax = plt.subplots(figsize=(14, 12))
    
    sns.heatmap(corr, cmap='coolwarm', center=0, annot=False, 
               fmt='.2f', cbar_kws={'label': 'Correlation Coefficient'},
               linewidths=0.5, ax=ax, vmin=-1, vmax=1)
    
    ax.set_title('Inter-County Yield Correlation Matrix\n(How similarly do counties\' yields move together?)', 
                fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/13_County_Correlation_Matrix.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 13_County_Correlation_Matrix.png")
    plt.close()


def plot_14_data_coverage(data, output_dir):
    """Plot 14: Data availability/coverage visualization."""
    print("\n📊 Plot 14: Data coverage matrix...")
    
    df = data['long'].copy()
    
    # Create presence matrix
    coverage = df.pivot_table(index='County', columns='Year', 
                              values='Yield', aggfunc=lambda x: 1)
    coverage = coverage.fillna(0)
    
    # Sort by district
    summary = data['summary'].set_index('County')
    coverage = coverage.join(summary[['District']])
    coverage = coverage.sort_values('District')
    district_col = coverage['District']
    coverage = coverage.drop('District', axis=1)
    
    fig, ax = plt.subplots(figsize=(18, 10))
    
    sns.heatmap(coverage, cmap=['white', 'darkgreen'], cbar=False,
               linewidths=0.5, ax=ax, linecolor='gray')
    
    ax.set_title('Data Coverage by County and Year (1997-2024)\nGreen = Data Available, White = Missing', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('County', fontsize=13)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/14_Data_Coverage_Matrix.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 14_Data_Coverage_Matrix.png")
    plt.close()


def plot_15_census_year_comparison(data, output_dir):
    """Plot 15: Census year snapshots for irrigation correlation."""
    print("\n📊 Plot 15: Census year snapshots...")
    
    census = data['census'].copy()
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    census_years = sorted(census['Year'].unique())
    
    for idx, year in enumerate(census_years):
        ax = axes[idx]
        year_data = census[census['Year'] == year].copy()
        year_data = year_data.sort_values('Yield', ascending=False)
        
        colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in year_data['District']]
        
        bars = ax.bar(range(len(year_data)), year_data['Yield'], 
                     color=colors, edgecolor='black', linewidth=0.8, alpha=0.85)
        ax.set_title(f'{year} Census', fontsize=13, fontweight='bold')
        ax.set_ylabel('Yield (Bu/Acre)', fontsize=11)
        ax.set_xticks(range(len(year_data)))
        ax.set_xticklabels(year_data['County'], rotation=45, ha='right', fontsize=8)
        ax.grid(axis='y', alpha=0.3)
        
        # Add mean line
        mean_val = year_data['Yield'].mean()
        ax.axhline(y=mean_val, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    
    plt.suptitle('Census Year Yield Snapshots (for Irrigation Analysis)', 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/15_Census_Year_Snapshots.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 15_Census_Year_Snapshots.png")
    plt.close()


def plot_16_yield_range_by_county(data, output_dir):
    """Plot 16: Min-max yield ranges by county."""
    print("\n📊 Plot 16: Yield ranges by county...")
    
    summary = data['summary'].copy()
    summary = summary.sort_values('Yield_mean')
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in summary['District']]
    
    # Plot ranges
    for idx, row in enumerate(summary.itertuples()):
        color = colors[idx]
        ax.barh(idx, row.Yield_max - row.Yield_min, left=row.Yield_min,
               height=0.6, color=color, alpha=0.4, edgecolor='black', linewidth=0.5)
        ax.scatter(row.Yield_mean, idx, s=100, color=color, 
                  edgecolors='black', linewidth=1.5, zorder=3, alpha=0.95)
    
    ax.set_yticks(range(len(summary)))
    ax.set_yticklabels(summary['County'], fontsize=10)
    ax.set_xlabel('Yield (Bu/Acre)', fontsize=13)
    ax.set_title('Yield Ranges by County (1997-2024)\nBars show min-max range, dots show mean', 
                fontsize=16, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Legend
    legend_elements = [plt.Rectangle((0,0),1,1, fc=color, ec='black', alpha=0.7, label=district) 
                      for district, color in UNIVERSAL_DISTRICT_COLORS.items()]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/16_Yield_Ranges_By_County.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 16_Yield_Ranges_By_County.png")
    plt.close()


def plot_17_recent_vs_historical(data, output_dir):
    """Plot 17: Recent period vs historical comparison."""
    print("\n📊 Plot 17: Recent vs historical periods...")
    
    df = data['long'].copy()
    df['Period'] = df['Year'].apply(lambda y: 'Recent (2014-2024)' if y >= 2014 else 'Historical (1997-2013)')
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # Box plots by district
    districts = ['WESTERN', 'SOUTHERN', 'LOWER EASTERN SHORE', 
                'UPPER EASTERN SHORE', 'NORTH CENTRAL']
    
    for ax_idx, period in enumerate(['Historical (1997-2013)', 'Recent (2014-2024)']):
        ax = axes[ax_idx]
        period_data = df[df['Period'] == period]
        
        bp_data = [period_data[period_data['District']==d]['Yield'].values for d in districts]
        colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in districts]
        
        bp = ax.boxplot(bp_data, labels=districts, patch_artist=True, widths=0.6)
        
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
            patch.set_edgecolor('black')
            patch.set_linewidth(1.5)
        
        ax.set_title(period, fontsize=13, fontweight='bold')
        ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=15, ha='right')
    
    plt.suptitle('Yield Distribution Comparison: Historical vs Recent Period', 
                fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/17_Historical_vs_Recent_Comparison.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 17_Historical_vs_Recent_Comparison.png")
    plt.close()


def plot_18_yield_gap_analysis(data, output_dir):
    """Plot 18: Yield gap between top and bottom performers."""
    print("\n📊 Plot 18: Yield gap analysis...")
    
    df = data['long'].copy()
    
    # Calculate top and bottom quintiles by year
    gaps = []
    for year in sorted(df['Year'].unique()):
        year_data = df[df['Year'] == year]
        if len(year_data) >= 5:
            top20 = year_data.nlargest(int(len(year_data)*0.2), 'Yield')['Yield'].mean()
            bottom20 = year_data.nsmallest(int(len(year_data)*0.2), 'Yield')['Yield'].mean()
            gap = top20 - bottom20
            gaps.append({'Year': year, 'Gap': gap, 'Top20': top20, 'Bottom20': bottom20})
    
    gap_df = pd.DataFrame(gaps)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Gap over time
    ax1.fill_between(gap_df['Year'], 0, gap_df['Gap'], 
                    color='coral', alpha=0.6, edgecolor='black', linewidth=1)
    ax1.plot(gap_df['Year'], gap_df['Gap'], 
            marker='o', linewidth=2, markersize=7, color='darkred', alpha=0.9)
    ax1.set_title('Yield Gap Between Top and Bottom 20% of Counties (1997-2024)', 
                fontsize=15, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Yield Gap (Bu/Acre)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Top vs bottom trends
    ax2.plot(gap_df['Year'], gap_df['Top20'], marker='o', linewidth=2.5, 
            markersize=8, label='Top 20% Counties', color='darkgreen', alpha=0.85)
    ax2.plot(gap_df['Year'], gap_df['Bottom20'], marker='o', linewidth=2.5, 
            markersize=8, label='Bottom 20% Counties', color='darkred', alpha=0.85)
    ax2.fill_between(gap_df['Year'], gap_df['Bottom20'], gap_df['Top20'],
                    color='gray', alpha=0.2)
    ax2.set_title('Top vs Bottom Performers Over Time', fontsize=15, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Average Yield (Bu/Acre)', fontsize=12)
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/18_Yield_Gap_Analysis.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 18_Yield_Gap_Analysis.png")
    plt.close()


def plot_19_county_facets(data, output_dir):
    """Plot 19: Small multiples showing each county's trajectory."""
    print("\n📊 Plot 19: County trajectory facets...")
    
    df = data['long'].copy()
    
    # Get counties with most data
    good_counties = data['quality'][data['quality']['Years_Available'] >= 20].sort_values('Avg_Yield', ascending=False)['County'].tolist()
    
    if len(good_counties) > 20:
        good_counties = good_counties[:20]
    
    n_counties = len(good_counties)
    n_cols = 4
    n_rows = int(np.ceil(n_counties / n_cols))
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, n_rows*3))
    axes = axes.flatten()
    
    for idx, county in enumerate(good_counties):
        ax = axes[idx]
        county_data = df[df['County'] == county]
        district = county_data['District'].iloc[0]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        
        ax.plot(county_data['Year'], county_data['Yield'], 
               marker='o', linewidth=2, markersize=5, color=color, alpha=0.7)
        
        # Add trend line
        if len(county_data) >= 5:
            z = np.polyfit(county_data['Year'], county_data['Yield'], 1)
            p = np.poly1d(z)
            ax.plot(county_data['Year'], p(county_data['Year']), 
                   linestyle='--', linewidth=1.5, color=color, alpha=0.9)
        
        ax.set_title(f'{county} ({district[:15]})', fontsize=10, fontweight='bold')
        ax.set_ylabel('Yield', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=8)
    
    # Remove empty subplots
    for idx in range(n_counties, len(axes)):
        fig.delaxes(axes[idx])
    
    plt.suptitle('Individual County Yield Trajectories (1997-2024)', 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/19_County_Trajectory_Facets.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 19_County_Trajectory_Facets.png")
    plt.close()


def plot_20_yield_distribution_evolution(data, output_dir):
    """Plot 20: How yield distribution has changed over time."""
    print("\n📊 Plot 20: Yield distribution evolution...")
    
    df = data['long'].copy()
    
    # Select snapshots every 5 years
    snapshot_years = [1997, 2002, 2007, 2012, 2017, 2022]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for year in snapshot_years:
        year_data = df[df['Year'] == year]['Yield'].dropna()
        ax.hist(year_data, bins=15, alpha=0.5, label=str(year), edgecolor='black', linewidth=0.5)
    
    ax.set_title('Evolution of Yield Distribution Across Census Years', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Yield (Bu/Acre)', fontsize=13)
    ax.set_ylabel('Number of Counties', fontsize=13)
    ax.legend(loc='upper left', fontsize=11, title='Census Year')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/20_Yield_Distribution_Evolution.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: 20_Yield_Distribution_Evolution.png")
    plt.close()


def main():
    """Generate all yield visualization plots."""
    print("=" * 80)
    print("COMPREHENSIVE YIELD VISUALIZATION SUITE")
    print("=" * 80)
    
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    data = load_datasets()
    
    plot_1_district_time_series(data, output_dir)
    plot_2_county_heatmap(data, output_dir)
    plot_2b_county_heatmap_2012plus(data, output_dir)
    plot_3_district_heatmap(data, output_dir)
    plot_4_box_plots_by_district(data, output_dir)
    plot_5_top_counties_time_series(data, output_dir)
    plot_6_yield_variability_cv(data, output_dir)
    plot_7_year_to_year_change(data, output_dir)
    plot_8_yield_trends_with_regression(data, output_dir)
    plot_9_county_rankings(data, output_dir)
    plot_10_yield_stability(data, output_dir)
    plot_11_decade_comparison(data, output_dir)
    plot_12_best_worst_years(data, output_dir)
    plot_13_county_correlation_matrix(data, output_dir)
    plot_14_data_coverage(data, output_dir)
    plot_15_census_year_comparison(data, output_dir)
    plot_16_yield_range_by_county(data, output_dir)
    plot_17_recent_vs_historical(data, output_dir)
    plot_18_yield_gap_analysis(data, output_dir)
    plot_19_county_facets(data, output_dir)
    plot_20_yield_distribution_evolution(data, output_dir)
    
    print("\n" + "=" * 80)
    print(f"✅ Generated 21 comprehensive yield plots!")
    print(f"📁 Output directory: {output_dir}/")
    print("=" * 80)


if __name__ == "__main__":
    main()

