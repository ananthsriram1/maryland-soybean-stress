#!/usr/bin/env python3
"""
Comprehensive Irrigation Analysis for Maryland Soybeans
Analyzes irrigation adoption, farm size, trends, and relationships with yield.

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


def load_irrigation_data():
    """Load and process irrigation data with acres and operations."""
    print("🔄 Loading comprehensive irrigation data...")
    
    df = pd.read_csv('data/nass/IrrigationvsNonirrigated.csv')
    
    # Clean values
    df['Value_str'] = df['Value'].astype(str)
    df['Is_Suppressed'] = df['Value_str'].str.contains(r'\(D\)|\(L\)', na=False)
    df['Value_clean'] = (
        df['Value_str']
        .str.replace(',', '', regex=False)
        .str.replace(r'\(D\)|\(L\)', '', regex=True)
        .str.strip()
    )
    df['Value_numeric'] = pd.to_numeric(df['Value_clean'], errors='coerce')
    
    # Separate acres and operations
    acres_df = df[df['Data Item'] == 'SOYBEANS, IRRIGATED - ACRES HARVESTED'].copy()
    ops_df = df[df['Data Item'] == 'SOYBEANS, IRRIGATED - OPERATIONS WITH AREA HARVESTED'].copy()
    
    # Merge
    acres_df = acres_df[['Year', 'Ag District', 'County', 'Value_numeric', 'Is_Suppressed']].rename(
        columns={'Value_numeric': 'Acres', 'Is_Suppressed': 'Acres_Suppressed'})
    ops_df = ops_df[['Year', 'County', 'Value_numeric', 'Is_Suppressed']].rename(
        columns={'Value_numeric': 'Operations', 'Is_Suppressed': 'Operations_Suppressed'})
    
    combined = pd.merge(acres_df, ops_df, on=['Year', 'County'], how='outer')
    
    # Clean district names
    combined['Ag District'] = combined['Ag District'].str.upper().str.strip()
    combined['County'] = combined['County'].str.title().str.strip()
    
    # Calculate average farm size
    combined['Avg_Farm_Size'] = combined['Acres'] / combined['Operations']
    
    print(f"   ✅ Loaded {len(combined)} records")
    print(f"   📅 Years: {sorted(combined['Year'].unique())}")
    print(f"   📍 Counties: {combined['County'].nunique()}")
    
    return combined


def analyze_irrigation_summary(df):
    """Print comprehensive irrigation statistics."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE IRRIGATION ANALYSIS")
    print("=" * 80)
    
    for year in sorted(df['Year'].unique()):
        year_data = df[df['Year'] == year]
        
        # Non-suppressed data
        valid_data = year_data[~year_data['Acres_Suppressed'] & ~year_data['Operations_Suppressed']]
        
        print(f"\n{'=' * 40}")
        print(f"CENSUS YEAR: {year}")
        print(f"{'=' * 40}")
        
        if len(valid_data) > 0:
            total_acres = valid_data['Acres'].sum()
            total_ops = valid_data['Operations'].sum()
            avg_size = total_acres / total_ops if total_ops > 0 else 0
            
            print(f"\n📊 STATEWIDE TOTALS (non-suppressed):")
            print(f"   Total irrigated acres: {total_acres:,.0f}")
            print(f"   Total operations: {total_ops:,.0f}")
            print(f"   Average farm size: {avg_size:.1f} acres/operation")
            
            print(f"\n🏛️  BY DISTRICT:")
            for district in sorted(valid_data['Ag District'].dropna().unique()):
                dist_data = valid_data[valid_data['Ag District'] == district]
                dist_acres = dist_data['Acres'].sum()
                dist_ops = dist_data['Operations'].sum()
                dist_avg = dist_acres / dist_ops if dist_ops > 0 else 0
                pct_acres = (dist_acres / total_acres * 100) if total_acres > 0 else 0
                
                print(f"   {district:25} | {dist_acres:>8,.0f} acres ({pct_acres:>5.1f}%) | {dist_ops:>4.0f} ops | {dist_avg:>6.1f} avg")
            
            print(f"\n📍 TOP 10 COUNTIES BY ACRES:")
            top_counties = valid_data.nlargest(10, 'Acres')[['County', 'Ag District', 'Acres', 'Operations', 'Avg_Farm_Size']]
            for idx, row in top_counties.iterrows():
                print(f"   {row['County']:15} ({row['Ag District']:20}) | {row['Acres']:>8,.0f} acres | {row['Operations']:>3.0f} ops | {row['Avg_Farm_Size']:>6.1f} avg")
            
            print(f"\n🌾 FARM SIZE DISTRIBUTION:")
            print(f"   Min farm size: {valid_data['Avg_Farm_Size'].min():.1f} acres")
            print(f"   Max farm size: {valid_data['Avg_Farm_Size'].max():.1f} acres")
            print(f"   Median farm size: {valid_data['Avg_Farm_Size'].median():.1f} acres")
            print(f"   Mean farm size: {valid_data['Avg_Farm_Size'].mean():.1f} acres")


