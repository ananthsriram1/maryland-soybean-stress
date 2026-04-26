#!/usr/bin/env python3
"""
Maryland Soil Composition Visualization
Creates comprehensive plots for soil composition analysis.

Author: Maryland Soybean Stress Project
"""

import os
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.patches import Patch

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

# District colors for consistency
DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',
    'SOUTHERN': '#90EE90', 
    'LOWER EASTERN SHORE': '#4ECDC4',
    'UPPER EASTERN SHORE': '#9370DB',
    'WESTERN': '#FFD700'
}

# County to district mapping
COUNTY_TO_DISTRICT = {
    'Allegany': 'WESTERN',
    'Anne Arundel': 'SOUTHERN',
    'Baltimore': 'NORTH CENTRAL',
    'Calvert': 'SOUTHERN',
    'Caroline': 'UPPER EASTERN SHORE',
    'Carroll': 'NORTH CENTRAL',
    'Cecil': 'UPPER EASTERN SHORE',
    'Charles': 'SOUTHERN',
    'Dorchester': 'LOWER EASTERN SHORE',
    'Frederick': 'NORTH CENTRAL',
    'Garrett': 'WESTERN',
    'Harford': 'NORTH CENTRAL',
    'Howard': 'NORTH CENTRAL',
    'Kent': 'UPPER EASTERN SHORE',
    'Montgomery': 'NORTH CENTRAL',
    'Prince George\'s': 'SOUTHERN',
    'Queen Anne\'s': 'UPPER EASTERN SHORE',
    'Somerset': 'LOWER EASTERN SHORE',
    'St. Mary\'s': 'SOUTHERN',
    'Talbot': 'UPPER EASTERN SHORE',
    'Washington': 'NORTH CENTRAL',
    'Wicomico': 'LOWER EASTERN SHORE',
    'Worcester': 'LOWER EASTERN SHORE'
}

def load_soil_data():
    """Load processed soil composition data."""
    soil_orig = pd.read_csv('data/processed/maryland_soil_composition_processed.csv')
    soil_2020 = pd.read_csv('data/processed/maryland_soil_composition_processed_2020.csv')
    soil_mapping = pd.read_csv('data/processed/soil_type_mapping.csv')
    
    return soil_orig, soil_2020, soil_mapping

