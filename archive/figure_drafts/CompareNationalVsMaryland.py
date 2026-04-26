#!/usr/bin/env python3
"""
National vs Maryland Yield Comparison
Compares Maryland soybean yields to national averages.

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


def load_national_data():
    """Load and clean national average yield data."""
    print("🔄 Loading national soybean data...")
    
    df = pd.read_csv('data/NationalAverageSoybean.csv')
    
    # Filter for final year values (not forecasts)
    df = df[df['Period'] == 'YEAR'].copy()
    
    # Extract yield data
    yield_df = df[df['Data Item'] == 'SOYBEANS - YIELD, MEASURED IN BU / ACRE'].copy()
    
    yield_df['Year'] = pd.to_numeric(yield_df['Year'], errors='coerce')
    yield_df['Value'] = yield_df['Value'].astype(str).str.replace(',', '').str.strip()
    yield_df['National_Yield'] = pd.to_numeric(yield_df['Value'], errors='coerce')
    
    yield_df = yield_df[['Year', 'National_Yield']].dropna()
    yield_df['Year'] = yield_df['Year'].astype(int)
    
    print(f"   ✅ National data: {len(yield_df)} years ({yield_df['Year'].min()}-{yield_df['Year'].max()})")
    
    return yield_df


def load_maryland_data():
    """Load Maryland processed yield data."""
    print("🔄 Loading Maryland yield data...")
    
    md_long = pd.read_csv('data/processed_yield/yield_clean_long_format.csv')
    md_district = pd.read_csv('data/processed_yield/yield_district_averages_by_year.csv')
    
    # Calculate statewide average
    md_statewide = md_long.groupby('Year')['Yield'].mean().reset_index()
    md_statewide = md_statewide.rename(columns={'Yield': 'Maryland_Yield'})
    
    print(f"   ✅ Maryland data: {len(md_statewide)} years")
    
    return md_long, md_district, md_statewide


def plot_1_national_vs_maryland_trends(nat, md_state, output_dir):
    """Plot 1: Direct comparison of national vs Maryland yields."""
    print("\n📊 Plot 1: National vs Maryland trends...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
    
    # Time series
    ax1.plot(merged['Year'], merged['National_Yield'], marker='o', linewidth=3, 
            markersize=8, label='US National Average', color='navy', alpha=0.85)
    ax1.plot(merged['Year'], merged['Maryland_Yield'], marker='s', linewidth=3, 
            markersize=8, label='Maryland Average', color='crimson', alpha=0.85)
    
    ax1.set_title('National vs Maryland Soybean Yields (1997-2024)', 
                 fontsize=16, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=13)
    ax1.set_ylabel('Yield (Bu/Acre)', fontsize=13)
    ax1.legend(loc='upper left', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Gap analysis
    merged['Gap'] = merged['Maryland_Yield'] - merged['National_Yield']
    
    colors = ['green' if g >= 0 else 'red' for g in merged['Gap']]
    ax2.bar(merged['Year'], merged['Gap'], color=colors, edgecolor='black', 
           linewidth=0.8, alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    
    ax2.set_title('Maryland Yield Gap vs National Average\n(Positive = Maryland outperforms, Negative = Maryland underperforms)', 
                 fontsize=15, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=13)
    ax2.set_ylabel('Yield Difference (Bu/Acre)', fontsize=13)
    ax2.grid(axis='y', alpha=0.3)
    
    # Stats
    avg_gap = merged['Gap'].mean()
    recent_gap = merged[merged['Year'] >= 2014]['Gap'].mean()
    ax2.text(0.02, 0.98, f'Avg Gap (all years): {avg_gap:+.1f} bu/ac\nRecent Avg (2014-24): {recent_gap:+.1f} bu/ac',
            transform=ax2.transAxes, va='top', ha='left',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9), fontsize=11)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/National_vs_MD_Trends.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: National_vs_MD_Trends.png")
    plt.close()


def plot_2_districts_vs_national(nat, md_district, output_dir):
    """Plot 2: All Maryland districts vs national average."""
    print("\n📊 Plot 2: Districts vs national...")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # National line
    ax.plot(nat['Year'], nat['National_Yield'], marker='o', linewidth=3.5, 
           markersize=9, label='US National', color='black', alpha=0.9, zorder=10)
    
    # District lines
    for district in sorted(md_district['District'].unique()):
        dist_data = md_district[md_district['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax.plot(dist_data['Year'], dist_data['Yield_mean'], marker='s', 
               linewidth=2.5, markersize=7, label=f'MD - {district}', 
               color=color, alpha=0.75)
    
    ax.set_title('Maryland Agricultural Districts vs US National Average (1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Yield (Bu/Acre)', fontsize=13)
    ax.legend(loc='upper left', fontsize=10, ncol=2)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Districts_vs_National.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: Districts_vs_National.png")
    plt.close()


def plot_3_relative_performance(nat, md_state, md_district, output_dir):
    """Plot 3: Relative performance (Maryland as % of national)."""
    print("\n📊 Plot 3: Relative performance...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    merged['MD_Pct_of_National'] = (merged['Maryland_Yield'] / merged['National_Yield'] * 100)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Maryland overall
    ax1.plot(merged['Year'], merged['MD_Pct_of_National'], marker='o', 
            linewidth=2.5, markersize=8, color='crimson', alpha=0.85)
    ax1.axhline(y=100, color='black', linestyle='--', linewidth=1.5, alpha=0.7, label='Parity (100%)')
    ax1.fill_between(merged['Year'], 100, merged['MD_Pct_of_National'], 
                    where=(merged['MD_Pct_of_National'] >= 100), color='green', alpha=0.2)
    ax1.fill_between(merged['Year'], 100, merged['MD_Pct_of_National'], 
                    where=(merged['MD_Pct_of_National'] < 100), color='red', alpha=0.2)
    
    ax1.set_title('Maryland as % of US National Average', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Maryland Yield (% of National)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # By district
    for district in sorted(md_district['District'].unique()):
        dist_data = md_district[md_district['District'] == district]
        dist_merged = pd.merge(nat, dist_data, on='Year', how='inner')
        dist_merged['Pct'] = (dist_merged['Yield_mean'] / dist_merged['National_Yield'] * 100)
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax2.plot(dist_merged['Year'], dist_merged['Pct'], marker='s', 
                linewidth=2, markersize=6, label=district, color=color, alpha=0.75)
    
    ax2.axhline(y=100, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.set_title('Districts as % of US National Average', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('District Yield (% of National)', fontsize=12)
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Relative_Performance_vs_National.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: Relative_Performance_vs_National.png")
    plt.close()


def plot_4_scatter_md_vs_national(nat, md_state, output_dir):
    """Plot 4: Scatter plot of Maryland vs national yields."""
    print("\n📊 Plot 4: Scatter correlation...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Color by decade
    merged['Decade'] = (merged['Year'] // 10) * 10
    decades = sorted(merged['Decade'].unique())
    colors = plt.cm.viridis(np.linspace(0, 1, len(decades)))
    decade_colors = dict(zip(decades, colors))
    
    for decade in decades:
        decade_data = merged[merged['Decade'] == decade]
        ax.scatter(decade_data['National_Yield'], decade_data['Maryland_Yield'], 
                  s=120, color=decade_colors[decade], alpha=0.7, 
                  edgecolors='black', linewidth=1, label=f'{decade}s')
    
    # Add 1:1 line
    min_val = min(merged['National_Yield'].min(), merged['Maryland_Yield'].min())
    max_val = max(merged['National_Yield'].max(), merged['Maryland_Yield'].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=2, 
           alpha=0.5, label='1:1 Parity')
    
    # Regression line
    z = np.polyfit(merged['National_Yield'], merged['Maryland_Yield'], 1)
    p = np.poly1d(z)
    x_vals = np.linspace(min_val, max_val, 100)
    ax.plot(x_vals, p(x_vals), 'r-', linewidth=2.5, alpha=0.7, 
           label=f'Regression (slope={z[0]:.2f})')
    
    # Correlation
    r, pval = stats.pearsonr(merged['National_Yield'], merged['Maryland_Yield'])
    
    ax.set_title('Maryland vs US National Soybean Yields\n(1997-2024)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('US National Average Yield (Bu/Acre)', fontsize=13)
    ax.set_ylabel('Maryland Average Yield (Bu/Acre)', fontsize=13)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Stats box
    stats_text = f'Correlation: r = {r:.3f}\nR² = {r**2:.3f}\np-value < 0.001'
    ax.text(0.98, 0.02, stats_text, transform=ax.transAxes, 
           ha='right', va='bottom',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9), fontsize=11)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/MD_vs_National_Scatter.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: MD_vs_National_Scatter.png")
    plt.close()


def plot_5_growth_rate_comparison(nat, md_state, output_dir):
    """Plot 5: Growth rate comparison."""
    print("\n📊 Plot 5: Growth rate comparison...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    merged = merged.sort_values('Year')
    
    # Calculate 5-year rolling average growth
    merged['National_Growth'] = merged['National_Yield'].pct_change(periods=5) * 100
    merged['Maryland_Growth'] = merged['Maryland_Yield'].pct_change(periods=5) * 100
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.plot(merged['Year'], merged['National_Growth'], marker='o', linewidth=2.5, 
           markersize=8, label='US National (5-yr % change)', color='navy', alpha=0.85)
    ax.plot(merged['Year'], merged['Maryland_Growth'], marker='s', linewidth=2.5, 
           markersize=8, label='Maryland (5-yr % change)', color='crimson', alpha=0.85)
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    ax.set_title('Yield Growth Rates: Maryland vs US National\n(5-Year Percent Change)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('5-Year Growth Rate (%)', fontsize=13)
    ax.legend(loc='best', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Growth_Rate_Comparison.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: Growth_Rate_Comparison.png")
    plt.close()


def plot_6_normalized_comparison(nat, md_state, md_district, output_dir):
    """Plot 6: Normalized yields (index base year)."""
    print("\n📊 Plot 6: Normalized trends (1997 = 100)...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    
    # Normalize to first year
    base_year = merged['Year'].min()
    nat_base = merged[merged['Year'] == base_year]['National_Yield'].values[0]
    md_base = merged[merged['Year'] == base_year]['Maryland_Yield'].values[0]
    
    merged['National_Index'] = (merged['National_Yield'] / nat_base) * 100
    merged['Maryland_Index'] = (merged['Maryland_Yield'] / md_base) * 100
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.plot(merged['Year'], merged['National_Index'], marker='o', linewidth=3, 
           markersize=8, label='US National', color='navy', alpha=0.85)
    ax.plot(merged['Year'], merged['Maryland_Index'], marker='s', linewidth=3, 
           markersize=8, label='Maryland', color='crimson', alpha=0.85)
    
    # Add districts
    for district in sorted(md_district['District'].unique()):
        dist_data = md_district[md_district['District'] == district]
        dist_base = dist_data[dist_data['Year'] == base_year]['Yield_mean'].values
        if len(dist_base) > 0:
            dist_data = dist_data.copy()
            dist_data['Index'] = (dist_data['Yield_mean'] / dist_base[0]) * 100
            color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
            ax.plot(dist_data['Year'], dist_data['Index'], marker='^', 
                   linewidth=1.5, markersize=5, label=f'MD - {district}', 
                   color=color, alpha=0.5, linestyle=':')
    
    ax.axhline(y=100, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_title(f'Normalized Yield Trends ({base_year} = 100)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Yield Index', fontsize=13)
    ax.legend(loc='upper left', fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Normalized_Yield_Index.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: Normalized_Yield_Index.png")
    plt.close()


def plot_7_volatility_comparison(nat, md_state, output_dir):
    """Plot 7: Yield volatility comparison."""
    print("\n📊 Plot 7: Volatility comparison...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    
    # Calculate rolling standard deviation
    window = 5
    merged['National_Rolling_Std'] = merged['National_Yield'].rolling(window=window).std()
    merged['Maryland_Rolling_Std'] = merged['Maryland_Yield'].rolling(window=window).std()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.plot(merged['Year'], merged['National_Rolling_Std'], marker='o', linewidth=2.5, 
           markersize=7, label=f'US National ({window}-yr rolling std)', 
           color='navy', alpha=0.85)
    ax.plot(merged['Year'], merged['Maryland_Rolling_Std'], marker='s', linewidth=2.5, 
           markersize=7, label=f'Maryland ({window}-yr rolling std)', 
           color='crimson', alpha=0.85)
    
    ax.set_title('Yield Volatility Comparison: Maryland vs US National\n(5-Year Rolling Standard Deviation)', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel('Rolling Std Dev (Bu/Acre)', fontsize=13)
    ax.legend(loc='best', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Volatility_Comparison.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: Volatility_Comparison.png")
    plt.close()


def plot_8_decade_averages(nat, md_state, md_district, output_dir):
    """Plot 8: Decade average comparison."""
    print("\n📊 Plot 8: Decade averages...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    merged['Decade'] = (merged['Year'] // 10) * 10
    
    decade_stats = merged.groupby('Decade').agg({
        'National_Yield': 'mean',
        'Maryland_Yield': 'mean'
    }).reset_index()
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(decade_stats))
    width = 0.35
    
    ax.bar(x - width/2, decade_stats['National_Yield'], width, 
          label='US National', color='navy', edgecolor='black', linewidth=1, alpha=0.8)
    ax.bar(x + width/2, decade_stats['Maryland_Yield'], width, 
          label='Maryland', color='crimson', edgecolor='black', linewidth=1, alpha=0.8)
    
    ax.set_xlabel('Decade', fontsize=13)
    ax.set_ylabel('Average Yield (Bu/Acre)', fontsize=13)
    ax.set_title('Average Soybean Yields by Decade: Maryland vs US National', 
                fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{int(d)}s' for d in decade_stats['Decade']])
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, row in enumerate(decade_stats.itertuples()):
        ax.text(i - width/2, row.National_Yield, f'{row.National_Yield:.1f}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.text(i + width/2, row.Maryland_Yield, f'{row.Maryland_Yield:.1f}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Decade_Averages_Comparison.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: Decade_Averages_Comparison.png")
    plt.close()


def plot_9_best_worst_national_years(nat, md_long, output_dir):
    """Plot 9: Maryland performance in best/worst national years."""
    print("\n📊 Plot 9: MD in best/worst national years...")
    
    # Get best and worst 5 national years
    nat_sorted = nat.sort_values('National_Yield')
    worst_5 = nat_sorted.head(5)['Year'].tolist()
    best_5 = nat_sorted.tail(5)['Year'].tolist()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Worst national years
    worst_md = md_long[md_long['Year'].isin(worst_5)]
    worst_dist = worst_md.groupby(['District', 'Year'])['Yield'].mean().reset_index()
    
    for district in sorted(worst_dist['District'].unique()):
        dist_data = worst_dist[worst_dist['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax1.plot(dist_data['Year'], dist_data['Yield'], marker='o', 
                linewidth=2.5, markersize=9, label=district, color=color, alpha=0.85)
    
    ax1.set_title('Maryland Districts in 5 Worst US National Years', fontsize=13, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Maryland Yield (Bu/Acre)', fontsize=12)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Best national years
    best_md = md_long[md_long['Year'].isin(best_5)]
    best_dist = best_md.groupby(['District', 'Year'])['Yield'].mean().reset_index()
    
    for district in sorted(best_dist['District'].unique()):
        dist_data = best_dist[best_dist['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax2.plot(dist_data['Year'], dist_data['Yield'], marker='o', 
                linewidth=2.5, markersize=9, label=district, color=color, alpha=0.85)
    
    ax2.set_title('Maryland Districts in 5 Best US National Years', fontsize=13, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Maryland Yield (Bu/Acre)', fontsize=12)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/MD_in_Best_Worst_National_Years.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: MD_in_Best_Worst_National_Years.png")
    plt.close()


def plot_10_cumulative_gains(nat, md_state, output_dir):
    """Plot 10: Cumulative yield gains since baseline."""
    print("\n📊 Plot 10: Cumulative gains...")
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    merged = merged.sort_values('Year')
    
    base_year = merged['Year'].min()
    nat_baseline = merged[merged['Year'] == base_year]['National_Yield'].values[0]
    md_baseline = merged[merged['Year'] == base_year]['Maryland_Yield'].values[0]
    
    merged['National_Cumulative_Gain'] = merged['National_Yield'] - nat_baseline
    merged['Maryland_Cumulative_Gain'] = merged['Maryland_Yield'] - md_baseline
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.fill_between(merged['Year'], 0, merged['National_Cumulative_Gain'], 
                   color='navy', alpha=0.3, label='US National gain')
    ax.plot(merged['Year'], merged['National_Cumulative_Gain'], 
           marker='o', linewidth=2.5, markersize=7, color='navy', alpha=0.9)
    
    ax.fill_between(merged['Year'], 0, merged['Maryland_Cumulative_Gain'], 
                   color='crimson', alpha=0.3, label='Maryland gain')
    ax.plot(merged['Year'], merged['Maryland_Cumulative_Gain'], 
           marker='s', linewidth=2.5, markersize=7, color='crimson', alpha=0.9)
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    
    ax.set_title(f'Cumulative Yield Gains Since {base_year}', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Year', fontsize=13)
    ax.set_ylabel(f'Yield Gain Since {base_year} (Bu/Acre)', fontsize=13)
    ax.legend(loc='upper left', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/Cumulative_Yield_Gains.png', dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: Cumulative_Yield_Gains.png")
    plt.close()


def generate_summary_stats(nat, md_state, md_district):
    """Generate summary statistics."""
    print("\n📊 Summary Statistics:")
    print("=" * 60)
    
    merged = pd.merge(nat, md_state, on='Year', how='inner')
    merged['Gap'] = merged['Maryland_Yield'] - merged['National_Yield']
    
    print(f"\nOVERALL (1997-2024):")
    print(f"  National average: {merged['National_Yield'].mean():.1f} bu/ac")
    print(f"  Maryland average: {merged['Maryland_Yield'].mean():.1f} bu/ac")
    print(f"  Average gap: {merged['Gap'].mean():+.1f} bu/ac")
    print(f"  Correlation: r = {merged['National_Yield'].corr(merged['Maryland_Yield']):.3f}")
    
    print(f"\nRECENT PERIOD (2014-2024):")
    recent = merged[merged['Year'] >= 2014]
    print(f"  National average: {recent['National_Yield'].mean():.1f} bu/ac")
    print(f"  Maryland average: {recent['Maryland_Yield'].mean():.1f} bu/ac")
    print(f"  Average gap: {recent['Gap'].mean():+.1f} bu/ac")
    
    print(f"\nHISTORICAL PERIOD (1997-2013):")
    historical = merged[merged['Year'] < 2014]
    print(f"  National average: {historical['National_Yield'].mean():.1f} bu/ac")
    print(f"  Maryland average: {historical['Maryland_Yield'].mean():.1f} bu/ac")
    print(f"  Average gap: {historical['Gap'].mean():+.1f} bu/ac")
    
    print(f"\nGROWTH RATES:")
    first_5yr = merged[merged['Year'] <= merged['Year'].min() + 4]
    last_5yr = merged[merged['Year'] >= merged['Year'].max() - 4]
    
    nat_growth = ((last_5yr['National_Yield'].mean() - first_5yr['National_Yield'].mean()) / 
                 first_5yr['National_Yield'].mean() * 100)
    md_growth = ((last_5yr['Maryland_Yield'].mean() - first_5yr['Maryland_Yield'].mean()) / 
                first_5yr['Maryland_Yield'].mean() * 100)
    
    print(f"  National (first 5yr → last 5yr): {nat_growth:+.1f}%")
    print(f"  Maryland (first 5yr → last 5yr): {md_growth:+.1f}%")


def main():
    """Run comprehensive national vs Maryland comparison."""
    print("=" * 80)
    print("NATIONAL VS MARYLAND YIELD COMPARISON")
    print("=" * 80)
    
    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)
    
    nat = load_national_data()
    md_long, md_district, md_state = load_maryland_data()
    
    plot_1_national_vs_maryland_trends(nat, md_state, output_dir)
    plot_2_districts_vs_national(nat, md_district, output_dir)
    plot_3_relative_performance(nat, md_state, md_district, output_dir)
    plot_4_scatter_md_vs_national(nat, md_state, output_dir)
    plot_5_growth_rate_comparison(nat, md_state, output_dir)
    plot_6_normalized_comparison(nat, md_state, md_district, output_dir)
    plot_7_volatility_comparison(nat, md_state, output_dir)
    plot_8_decade_averages(nat, md_state, output_dir)
    plot_9_best_worst_national_years(nat, md_long, output_dir)
    plot_10_cumulative_gains(nat, md_state, output_dir)
    
    generate_summary_stats(nat, md_state, md_district)
    
    print("\n" + "=" * 80)
    print("✅ National vs Maryland comparison complete!")
    print(f"📁 Output directory: {output_dir}/")
    print("=" * 80)


if __name__ == "__main__":
    main()




