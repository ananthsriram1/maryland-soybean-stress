#!/usr/bin/env python3
"""
Plot acres planted and yield for SaLo > 8% counties with irrigation status labels.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch

plt.style.use('seaborn-v0_8') if 'seaborn-v0_8' in plt.style.available else plt.style.use('seaborn')

OUTPUT_DIR = 'outputs/Irrigation/SaLoCounties'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SI: 1 ac = 0.404685642 ha; soybean yield bu/ac → kg/ha (60 lb/bu, 1 ac = 0.404685642 ha)
ACRE_TO_HA = 0.404685642
BUAC_TO_KGHA = 67.251

COUNTIES = [
	('Anne Arundel','Southern','NO'),
	('Calvert','Southern','NO'),
	('Caroline','Upper Eastern Shore','YES'),
	('Dorchester','Lower Eastern Shore','YES'),
	("Prince George’s",'Southern','NO'),
	("Queen Anne’s",'Upper Eastern Shore','YES'),
	('Somerset','Lower Eastern Shore','NO'),
	("St. Mary’s",'Southern','NO'),
	('Talbot','Upper Eastern Shore','YES'),
	('Wicomico','Lower Eastern Shore','YES'),
	('Worcester','Lower Eastern Shore','YES'),
]

PLANTED_PATH = 'data/nass/Soybean_Acres_Planted_By_County.csv'
YIELD_PATH = 'data/nass/Soybean_Yield_BU:Acre_By_County.csv'
YEARS = [2018, 2020, 2022, 2023]

NORM = {
	'Anne Arundel':'ANNE ARUNDEL','Calvert':'CALVERT','Caroline':'CAROLINE','Dorchester':'DORCHESTER',
	"Prince George’s":'PRINCE GEORGES',"Queen Anne’s":'QUEEN ANNES','Somerset':'SOMERSET',
	"St. Mary’s":'ST MARYS','Talbot':'TALBOT','Wicomico':'WICOMICO','Worcester':'WORCESTER'
}


def load_planted():
	df = pd.read_csv(PLANTED_PATH)
	df = df[(df['State']=='MARYLAND') & (df['Geo Level']=='COUNTY')].copy()
	df['County_norm'] = df['County'].str.upper().str.replace("'",'', regex=False).str.replace('.', '', regex=False)
	df['Value_num'] = pd.to_numeric(df['Value'].astype(str).str.replace(',','', regex=False), errors='coerce')
	return df


def load_yield():
	df = pd.read_csv(YIELD_PATH)
	df = df[(df['State']=='MARYLAND') & (df['Geo Level']=='COUNTY')].copy()
	df['County_norm'] = df['County'].str.upper().str.replace("'",'', regex=False).str.replace('.', '', regex=False)
	df['Value_num'] = pd.to_numeric(df['Value'].astype(str).str.replace(',','', regex=False), errors='coerce')
	return df


def build_matrix(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
	rows = []
	for county, district, irr in COUNTIES:
		norm = NORM[county]
		for year in YEARS:
			sub = df[(df['County_norm']==norm) & (df['Year']==year)]
			val = np.nan if sub.empty or sub[value_col].isna().all() else float(sub.iloc[0][value_col])
			rows.append({'County': county, 'Year': year, 'Value': val, 'District': district, 'Irrigation': irr})
	mat = pd.DataFrame(rows).pivot(index='Year', columns='County', values='Value')
	return mat


def annotate_columns_with_irrigation(columns):
	labels = []
	for c in columns:
		irr = next(irr for name, _, irr in COUNTIES if name == c)
		labels.append(f"{c}\nIrrig: {irr}")
	return labels


def quantile_limits(mat: pd.DataFrame, q_low=0.05, q_high=0.95):
	vals = mat.values.flatten()
	vals = vals[~np.isnan(vals)]
	if len(vals) == 0:
		return None, None
	return float(np.quantile(vals, q_low)), float(np.quantile(vals, q_high))


def main():
	planted = load_planted()
	yield_df = load_yield()
	plant_mat = build_matrix(planted, 'Value_num')
	yield_mat = build_matrix(yield_df, 'Value_num')

	# Order counties by mean acres planted (ascending) so low-acreage (mostly non-irrigated)
	# appear left and high-acreage (irrigated) right — highlights "irrigate only when enough acres"
	mean_acres = plant_mat.mean(axis=0).sort_values(ascending=True)
	col_order = mean_acres.index.tolist()
	plant_mat = plant_mat[col_order]
	yield_mat = yield_mat[col_order]

	# Prepare masks to leave suppressed (NaN) blank
	plant_mask = plant_mat.isna()
	yield_mask = yield_mat.isna()

	# SI matrices for display
	plant_mat_ha = plant_mat * ACRE_TO_HA
	yield_mat_kgha = yield_mat * BUAC_TO_KGHA
	# Robust color scaling using quantiles (ignore outliers)
	p_vmin, p_vmax = quantile_limits(plant_mat_ha)
	y_vmin, y_vmax = quantile_limits(yield_mat_kgha)

	# Figure with irrigation status strip on top
	n_cols = plant_mat.shape[1]
	fig_h = 11
	fig_w = max(12, n_cols * 1.3)
	fig = plt.figure(figsize=(fig_w, fig_h))
	gs = fig.add_gridspec(3, 1, height_ratios=[0.35, 1, 1], hspace=0.25)
	ax_strip = fig.add_subplot(gs[0, 0])
	ax1 = fig.add_subplot(gs[1, 0])
	ax2 = fig.add_subplot(gs[2, 0])

	# Irrigation status strip (categorical)
	irr_map = {'YES': '#2ca02c', 'NO': '#d62728'}  # colorblind-friendly contrast
	strip_vals = [next(irr for name, _, irr in COUNTIES if name == c) for c in plant_mat.columns]
	strip_colors = [irr_map.get(v, '#808080') for v in strip_vals]
	ax_strip.set_xlim(-0.5, n_cols-0.5)
	ax_strip.set_ylim(-0.5, 0.5)
	for i, c in enumerate(strip_colors):
		ax_strip.add_patch(plt.Rectangle((i-0.5, -0.5), 1, 1, color=c))
	ax_strip.set_yticks([])
	ax_strip.set_xticks(range(n_cols))
	ax_strip.set_xticklabels(['' for _ in range(n_cols)])
	ax_strip.set_title('Irrigation status (green = YES, red = NO)', fontsize=12)
	# Legend
	leg_elems = [plt.Rectangle((0,0),1,1,color=irr_map['YES'], label='Irrigation: YES'),
				 plt.Rectangle((0,0),1,1,color=irr_map['NO'], label='Irrigation: NO')]
	ax_strip.legend(handles=leg_elems, loc='center left', bbox_to_anchor=(1.01, 0.5), frameon=False)

	# Heatmaps with masks and colorblind-safe palettes
	ax1.set_facecolor('white')
	ax2.set_facecolor('white')
	sns.heatmap(plant_mat_ha, mask=plant_mask, annot=True, fmt='.0f', cmap='viridis',
				vmin=p_vmin, vmax=p_vmax,
				cbar_kws={'label':'Area planted (ha)'}, ax=ax1)
	ax1.set_title('Soybean area planted (ha) — SaLo > 8% Counties (counties ordered by mean area)', fontsize=14, fontweight='bold', pad=10)
	ax1.set_ylabel('Year')

	sns.heatmap(yield_mat_kgha, mask=yield_mask, annot=True, fmt='.0f', cmap='magma',
				vmin=y_vmin, vmax=y_vmax,
				cbar_kws={'label':'Yield (kg/ha)'}, ax=ax2)
	ax2.set_title('Soybean yield (kg/ha)', fontsize=14)
	ax2.set_ylabel('Year')

	labels = annotate_columns_with_irrigation(plant_mat.columns)
	ax2.set_xticklabels(labels, rotation=45, ha='right')
	ax1.set_xticklabels(['' for _ in labels])

	# Format colorbars
	for ax in (ax1, ax2):
		if ax.collections and ax.collections[0].colorbar:
			fmt = (lambda x, p: f'{int(x):,}') if ax is ax1 else (lambda x, p: f'{x:.0f}')
			ax.collections[0].colorbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt))

	plt.tight_layout(rect=[0, 0.02, 1, 1])
	outfile = f"{OUTPUT_DIR}/SaLo_Counties_Planted_and_Yield_Heatmaps_Robust.png"
	plt.savefig(outfile, dpi=300, bbox_inches='tight')
	print(f"Saved: {outfile}")

	# Save CSVs for reference (acres / bu ac) and SI copies
	plant_mat.to_csv(f"{OUTPUT_DIR}/Planted_Matrix.csv")
	yield_mat.to_csv(f"{OUTPUT_DIR}/Yield_Matrix.csv")
	plant_mat_ha.to_csv(f"{OUTPUT_DIR}/Planted_Matrix_ha.csv")
	yield_mat_kgha.to_csv(f"{OUTPUT_DIR}/Yield_Matrix_kg_ha.csv")

	# Bar chart version: clearer "low acres = no irrigation, high acres = irrigation"
	plot_bar_chart(plant_mat, yield_mat, col_order)


def plot_bar_chart(plant_mat, yield_mat, col_order):
	"""Horizontal bar charts: mean area (ha) and mean yield (kg/ha) by county, colored by irrigation."""
	counties = col_order
	mean_acres = plant_mat.mean(axis=0).reindex(col_order).fillna(0) * ACRE_TO_HA
	mean_yield = yield_mat.mean(axis=0).reindex(col_order) * BUAC_TO_KGHA
	acres_vals = mean_acres.values
	yield_vals = mean_yield.values  # may have NaN for yield
	irr_map = {'YES': '#2e7d32', 'NO': '#c62828'}
	colors = [irr_map[next(irr for name, _, irr in COUNTIES if name == c)] for c in counties]
	n = len(counties)
	y_pos = np.arange(n)

	fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
	# Left: mean soybean acres planted
	bars1 = ax1.barh(y_pos, acres_vals, color=colors, height=0.7, edgecolor='black', linewidth=0.5)
	ax1.set_yticks(y_pos)
	ax1.set_yticklabels([f"{c}  (Irrig: {next(irr for _n, _, irr in COUNTIES if _n == c)})" for c in counties], fontsize=10)
	ax1.set_xlabel("Mean soybean area planted (ha) (2018, 2020, 2022, 2023)")
	ax1.set_title("Area planted (ha)", fontsize=12, fontweight="bold")
	ax1.invert_yaxis()  # top = lowest acres so pattern is clear (low → high)
	ref_ha = 20000 * ACRE_TO_HA
	ax1.axvline(ref_ha, color='gray', linestyle='--', linewidth=1, alpha=0.8)
	ax1.text(ref_ha * 1.025, n - 0.5, "~8.1k ha", fontsize=9, color='gray', va='center')
	ax1.set_xlim(0, None)

	# Right: horizontal boxplots to show yield variability (kg/ha)
	box_data = [(yield_mat[c].dropna() * BUAC_TO_KGHA).values for c in counties]
	bp = ax2.boxplot(
		box_data, vert=False, positions=y_pos, widths=0.55,
		patch_artist=True, showmeans=True,
		meanprops=dict(marker='D', markerfacecolor='black', markeredgecolor='black', markersize=6),
		medianprops=dict(color='black', linewidth=1.5),
		flierprops=dict(marker='o', markersize=5),
	)
	for patch, col in zip(bp['boxes'], colors):
		patch.set_facecolor(col)
		patch.set_alpha(0.85)
		patch.set_edgecolor('black')
	ax2.set_yticks(y_pos)
	ax2.set_yticklabels([])
	ax2.set_xlabel("Soybean yield (kg/ha)")
	ax2.set_title("Yield variability (2018–2023)", fontsize=12, fontweight="bold")
	ax2.set_xlim(25 * BUAC_TO_KGHA, 60 * BUAC_TO_KGHA)

	# Legend: to the right of the right panel so it doesn't cover the title
	leg = [
		Patch(facecolor=irr_map['YES'], edgecolor='black', label='Irrigated'),
		Patch(facecolor=irr_map['NO'], edgecolor='black', label='Not irrigated'),
	]
	ax2.legend(handles=leg, loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=10, frameon=True)

	fig.suptitle("Soybean area and yield (SI) — SaLo > 8% counties (ordered by area)", fontsize=12, fontweight='bold', y=1.02)
	plt.tight_layout(rect=[0, 0.02, 1, 0.96])
	out_bar = f"{OUTPUT_DIR}/SaLo_Counties_Acres_and_Yield_Bars.png"
	plt.savefig(out_bar, dpi=300, bbox_inches='tight')
	plt.close()
	print(f"Saved: {out_bar}")


if __name__ == '__main__':
	main()