def plot_1_overall_soil_distribution(soil_data, soil_mapping, output_dir):
    """Plot overall soil type distribution as pie chart."""
    
    # Calculate total area for each soil type
    soil_totals = {}
    for _, row in soil_mapping.iterrows():
        code = row['Code']
        col_name = f'{code}_Area_Acres'
        if col_name in soil_data.columns:
            total_area = soil_data[col_name].sum()
            if total_area > 0:
                soil_totals[code] = {
                    'area': total_area,
                    'name': row['Name'],
                    'color': row['Color']
                }
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    labels = [f"{code}\n({info['name']})" for code, info in soil_totals.items()]
    sizes = [info['area'] for info in soil_totals.values()]
    colors = [info['color'] for info in soil_totals.values()]
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                     startangle=90, textprops={'fontsize': 10})
    
    # Format percentage text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Maryland Soil Composition Distribution\n(Total Area by Soil Type)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Add total area text
    total_area = sum(sizes)
    ax.text(0, -1.3, f'Total Area: {total_area:,.0f} acres', 
            ha='center', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_Overall_Soil_Distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_2_county_soil_heatmap(soil_data, soil_mapping, output_dir):
    """Create heatmap of soil types by county."""
    
    # Prepare data for heatmap
    soil_codes = soil_mapping['Code'].tolist()
    county_data = []
    
    for _, row in soil_data.iterrows():
        county_info = {'County': row['County']}
        for code in soil_codes:
            col_name = f'{code}_Percentage'
            if col_name in soil_data.columns:
                county_info[code] = row[col_name]
        county_data.append(county_info)
    
    heatmap_df = pd.DataFrame(county_data).set_index('County')
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Use custom colors for each soil type
    soil_colors = {}
    for _, row in soil_mapping.iterrows():
        soil_colors[row['Code']] = row['Color']
    
    # Create colormap for each soil type
    cmap = sns.color_palette("viridis", as_cmap=True)
    
    sns.heatmap(heatmap_df, annot=True, fmt='.1f', cmap=cmap, 
                cbar_kws={'label': 'Percentage (%)'}, ax=ax)
    
    ax.set_title('Soil Composition by County\n(Percentage Coverage)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Soil Type', fontsize=12, fontweight='bold')
    ax.set_ylabel('County', fontsize=12, fontweight='bold')
    
    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_County_Soil_Heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_3_district_soil_comparison(soil_data, soil_mapping, output_dir):
    """Compare soil composition by agricultural district."""
    
    # Add district information
    soil_data['District'] = soil_data['County'].map(COUNTY_TO_DISTRICT)
    
    # Calculate district averages
    district_soil = {}
    soil_codes = soil_mapping['Code'].tolist()
    
    for district in DISTRICT_COLORS.keys():
        district_data = soil_data[soil_data['District'] == district]
        district_soil[district] = {}
        
        for code in soil_codes:
            col_name = f'{code}_Percentage'
            if col_name in soil_data.columns:
                avg_percentage = district_data[col_name].mean()
                district_soil[district][code] = avg_percentage
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(14, 8))
    
    districts = list(DISTRICT_COLORS.keys())
    x = np.arange(len(districts))
    width = 0.8
    
    # Get soil type colors
    soil_colors = {}
    for _, row in soil_mapping.iterrows():
        soil_colors[row['Code']] = row['Color']
    
    # Plot stacked bars
    bottom = np.zeros(len(districts))
    
    for code in soil_codes:
        values = [district_soil[district].get(code, 0) for district in districts]
        if sum(values) > 0:  # Only plot if there's data
            ax.bar(x, values, width, bottom=bottom, label=code, 
                   color=soil_colors.get(code, 'gray'))
            bottom += values
    
    ax.set_xlabel('Agricultural District', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Soil Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title('Soil Composition by Agricultural District\n(Average Percentage Coverage)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.set_xticks(x)
    ax.set_xticklabels(districts, rotation=45, ha='right')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_District_Soil_Comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_4_top_soil_types_by_area(soil_data, soil_mapping, output_dir):
    """Plot top soil types by total area coverage."""
    
    # Calculate total area for each soil type
    soil_totals = []
    for _, row in soil_mapping.iterrows():
        code = row['Code']
        col_name = f'{code}_Area_Acres'
        if col_name in soil_data.columns:
            total_area = soil_data[col_name].sum()
            if total_area > 0:
                soil_totals.append({
                    'Code': code,
                    'Name': row['Name'],
                    'Area_Acres': total_area,
                    'Color': row['Color']
                })
    
    # Sort by area
    soil_totals.sort(key=lambda x: x['Area_Acres'], reverse=True)
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    codes = [item['Code'] for item in soil_totals]
    areas = [item['Area_Acres'] for item in soil_totals]
    colors = [item['Color'] for item in soil_totals]
    names = [item['Name'] for item in soil_totals]
    
    bars = ax.barh(codes, areas, color=colors)
    
    # Add value labels on bars
    for i, (bar, area) in enumerate(zip(bars, areas)):
        ax.text(bar.get_width() + max(areas) * 0.01, bar.get_y() + bar.get_height()/2,
                f'{area:,.0f} acres', ha='left', va='center', fontweight='bold')
    
    ax.set_xlabel('Total Area (Acres)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Soil Type', fontsize=12, fontweight='bold')
    ax.set_title('Soil Types by Total Area Coverage\n(Top Soil Types in Maryland)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Add legend with soil names
    legend_elements = [Patch(facecolor=color, label=f'{code} - {name}') 
                      for code, name, color in zip(codes, names, colors)]
    ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_Top_Soil_Types_by_Area.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_5_county_area_comparison(soil_data, output_dir):
    """Compare total soil area by county."""
    
    # Sort counties by total area
    county_areas = soil_data[['County', 'Total_Area_Acres']].copy()
    county_areas = county_areas.sort_values('Total_Area_Acres', ascending=True)
    
    # Add district colors
    county_areas['District'] = county_areas['County'].map(COUNTY_TO_DISTRICT)
    county_areas['Color'] = county_areas['District'].map(DISTRICT_COLORS)
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 10))
    
    bars = ax.barh(county_areas['County'], county_areas['Total_Area_Acres'], 
                   color=county_areas['Color'])
    
    # Add value labels
    for bar, area in zip(bars, county_areas['Total_Area_Acres']):
        ax.text(bar.get_width() + max(county_areas['Total_Area_Acres']) * 0.01,
                bar.get_y() + bar.get_height()/2,
                f'{area:,.0f} acres', ha='left', va='center', fontweight='bold')
    
    ax.set_xlabel('Total Soil Area (Acres)', fontsize=12, fontweight='bold')
    ax.set_ylabel('County', fontsize=12, fontweight='bold')
    ax.set_title('Total Soil Area by County\n(Color-coded by Agricultural District)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Add district legend
    legend_elements = [Patch(facecolor=color, label=district) 
                      for district, color in DISTRICT_COLORS.items()]
    ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_County_Area_Comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_6_soil_diversity_analysis(soil_data, soil_mapping, output_dir):
    """Analyze soil diversity by county."""
    
    # Calculate soil diversity metrics
    diversity_data = []
    soil_codes = soil_mapping['Code'].tolist()
    
    for _, row in soil_data.iterrows():
        county = row['County']
        percentages = []
        
        for code in soil_codes:
            col_name = f'{code}_Percentage'
            if col_name in soil_data.columns:
                percentage = row[col_name]
                if percentage > 0:
                    percentages.append(percentage)
        
        # Calculate diversity metrics
        num_soil_types = len(percentages)
        shannon_diversity = -sum((p/100) * np.log(p/100) for p in percentages if p > 0)
        max_percentage = max(percentages) if percentages else 0
        
        diversity_data.append({
            'County': county,
            'Num_Soil_Types': num_soil_types,
            'Shannon_Diversity': shannon_diversity,
            'Max_Percentage': max_percentage,
            'District': COUNTY_TO_DISTRICT.get(county, 'Unknown')
        })
    
    diversity_df = pd.DataFrame(diversity_data)
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Number of soil types by county
    diversity_df_sorted = diversity_df.sort_values('Num_Soil_Types', ascending=True)
    colors1 = [DISTRICT_COLORS.get(district, 'gray') for district in diversity_df_sorted['District']]
    
    bars1 = ax1.barh(diversity_df_sorted['County'], diversity_df_sorted['Num_Soil_Types'], color=colors1)
    ax1.set_xlabel('Number of Soil Types')
    ax1.set_title('Soil Type Diversity by County')
    
    # Add value labels
    for bar, value in zip(bars1, diversity_df_sorted['Num_Soil_Types']):
        ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                str(value), ha='left', va='center', fontweight='bold')
    
    # 2. Shannon diversity index
    diversity_df_sorted2 = diversity_df.sort_values('Shannon_Diversity', ascending=True)
    colors2 = [DISTRICT_COLORS.get(district, 'gray') for district in diversity_df_sorted2['District']]
    
    bars2 = ax2.barh(diversity_df_sorted2['County'], diversity_df_sorted2['Shannon_Diversity'], color=colors2)
    ax2.set_xlabel('Shannon Diversity Index')
    ax2.set_title('Soil Diversity Index by County')
    
    # Add value labels
    for bar, value in zip(bars2, diversity_df_sorted2['Shannon_Diversity']):
        ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f'{value:.2f}', ha='left', va='center', fontweight='bold')
    
    # 3. Dominant soil percentage
    diversity_df_sorted3 = diversity_df.sort_values('Max_Percentage', ascending=True)
    colors3 = [DISTRICT_COLORS.get(district, 'gray') for district in diversity_df_sorted3['District']]
    
    bars3 = ax3.barh(diversity_df_sorted3['County'], diversity_df_sorted3['Max_Percentage'], color=colors3)
    ax3.set_xlabel('Dominant Soil Percentage (%)')
    ax3.set_title('Dominant Soil Type Coverage')
    
    # Add value labels
    for bar, value in zip(bars3, diversity_df_sorted3['Max_Percentage']):
        ax3.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{value:.1f}%', ha='left', va='center', fontweight='bold')
    
    # 4. District comparison
    district_stats = diversity_df.groupby('District').agg({
        'Num_Soil_Types': 'mean',
        'Shannon_Diversity': 'mean',
        'Max_Percentage': 'mean'
    }).round(2)
    
    x = np.arange(len(district_stats.index))
    width = 0.25
    
    ax4.bar(x - width, district_stats['Num_Soil_Types'], width, label='Avg Soil Types', alpha=0.8)
    ax4.bar(x, district_stats['Shannon_Diversity'], width, label='Avg Diversity Index', alpha=0.8)
    ax4.bar(x + width, district_stats['Max_Percentage'], width, label='Avg Dominant %', alpha=0.8)
    
    ax4.set_xlabel('Agricultural District')
    ax4.set_ylabel('Average Value')
    ax4.set_title('Soil Diversity Metrics by District')
    ax4.set_xticks(x)
    ax4.set_xticklabels(district_stats.index, rotation=45, ha='right')
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/06_Soil_Diversity_Analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_7_original_vs_2020_comparison(soil_orig, soil_2020, output_dir):
    """Compare original vs 2020 soil data."""
    
    # Merge datasets for comparison
    comparison_data = []
    
    for _, orig_row in soil_orig.iterrows():
        county = orig_row['County']
        orig_area = orig_row['Total_Area_Acres']
        
        # Find matching 2020 data
        match_2020 = soil_2020[soil_2020['County'] == county]
        if not match_2020.empty:
            area_2020 = match_2020.iloc[0]['Total_Area_Acres']
            change = area_2020 - orig_area
            change_pct = (change / orig_area * 100) if orig_area > 0 else 0
            
            comparison_data.append({
                'County': county,
                'Original_Area': orig_area,
                'Area_2020': area_2020,
                'Change': change,
                'Change_Pct': change_pct,
                'District': COUNTY_TO_DISTRICT.get(county, 'Unknown')
            })
    
    comp_df = pd.DataFrame(comparison_data)
    comp_df = comp_df.sort_values('Change_Pct', ascending=True)
    
    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 1. Area change by county
    colors = [DISTRICT_COLORS.get(district, 'gray') for district in comp_df['District']]
    
    bars1 = ax1.barh(comp_df['County'], comp_df['Change_Pct'], color=colors)
    ax1.set_xlabel('Change in Area (%)')
    ax1.set_title('Soil Area Change: Original vs 2020\n(Percentage Change)')
    ax1.axvline(x=0, color='black', linestyle='--', alpha=0.5)
    
    # Add value labels
    for bar, value in zip(bars1, comp_df['Change_Pct']):
        ax1.text(bar.get_width() + (0.5 if value >= 0 else -0.5), bar.get_y() + bar.get_height()/2,
                f'{value:+.1f}%', ha='left' if value >= 0 else 'right', va='center', fontweight='bold')
    
    # 2. Scatter plot: Original vs 2020
    ax2.scatter(comp_df['Original_Area'], comp_df['Area_2020'], 
               c=colors, s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
    
    # Add diagonal line (no change)
    max_area = max(comp_df['Original_Area'].max(), comp_df['Area_2020'].max())
    ax2.plot([0, max_area], [0, max_area], 'k--', alpha=0.5, label='No Change')
    
    ax2.set_xlabel('Original Area (Acres)')
    ax2.set_ylabel('2020 Area (Acres)')
    ax2.set_title('Soil Area: Original vs 2020\n(Scatter Plot)')
    ax2.legend()
    
    # Add county labels for extreme points
    for _, row in comp_df.iterrows():
        if abs(row['Change_Pct']) > 5:  # Only label significant changes
            ax2.annotate(row['County'], (row['Original_Area'], row['Area_2020']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/07_Original_vs_2020_Comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main function to generate all soil composition plots."""
    
    print("="*80)
    print("MARYLAND SOIL COMPOSITION VISUALIZATION")
    print("="*80)
    
    # Create output directory
    output_dir = 'outputs/SoilComposition'
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    print("🔄 Loading soil composition data...")
    soil_orig, soil_2020, soil_mapping = load_soil_data()
    print(f"   ✅ Loaded {len(soil_orig)} counties (original)")
    print(f"   ✅ Loaded {len(soil_2020)} counties (2020)")
    print(f"   ✅ Loaded {len(soil_mapping)} soil types")
    
    # Generate plots
    print("\n📊 Generating soil composition visualizations...")
    
    print("   📈 Creating overall soil distribution...")
    plot_1_overall_soil_distribution(soil_orig, soil_mapping, output_dir)
    
    print("   📈 Creating county soil heatmap...")
    plot_2_county_soil_heatmap(soil_orig, soil_mapping, output_dir)
    
    print("   📈 Creating district soil comparison...")
    plot_3_district_soil_comparison(soil_orig, soil_mapping, output_dir)
    
    print("   📈 Creating top soil types by area...")
    plot_4_top_soil_types_by_area(soil_orig, soil_mapping, output_dir)
    
    print("   📈 Creating county area comparison...")
    plot_5_county_area_comparison(soil_orig, output_dir)
    
    print("   📈 Creating soil diversity analysis...")
    plot_6_soil_diversity_analysis(soil_orig, soil_mapping, output_dir)
    
    print("   📈 Creating original vs 2020 comparison...")
    plot_7_original_vs_2020_comparison(soil_orig, soil_2020, output_dir)
    
    print(f"\n✅ Soil composition visualization complete!")
    print(f"📁 Output directory: {output_dir}/")
    print("="*80)

if __name__ == "__main__":
    main()