def plot_operations_trends(df):
    """Plot number of operations (farms) using irrigation over time."""
    print("\n📊 Creating operations trends plot...")
    
    output_dir = 'outputs/Irrigation'
    os.makedirs(output_dir, exist_ok=True)
    
    valid_data = df[~df['Operations_Suppressed']].copy()
    
    # District totals
    district_ops = valid_data.groupby(['Ag District', 'Year'])['Operations'].sum().reset_index()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Line plot by district
    for district in sorted(district_ops['Ag District'].dropna().unique()):
        dist_data = district_ops[district_ops['Ag District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        ax1.plot(dist_data['Year'], dist_data['Operations'], marker='o', linewidth=2.5, 
                markersize=10, label=district, color=color, alpha=0.85)
    
    ax1.set_title('Number of Irrigating Operations by District', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Census Year', fontsize=12)
    ax1.set_ylabel('Number of Operations', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Stacked bar
    pivot = district_ops.pivot(index='Year', columns='Ag District', values='Operations').fillna(0)
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in pivot.columns]
    pivot.plot(kind='bar', stacked=True, ax=ax2, color=colors, edgecolor='black', linewidth=0.5)
    
    ax2.set_title('Total Irrigating Operations (Stacked)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Census Year', fontsize=12)
    ax2.set_ylabel('Number of Operations', fontsize=12)
    ax2.legend(title='District', loc='upper left', fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=0)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/Irrigation_Operations_Trends.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    plt.close()


def plot_farm_size_distribution(df):
    """Plot average farm size for irrigated operations."""
    print("\n📊 Creating farm size distribution plots...")
    
    output_dir = 'outputs/Irrigation'
    os.makedirs(output_dir, exist_ok=True)
    
    valid_data = df[~df['Acres_Suppressed'] & ~df['Operations_Suppressed'] & (df['Avg_Farm_Size'] > 0)].copy()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Box plot by district (latest year)
    latest_year = valid_data['Year'].max()
    latest_data = valid_data[valid_data['Year'] == latest_year]
    
    districts = sorted(latest_data['Ag District'].dropna().unique())
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in districts]
    
    bp = axes[0,0].boxplot([latest_data[latest_data['Ag District']==d]['Avg_Farm_Size'].values for d in districts],
                           labels=districts, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    axes[0,0].set_title(f'Farm Size Distribution by District ({latest_year})', fontsize=14, fontweight='bold')
    axes[0,0].set_ylabel('Avg Farm Size (acres/operation)', fontsize=11)
    axes[0,0].grid(axis='y', alpha=0.3)
    plt.setp(axes[0,0].xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 2: Time series of average farm size by district
    district_avg = valid_data.groupby(['Ag District', 'Year'])['Avg_Farm_Size'].mean().reset_index()
    
    for district in sorted(district_avg['Ag District'].unique()):
        dist_data = district_avg[district_avg['Ag District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
        axes[0,1].plot(dist_data['Year'], dist_data['Avg_Farm_Size'], marker='o', 
                      linewidth=2, markersize=8, label=district, color=color, alpha=0.85)
    
    axes[0,1].set_title('Average Irrigated Farm Size Over Time', fontsize=14, fontweight='bold')
    axes[0,1].set_xlabel('Census Year', fontsize=11)
    axes[0,1].set_ylabel('Avg Farm Size (acres/operation)', fontsize=11)
    axes[0,1].legend(loc='best', fontsize=9)
    axes[0,1].grid(True, alpha=0.3)
    
    # Plot 3: Histogram of farm sizes (all years)
    axes[1,0].hist(valid_data['Avg_Farm_Size'], bins=30, edgecolor='black', alpha=0.7, color='steelblue')
    axes[1,0].axvline(valid_data['Avg_Farm_Size'].median(), color='red', linestyle='--', 
                     linewidth=2, label=f'Median: {valid_data["Avg_Farm_Size"].median():.1f}')
    axes[1,0].axvline(valid_data['Avg_Farm_Size'].mean(), color='orange', linestyle='--', 
                     linewidth=2, label=f'Mean: {valid_data["Avg_Farm_Size"].mean():.1f}')
    axes[1,0].set_title('Distribution of Irrigated Farm Sizes (All Years)', fontsize=14, fontweight='bold')
    axes[1,0].set_xlabel('Avg Farm Size (acres/operation)', fontsize=11)
    axes[1,0].set_ylabel('Frequency', fontsize=11)
    axes[1,0].legend()
    axes[1,0].grid(axis='y', alpha=0.3)
    
    # Plot 4: Top counties by farm size (latest year)
    top_20 = latest_data.nlargest(20, 'Avg_Farm_Size')[['County', 'Ag District', 'Avg_Farm_Size']].sort_values('Avg_Farm_Size')
    colors_top = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in top_20['Ag District']]
    
    axes[1,1].barh(range(len(top_20)), top_20['Avg_Farm_Size'], color=colors_top, edgecolor='black', linewidth=0.5)
    axes[1,1].set_yticks(range(len(top_20)))
    axes[1,1].set_yticklabels(top_20['County'], fontsize=8)
    axes[1,1].set_title(f'Top 20 Counties by Avg Irrigated Farm Size ({latest_year})', fontsize=14, fontweight='bold')
    axes[1,1].set_xlabel('Avg Farm Size (acres/operation)', fontsize=11)
    axes[1,1].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    filename = f'{output_dir}/Irrigation_Farm_Size_Analysis.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    plt.close()


def plot_concentration_analysis(df):
    """Analyze concentration of irrigation in few large operations."""
    print("\n📊 Creating concentration analysis...")
    
    output_dir = 'outputs/Irrigation'
    os.makedirs(output_dir, exist_ok=True)
    
    valid_data = df[~df['Acres_Suppressed'] & ~df['Operations_Suppressed']].copy()
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    years = sorted(valid_data['Year'].unique())
    
    for idx, year in enumerate(years):
        ax = axes[idx]
        year_data = valid_data[valid_data['Year'] == year].copy()
        year_data = year_data.sort_values('Acres', ascending=False).reset_index(drop=True)
        year_data['Cumulative_Pct'] = (year_data['Acres'].cumsum() / year_data['Acres'].sum() * 100)
        year_data['County_Pct'] = ((year_data.index + 1) / len(year_data) * 100)
        
        # Color by district
        colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#808080') for d in year_data['Ag District']]
        
        ax.scatter(year_data['County_Pct'], year_data['Cumulative_Pct'], 
                  c=colors, s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
        ax.plot([0, 100], [0, 100], 'k--', alpha=0.3, label='Perfect equality')
        
        ax.set_title(f'{year} Census', fontsize=12, fontweight='bold')
        ax.set_xlabel('% of Counties', fontsize=10)
        ax.set_ylabel('% of Irrigated Acres', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        
        # Add text showing top concentration
        top_10_pct = year_data.head(int(len(year_data) * 0.1))['Cumulative_Pct'].iloc[-1] if len(year_data) >= 10 else 0
        ax.text(0.98, 0.02, f'Top 10% counties:\n{top_10_pct:.1f}% of acres', 
               transform=ax.transAxes, ha='right', va='bottom',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), fontsize=8)
    
    # Remove empty subplots
    for idx in range(len(years), len(axes)):
        fig.delaxes(axes[idx])
    
    plt.suptitle('Irrigation Concentration: Lorenz Curve Analysis\n(How much irrigation is concentrated in top counties?)',
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    filename = f'{output_dir}/Irrigation_Concentration_Lorenz.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   💾 Saved: {filename}")
    plt.close()


def correlate_with_yield(df):
    """Correlate irrigation metrics with yield performance."""
    print("\n📊 Analyzing irrigation vs yield performance...")
    
    output_dir = 'outputs/Irrigation'
    os.makedirs(output_dir, exist_ok=True)
    
    # Load yield data
    try:
        yield_df = pd.read_csv('data/nass/Soybean_Yield_BU:Acre_By_County.csv')
        yield_df = yield_df[yield_df['Year'] != 'Year']
        yield_df['Year'] = yield_df['Year'].astype(int)
        yield_df['County'] = yield_df['County'].astype(str).str.title().str.strip()
        yield_df['Value'] = pd.to_numeric(yield_df['Value'], errors='coerce')
        yield_df = yield_df.dropna(subset=['Value'])
        
        # Merge with irrigation data
        irr_data = df[~df['Acres_Suppressed'] & ~df['Operations_Suppressed']].copy()
        
        merged = pd.merge(yield_df[['Year', 'County', 'Value']], 
                         irr_data[['Year', 'County', 'Acres', 'Operations', 'Avg_Farm_Size', 'Ag District']], 
                         on=['Year', 'County'], how='left')
        
        merged['Has_Irrigation'] = ~merged['Acres'].isna()
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Yield comparison irrigated vs non-irrigated
        irrigated = merged[merged['Has_Irrigation']]
        non_irrigated = merged[~merged['Has_Irrigation']]
        
        axes[0,0].boxplot([irrigated['Value'], non_irrigated['Value']], 
                         labels=['Irrigated\nCounties', 'Non-Irrigated\nCounties'],
                         patch_artist=True)
        axes[0,0].set_title('Yield Comparison: Irrigated vs Non-Irrigated Counties', 
                           fontsize=14, fontweight='bold')
        axes[0,0].set_ylabel('Yield (Bu/Acre)', fontsize=12)
        axes[0,0].grid(axis='y', alpha=0.3)
        
        # Stats
        irr_mean = irrigated['Value'].mean()
        non_irr_mean = non_irrigated['Value'].mean()
        axes[0,0].text(0.5, 0.98, f'Irrigated: {irr_mean:.1f} bu/ac\nNon-Irrigated: {non_irr_mean:.1f} bu/ac',
                      transform=axes[0,0].transAxes, ha='center', va='top',
                      bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Plot 2: Yield vs irrigation intensity (acres)
        irrigated_only = merged[merged['Has_Irrigation']].copy()
        
        for district in sorted(irrigated_only['Ag District'].dropna().unique()):
            dist_data = irrigated_only[irrigated_only['Ag District'] == district]
            color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
            axes[0,1].scatter(dist_data['Acres'], dist_data['Value'], 
                            s=50, alpha=0.6, color=color, label=district)
        
        axes[0,1].set_title('Yield vs Irrigated Acres', fontsize=14, fontweight='bold')
        axes[0,1].set_xlabel('Irrigated Acres', fontsize=12)
        axes[0,1].set_ylabel('Yield (Bu/Acre)', fontsize=12)
        axes[0,1].legend(fontsize=9)
        axes[0,1].grid(True, alpha=0.3)
        
        # Plot 3: Yield vs farm size
        for district in sorted(irrigated_only['Ag District'].dropna().unique()):
            dist_data = irrigated_only[irrigated_only['Ag District'] == district]
            color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')
            axes[1,0].scatter(dist_data['Avg_Farm_Size'], dist_data['Value'], 
                            s=50, alpha=0.6, color=color, label=district)
        
        axes[1,0].set_title('Yield vs Average Irrigated Farm Size', fontsize=14, fontweight='bold')
        axes[1,0].set_xlabel('Avg Farm Size (acres/operation)', fontsize=12)
        axes[1,0].set_ylabel('Yield (Bu/Acre)', fontsize=12)
        axes[1,0].legend(fontsize=9)
        axes[1,0].grid(True, alpha=0.3)
        
        # Plot 4: Yield trends over time for high vs low irrigation counties
        # Define high irrigation as top 25% by acres in latest census
        latest_year = irr_data['Year'].max()
        latest_irr = irr_data[irr_data['Year'] == latest_year]
        high_irr_threshold = latest_irr['Acres'].quantile(0.75)
        high_irr_counties = latest_irr[latest_irr['Acres'] >= high_irr_threshold]['County'].unique()
        
        high_irr_yields = merged[merged['County'].isin(high_irr_counties)].groupby('Year')['Value'].mean()
        low_irr_yields = merged[~merged['County'].isin(high_irr_counties) & merged['Has_Irrigation']].groupby('Year')['Value'].mean()
        no_irr_yields = merged[~merged['Has_Irrigation']].groupby('Year')['Value'].mean()
        
        axes[1,1].plot(high_irr_yields.index, high_irr_yields.values, marker='o', linewidth=2.5,
                      markersize=8, label='High Irrigation Counties', color='darkgreen')
        axes[1,1].plot(low_irr_yields.index, low_irr_yields.values, marker='o', linewidth=2.5,
                      markersize=8, label='Low Irrigation Counties', color='orange')
        axes[1,1].plot(no_irr_yields.index, no_irr_yields.values, marker='o', linewidth=2.5,
                      markersize=8, label='Non-Irrigated Counties', color='gray')
        
        axes[1,1].set_title('Yield Trends by Irrigation Level', fontsize=14, fontweight='bold')
        axes[1,1].set_xlabel('Year', fontsize=12)
        axes[1,1].set_ylabel('Average Yield (Bu/Acre)', fontsize=12)
        axes[1,1].legend(fontsize=10)
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        filename = f'{output_dir}/Irrigation_vs_Yield_Analysis.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved: {filename}")
        plt.close()
        
    except Exception as e:
        print(f"   ⚠️  Could not correlate with yield data: {e}")


def main():
    """Run comprehensive irrigation analysis."""
    print("🌾 COMPREHENSIVE MARYLAND IRRIGATION ANALYSIS")
    print("=" * 80)
    
    df = load_irrigation_data()
    
    analyze_irrigation_summary(df)
    plot_operations_trends(df)
    plot_farm_size_distribution(df)
    plot_concentration_analysis(df)
    correlate_with_yield(df)
    
    print("\n" + "=" * 80)
    print("✅ Comprehensive irrigation analysis completed!")
    print("📁 Output directory: outputs/Irrigation/")
    print("=" * 80)


if __name__ == "__main__":
    main()




