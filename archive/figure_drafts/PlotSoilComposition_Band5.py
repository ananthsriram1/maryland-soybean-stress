#!/usr/bin/env python3
"""
Maryland Soil Composition Visualization (Band-5 Soybeans only)
Creates plots for soil composition analysis based on CDL band-5-only data.

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
	"Prince George's": 'SOUTHERN',
	"Queen Anne's": 'UPPER EASTERN SHORE',
	'Somerset': 'LOWER EASTERN SHORE',
	"St. Mary's": 'SOUTHERN',
	'Talbot': 'UPPER EASTERN SHORE',
	'Washington': 'NORTH CENTRAL',
	'Wicomico': 'LOWER EASTERN SHORE',
	'Worcester': 'LOWER EASTERN SHORE'
}


def load_soil_data_band5():
	"""Load processed band5 soil composition data and mapping."""
	soil_2018 = None
	soil_2020 = None
	soil_mapping = None
	mapping_path = 'data/processed_band5/soil_type_mapping_band5.csv'
	if os.path.exists(mapping_path):
		soil_mapping = pd.read_csv(mapping_path)

	path_2018 = 'data/processed_band5/maryland_soil_composition_processed_band5_2018band5.csv'
	path_2020 = 'data/processed_band5/maryland_soil_composition_processed_band5_2020band5.csv'

	if os.path.exists(path_2018):
		soil_2018 = pd.read_csv(path_2018)
	if os.path.exists(path_2020):
		soil_2020 = pd.read_csv(path_2020)

	# Prefer 2020 as "current" if available, else 2018
	soil_current = soil_2020 if soil_2020 is not None else soil_2018
	return soil_current, soil_2018, soil_2020, soil_mapping


def plot_1_overall_soil_distribution(soil_data: pd.DataFrame, soil_mapping: pd.DataFrame, output_dir: str, title_suffix: str = ""):
	soil_totals = {}
	for _, row in soil_mapping.iterrows():
		code = row['Code']
		col_name = f'{code}_Area_Acres'
		if col_name in soil_data.columns:
			total_area = soil_data[col_name].sum()
			if total_area > 0:
				soil_totals[code] = {'area': total_area, 'name': row['Name'], 'color': row['Color']}

	fig, ax = plt.subplots(figsize=(12, 8))
	labels = [f"{code}\n({info['name']})" for code, info in soil_totals.items()]
	sizes = [info['area'] for info in soil_totals.values()]
	colors = [info['color'] for info in soil_totals.values()]

	if not sizes:
		plt.close()
		return

	wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
	for autotext in autotexts:
		autotext.set_color('white')
		autotext.set_fontweight('bold')

	ax.set_title(f'Maryland Soil Composition Distribution {title_suffix}'.strip(), fontsize=16, fontweight='bold', pad=20)
	total_area = sum(sizes)
	ax.text(0, -1.3, f'Total Area: {total_area:,.0f} acres', ha='center', fontsize=12, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
	plt.tight_layout()
	plt.savefig(f'{output_dir}/01_Overall_Soil_Distribution.png', dpi=300, bbox_inches='tight')
	plt.close()


def plot_2_county_soil_heatmap(soil_data: pd.DataFrame, soil_mapping: pd.DataFrame, output_dir: str):
	soil_codes = soil_mapping['Code'].tolist()
	county_rows = []
	for _, row in soil_data.iterrows():
		entry = {'County': row['County']}
		for code in soil_codes:
			col = f'{code}_Percentage'
			if col in soil_data.columns:
				entry[code] = row[col]
		county_rows.append(entry)
	heatmap_df = pd.DataFrame(county_rows).set_index('County')

	fig, ax = plt.subplots(figsize=(14, 10))
	sns.heatmap(heatmap_df, annot=True, fmt='.1f', cmap=sns.color_palette("viridis", as_cmap=True), cbar_kws={'label': 'Percentage (%)'}, ax=ax)
	ax.set_title('Soil Composition by County (Band5)\n(Percentage Coverage)', fontsize=16, fontweight='bold', pad=20)
	ax.set_xlabel('Soil Type', fontsize=12, fontweight='bold')
	ax.set_ylabel('County', fontsize=12, fontweight='bold')
	plt.xticks(rotation=45, ha='right')
	plt.yticks(rotation=0)
	plt.tight_layout()
	plt.savefig(f'{output_dir}/02_County_Soil_Heatmap.png', dpi=300, bbox_inches='tight')
	plt.close()


def plot_3_district_soil_comparison(soil_data: pd.DataFrame, soil_mapping: pd.DataFrame, output_dir: str):
	soil_data = soil_data.copy()
	soil_data['District'] = soil_data['County'].map(COUNTY_TO_DISTRICT)
	soil_codes = soil_mapping['Code'].tolist()

	district_soil = {}
	for district in DISTRICT_COLORS.keys():
		d = soil_data[soil_data['District'] == district]
		district_soil[district] = {}
		for code in soil_codes:
			col = f'{code}_Percentage'
			if col in soil_data.columns:
				district_soil[district][code] = d[col].mean()

	fig, ax = plt.subplots(figsize=(14, 8))
	districts = list(DISTRICT_COLORS.keys())
	x = np.arange(len(districts))
	width = 0.8
	soil_colors = {row['Code']: row['Color'] for _, row in soil_mapping.iterrows()}
	bottom = np.zeros(len(districts))
	for code in soil_codes:
		values = [district_soil[d].get(code, 0) for d in districts]
		if sum(values) > 0:
			ax.bar(x, values, width, bottom=bottom, label=code, color=soil_colors.get(code, 'gray'))
			bottom += values
	ax.set_xlabel('Agricultural District', fontsize=12, fontweight='bold')
	ax.set_ylabel('Average Soil Percentage (%)', fontsize=12, fontweight='bold')
	ax.set_title('Soil Composition by Agricultural District (Band5)', fontsize=16, fontweight='bold', pad=20)
	ax.set_xticks(x)
	ax.set_xticklabels(districts, rotation=45, ha='right')
	ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
	plt.tight_layout()
	plt.savefig(f'{output_dir}/03_District_Soil_Comparison.png', dpi=300, bbox_inches='tight')
	plt.close()


def plot_4_top_soil_types_by_area(soil_data: pd.DataFrame, soil_mapping: pd.DataFrame, output_dir: str):
	soil_totals = []
	for _, row in soil_mapping.iterrows():
		code = row['Code']
		col = f'{code}_Area_Acres'
		if col in soil_data.columns:
			area = soil_data[col].sum()
			if area > 0:
				soil_totals.append({'Code': code, 'Name': row['Name'], 'Area_Acres': area, 'Color': row['Color']})
	soil_totals.sort(key=lambda x: x['Area_Acres'], reverse=True)
	if not soil_totals:
		return

	fig, ax = plt.subplots(figsize=(12, 8))
	codes = [t['Code'] for t in soil_totals]
	areas = [t['Area_Acres'] for t in soil_totals]
	colors = [t['Color'] for t in soil_totals]
	names = [t['Name'] for t in soil_totals]
	bars = ax.barh(codes, areas, color=colors)
	for bar, area in zip(bars, areas):
		ax.text(bar.get_width() + max(areas) * 0.01, bar.get_y() + bar.get_height()/2, f'{area:,.0f} acres', ha='left', va='center', fontweight='bold')
	ax.set_xlabel('Total Area (Acres)', fontsize=12, fontweight='bold')
	ax.set_ylabel('Soil Type', fontsize=12, fontweight='bold')
	ax.set_title('Soil Types by Total Area Coverage (Band5)', fontsize=16, fontweight='bold', pad=20)
	legend_elements = [Patch(facecolor=c, label=f'{code} - {name}') for code, name, c in zip(codes, names, colors)]
	ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
	plt.tight_layout()
	plt.savefig(f'{output_dir}/04_Top_Soil_Types_by_Area.png', dpi=300, bbox_inches='tight')
	plt.close()


def plot_5_county_area_comparison(soil_data: pd.DataFrame, output_dir: str):
	county_areas = soil_data[['County', 'Total_Area_Acres']].copy().sort_values('Total_Area_Acres', ascending=True)
	county_areas['District'] = county_areas['County'].map(COUNTY_TO_DISTRICT)
	county_areas['Color'] = county_areas['District'].map(DISTRICT_COLORS)
	fig, ax = plt.subplots(figsize=(12, 10))
	bars = ax.barh(county_areas['County'], county_areas['Total_Area_Acres'], color=county_areas['Color'])
	for bar, area in zip(bars, county_areas['Total_Area_Acres']):
		ax.text(bar.get_width() + max(county_areas['Total_Area_Acres']) * 0.01, bar.get_y() + bar.get_height()/2, f'{area:,.0f} acres', ha='left', va='center', fontweight='bold')
	ax.set_xlabel('Total Soil Area (Acres)', fontsize=12, fontweight='bold')
	ax.set_ylabel('County', fontsize=12, fontweight='bold')
	ax.set_title('Total Soil Area by County (Band5)\n(Color-coded by Agricultural District)', fontsize=16, fontweight='bold', pad=20)
	legend_elements = [Patch(facecolor=color, label=d) for d, color in DISTRICT_COLORS.items()]
	ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
	plt.tight_layout()
	plt.savefig(f'{output_dir}/05_County_Area_Comparison.png', dpi=300, bbox_inches='tight')
	plt.close()


def plot_6_soil_diversity_analysis(soil_data: pd.DataFrame, soil_mapping: pd.DataFrame, output_dir: str):
	soil_codes = soil_mapping['Code'].tolist()
	diversity_data = []
	for _, row in soil_data.iterrows():
		percentages = []
		for code in soil_codes:
			col = f'{code}_Percentage'
			if col in soil_data.columns:
				p = row[col]
				if p > 0:
					percentages.append(p)
		num_soil_types = len(percentages)
		shannon = -sum((p/100) * np.log(p/100) for p in percentages if p > 0)
		max_pct = max(percentages) if percentages else 0
		diversity_data.append({'County': row['County'], 'Num_Soil_Types': num_soil_types, 'Shannon_Diversity': shannon, 'Max_Percentage': max_pct, 'District': COUNTY_TO_DISTRICT.get(row['County'], 'Unknown')})
	diversity_df = pd.DataFrame(diversity_data)

	fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
	# 1
	d1 = diversity_df.sort_values('Num_Soil_Types')
	c1 = [DISTRICT_COLORS.get(d, 'gray') for d in d1['District']]
	bars1 = ax1.barh(d1['County'], d1['Num_Soil_Types'], color=c1)
	ax1.set_xlabel('Number of Soil Types')
	ax1.set_title('Soil Type Diversity by County (Band5)')
	for bar, v in zip(bars1, d1['Num_Soil_Types']):
		ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, str(v), ha='left', va='center', fontweight='bold')
	# 2
	d2 = diversity_df.sort_values('Shannon_Diversity')
	c2 = [DISTRICT_COLORS.get(d, 'gray') for d in d2['District']]
	bars2 = ax2.barh(d2['County'], d2['Shannon_Diversity'], color=c2)
	ax2.set_xlabel('Shannon Diversity Index')
	ax2.set_title('Soil Diversity Index by County (Band5)')
	for bar, v in zip(bars2, d2['Shannon_Diversity']):
		ax2.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2, f'{v:.2f}', ha='left', va='center', fontweight='bold')
	# 3
	d3 = diversity_df.sort_values('Max_Percentage')
	c3 = [DISTRICT_COLORS.get(d, 'gray') for d in d3['District']]
	bars3 = ax3.barh(d3['County'], d3['Max_Percentage'], color=c3)
	ax3.set_xlabel('Dominant Soil Percentage (%)')
	ax3.set_title('Dominant Soil Type Coverage (Band5)')
	for bar, v in zip(bars3, d3['Max_Percentage']):
		ax3.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f'{v:.1f}%', ha='left', va='center', fontweight='bold')
	# 4
	dstats = diversity_df.groupby('District').agg({'Num_Soil_Types': 'mean', 'Shannon_Diversity': 'mean', 'Max_Percentage': 'mean'}).round(2)
	x = np.arange(len(dstats.index))
	w = 0.25
	ax4.bar(x - w, dstats['Num_Soil_Types'], w, label='Avg Soil Types', alpha=0.8)
	ax4.bar(x, dstats['Shannon_Diversity'], w, label='Avg Diversity Index', alpha=0.8)
	ax4.bar(x + w, dstats['Max_Percentage'], w, label='Avg Dominant %', alpha=0.8)
	ax4.set_xlabel('Agricultural District')
	ax4.set_ylabel('Average Value')
	ax4.set_title('Soil Diversity Metrics by District (Band5)')
	ax4.set_xticks(x)
	ax4.set_xticklabels(dstats.index, rotation=45, ha='right')
	ax4.legend()
	plt.tight_layout()
	plt.savefig(f'{output_dir}/06_Soil_Diversity_Analysis.png', dpi=300, bbox_inches='tight')
	plt.close()


def main():
	print("="*80)
	print("MARYLAND SOIL COMPOSITION VISUALIZATION (Band-5 Soybeans)")
	print("="*80)
	output_dir = 'outputs/SoilCompositionBand5'
	os.makedirs(output_dir, exist_ok=True)

	print("🔄 Loading band-5 soil composition data...")
	soil_current, soil_2018, soil_2020, soil_mapping = load_soil_data_band5()
	if soil_current is None or soil_mapping is None:
		print("⚠️  No processed band5 soil data found. Please run PreprocessSoilData_Band5.py first.")
		return
	print(f"   ✅ Loaded {len(soil_current)} counties (current)")
	print(f"   ✅ Loaded {len(soil_mapping)} soil types")

	print("\n📊 Generating band-5 soil composition visualizations...")
	print("   📈 Creating overall soil distribution...")
	title_suffix = "(Band5 Current)"
	plot_1_overall_soil_distribution(soil_current, soil_mapping, output_dir, title_suffix)

	print("   📈 Creating county soil heatmap...")
	plot_2_county_soil_heatmap(soil_current, soil_mapping, output_dir)

	print("   📈 Creating district soil comparison...")
	plot_3_district_soil_comparison(soil_current, soil_mapping, output_dir)

	print("   📈 Creating top soil types by area...")
	plot_4_top_soil_types_by_area(soil_current, soil_mapping, output_dir)

	print("   📈 Creating county area comparison...")
	plot_5_county_area_comparison(soil_current, output_dir)

	print("   📈 Creating soil diversity analysis...")
	plot_6_soil_diversity_analysis(soil_current, soil_mapping, output_dir)

	# Optional: 2018 vs 2020 comparison if both exist
	if soil_2018 is not None and soil_2020 is not None:
		print("   📈 Creating 2018 vs 2020 comparison...")
		# Build comparison dataframe similar to original script
		comparison_rows = []
		for _, row18 in soil_2018.iterrows():
			county = row18['County']
			area18 = row18['Total_Area_Acres']
			match20 = soil_2020[soil_2020['County'] == county]
			if not match20.empty:
				area20 = match20.iloc[0]['Total_Area_Acres']
				change = area20 - area18
				change_pct = (change / area18 * 100) if area18 > 0 else 0
				comparison_rows.append({'County': county, 'Area_2018': area18, 'Area_2020': area20, 'Change': change, 'Change_Pct': change_pct, 'District': COUNTY_TO_DISTRICT.get(county, 'Unknown')})

		comp_df = pd.DataFrame(comparison_rows).sort_values('Change_Pct', ascending=True)
		fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
		colors = [DISTRICT_COLORS.get(d, 'gray') for d in comp_df['District']]
		bars1 = ax1.barh(comp_df['County'], comp_df['Change_Pct'], color=colors)
		ax1.set_xlabel('Change in Area (%)')
		ax1.set_title('Soil Area Change: 2018 vs 2020 (Band5)')
		ax1.axvline(x=0, color='black', linestyle='--', alpha=0.5)
		for bar, value in zip(bars1, comp_df['Change_Pct']):
			ax1.text(bar.get_width() + (0.5 if value >= 0 else -0.5), bar.get_y() + bar.get_height()/2, f'{value:+.1f}%', ha='left' if value >= 0 else 'right', va='center', fontweight='bold')
		ax2.scatter(comp_df['Area_2018'], comp_df['Area_2020'], c=colors, s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
		max_area = max(comp_df['Area_2018'].max(), comp_df['Area_2020'].max())
		ax2.plot([0, max_area], [0, max_area], 'k--', alpha=0.5, label='No Change')
		ax2.set_xlabel('2018 Area (Acres)')
		ax2.set_ylabel('2020 Area (Acres)')
		ax2.set_title('Soil Area: 2018 vs 2020 (Band5)')
		ax2.legend()
		for _, r in comp_df.iterrows():
			if abs(r['Change_Pct']) > 5:
				ax2.annotate(r['County'], (r['Area_2018'], r['Area_2020']), xytext=(5, 5), textcoords='offset points', fontsize=8)
		plt.tight_layout()
		plt.savefig(f'{output_dir}/07_2018_vs_2020_Comparison.png', dpi=300, bbox_inches='tight')
		plt.close()

	print(f"\n✅ Band-5 soil composition visualization complete!")
	print(f"📁 Output directory: {output_dir}/")
	print("="*80)


if __name__ == "__main__":
	main()
