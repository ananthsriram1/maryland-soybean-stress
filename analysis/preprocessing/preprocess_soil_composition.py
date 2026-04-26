#!/usr/bin/env python3
"""
Preprocess soil composition data (Band-5, soybean-pixel-only) for Maryland counties.

Reads the band-5-only CDL soybean soil composition CSVs (one row per county,
SSURGO-derived soil type counts within soybean-classified pixels) and emits
clean long, wide, summary, and dominant-soil tables.

Inputs:
  data/soybeanSoilCompositionPerCounty2018band5.csv
  data/soybeanSoilCompositionPerCounty2020band5.csv
    (These are GEE-exported tables from the Band-5 soybean soil-composition
    pipeline; they are not committed in this repository. Reproducers need to
    regenerate them from the GEE_Scripts/ exports — add a GEE_Scripts README
    pointer in Phase 4. TODO: document which GEE_Scripts/ source produces them.)

Outputs (under data/processed_band5/):
  maryland_soil_composition_processed_band5{suffix}.csv
  maryland_soil_summary_by_county_band5{suffix}.csv
  maryland_dominant_soil_by_county_band5{suffix}.csv
  maryland_soil_wide_format_band5{suffix}.csv
  soil_type_mapping_band5.csv

Paper figures:
  - Feeds Figure 2 (soil composition heatmap by district;
    analysis/figures/figure02_soil_district_heatmap.py).
  - Feeds Figure 10 (>8% sandy loam counties yield;
    analysis/figures/figure10_salo_counties_yield.py).

History:
  This is the canonical Band-5 (soybean-pixel-only) version. The earlier
  whole-county SSURGO version is preserved verbatim at
  archive/soil_legacy/PreprocessSoilData.py for traceability and is not
  used by any manuscript figure.

Author: Maryland Soybean Stress Project
"""

import pandas as pd
import ast
import os


def load_and_preprocess_soil_data(input_file: str):
	"""Load and preprocess soil composition data for Maryland counties only."""
	# Load the raw data
	df = pd.read_csv(input_file)
	print(f"📊 Loaded {len(df)} total counties from {os.path.basename(input_file)}")

	# Filter for Maryland counties (GEOID starting with 24)
	md_df = df[df['GEOID'].astype(str).str.startswith('24')].copy()
	print(f"✅ Found {len(md_df)} Maryland counties")

	# Define soil type mapping (same as main preprocessing)
	soil_type_mapping = {
		1: {'code': 'Cl', 'name': 'Clay', 'color': '#d5c36b'},
		2: {'code': 'SiCl', 'name': 'Silty Clay', 'color': '#b96947'},
		3: {'code': 'SaCl', 'name': 'Sandy Clay', 'color': '#9d3706'},
		4: {'code': 'ClLo', 'name': 'Clay Loam', 'color': '#ae868f'},
		5: {'code': 'SiClLo', 'name': 'Silty Clay Loam', 'color': '#f86714'},
		6: {'code': 'SaClLo', 'name': 'Sandy Clay Loam', 'color': '#46d143'},
		7: {'code': 'Lo', 'name': 'Loam', 'color': '#368f20'},
		8: {'code': 'SiLo', 'name': 'Silty Loam', 'color': '#3e5a14'},
		9: {'code': 'SaLo', 'name': 'Sandy Loam', 'color': '#ffd557'},
		10: {'code': 'Si', 'name': 'Silt', 'color': '#fff72e'},
		11: {'code': 'LoSa', 'name': 'Loamy Sand', 'color': '#ff5a9d'},
		12: {'code': 'Sa', 'name': 'Sand', 'color': '#ff005b'}
	}

	processed_data = []

	for _, row in md_df.iterrows():
		county_name = row['NAME']
		geoid = row['GEOID']
		histogram_str = row['histogram']

		# Parse the histogram string
		try:
			if histogram_str == '{}' or pd.isna(histogram_str):
				histogram = {}
			else:
				# Replace = with : to make it valid Python dict syntax
				histogram_str_fixed = histogram_str.replace('=', ':')
				histogram = ast.literal_eval(histogram_str_fixed)
		except Exception as e:
			print(f"⚠️  Warning: Could not parse histogram for {county_name}: {e}")
			histogram = {}

		# Calculate total area in pixels, then convert to square meters and acres
		total_pixels = sum(histogram.values()) if histogram else 0

		# Convert pixels to area (250m x 250m pixels)
		pixel_size_meters = 250
		square_meters_per_pixel = pixel_size_meters ** 2
		square_meters_per_acre = 4046.86
		total_area_sq_meters = total_pixels * square_meters_per_pixel
		total_area_acres = total_area_sq_meters / square_meters_per_acre

		county_data = {
			'County': county_name,
			'GEOID': geoid,
			'Total_Pixels': total_pixels,
			'Total_Area_SqMeters': round(total_area_sq_meters, 2),
			'Total_Area_Acres': round(total_area_acres, 2)
		}

		# Add soil type values
		for soil_id, pixels in (histogram.items() if isinstance(histogram, dict) else []):
			if soil_id in soil_type_mapping:
				soil_info = soil_type_mapping[soil_id]
				percentage = (pixels / total_pixels * 100) if total_pixels > 0 else 0
				soil_area_sq_meters = pixels * square_meters_per_pixel
				soil_area_acres = soil_area_sq_meters / square_meters_per_acre

				county_data[f"{soil_info['code']}_Pixels"] = pixels
				county_data[f"{soil_info['code']}_Area_SqMeters"] = round(soil_area_sq_meters, 2)
				county_data[f"{soil_info['code']}_Area_Acres"] = round(soil_area_acres, 2)
				county_data[f"{soil_info['code']}_Percentage"] = round(percentage, 2)
				county_data[f"{soil_info['code']}_Name"] = soil_info['name']
				county_data[f"{soil_info['code']}_Color"] = soil_info['color']

		# Ensure columns for all soil types exist
		for soil_id, soil_info in soil_type_mapping.items():
			code = soil_info['code']
			if f'{code}_Pixels' not in county_data:
				county_data[f'{code}_Pixels'] = 0
				county_data[f'{code}_Area_SqMeters'] = 0
				county_data[f'{code}_Area_Acres'] = 0
				county_data[f'{code}_Percentage'] = 0
				county_data[f'{code}_Name'] = soil_info['name']
				county_data[f'{code}_Color'] = soil_info['color']

		processed_data.append(county_data)

	processed_df = pd.DataFrame(processed_data)
	processed_df = processed_df.sort_values('County').reset_index(drop=True)
	return processed_df, soil_type_mapping


def save_processed_data(processed_df: pd.DataFrame, soil_type_mapping: dict, year_suffix: str = ""):
	"""Save processed soil data in multiple formats under data/processed_band5."""
	os.makedirs('data/processed_band5', exist_ok=True)
	print(f"\n💾 Saving processed soil data (band5){' ' + year_suffix if year_suffix else ''}...")

	file_suffix = f"_{year_suffix}" if year_suffix else ""
	processed_df.to_csv(f'data/processed_band5/maryland_soil_composition_processed_band5{file_suffix}.csv', index=False)
	print(f"   ✅ Main processed file: maryland_soil_composition_processed_band5{file_suffix}.csv")

	summary_cols = ['County', 'GEOID', 'Total_Pixels', 'Total_Area_SqMeters', 'Total_Area_Acres'] + [col for col in processed_df.columns if col.endswith('_Percentage')]
	summary_df = processed_df[summary_cols].copy()
	summary_df.to_csv(f'data/processed_band5/maryland_soil_summary_by_county_band5{file_suffix}.csv', index=False)
	print(f"   ✅ Summary file: maryland_soil_summary_by_county_band5{file_suffix}.csv")

	# Soil mapping saved once for band5
	if not year_suffix or not os.path.exists('data/processed_band5/soil_type_mapping_band5.csv'):
		soil_mapping_df = pd.DataFrame([
			{'Soil_ID': soil_id, 'Code': info['code'], 'Name': info['name'], 'Color': info['color']}
			for soil_id, info in soil_type_mapping.items()
		])
		soil_mapping_df.to_csv('data/processed_band5/soil_type_mapping_band5.csv', index=False)
		print("   ✅ Soil mapping: soil_type_mapping_band5.csv")

	dominant_soils = []
	for _, row in processed_df.iterrows():
		county = row['County']
		max_percentage = 0
		dominant_soil = None
		for col in processed_df.columns:
			if col.endswith('_Percentage'):
				soil_code = col.replace('_Percentage', '')
				percentage = row[col]
				if percentage > max_percentage:
					max_percentage = percentage
					dominant_soil = soil_code
		dominant_soils.append({
			'County': county,
			'GEOID': row['GEOID'],
			'Dominant_Soil_Code': dominant_soil,
			'Dominant_Soil_Percentage': max_percentage,
			'Dominant_Soil_Name': row[f'{dominant_soil}_Name'] if dominant_soil else 'Unknown'
		})
	pd.DataFrame(dominant_soils).to_csv(f'data/processed_band5/maryland_dominant_soil_by_county_band5{file_suffix}.csv', index=False)
	print(f"   ✅ Dominant soils: maryland_dominant_soil_by_county_band5{file_suffix}.csv")

	wide_cols = ['County'] + [col for col in processed_df.columns if col.endswith('_Percentage')]
	processed_df[wide_cols].to_csv(f'data/processed_band5/maryland_soil_wide_format_band5{file_suffix}.csv', index=False)
	print(f"   ✅ Wide format: maryland_soil_wide_format_band5{file_suffix}.csv")


def print_summary_statistics(processed_df: pd.DataFrame, soil_type_mapping: dict):
	"""Print summary statistics about the processed data."""
	print("\n" + "="*80)
	print("MARYLAND SOIL COMPOSITION SUMMARY (band5)")
	print("="*80)
	print(f"\n📊 OVERALL STATISTICS:")
	print(f"  Counties processed: {len(processed_df)}")
	print(f"  Total pixels: {processed_df['Total_Pixels'].sum():,.0f} pixels")
	print(f"  Total area: {processed_df['Total_Area_Acres'].sum():,.0f} acres")
	print(f"  Average area per county: {processed_df['Total_Area_Acres'].mean():,.0f} acres")

	print(f"\n🌱 DOMINANT SOIL TYPES:")
	soil_counts = {}
	for _, row in processed_df.iterrows():
		max_percentage = 0
		dominant_soil = None
		for col in processed_df.columns:
			if col.endswith('_Percentage'):
				soil_code = col.replace('_Percentage', '')
				percentage = row[col]
				if percentage > max_percentage:
					max_percentage = percentage
					dominant_soil = soil_code
		if dominant_soil:
			soil_counts[dominant_soil] = soil_counts.get(dominant_soil, 0) + 1
	for soil_code, count in sorted(soil_counts.items(), key=lambda x: x[1], reverse=True):
		soil_name = soil_type_mapping.get(next(k for k, v in soil_type_mapping.items() if v['code'] == soil_code), {}).get('name', 'Unknown')
		print(f"  {soil_code} ({soil_name}): {count} counties")


def main():
	"""Main function to preprocess band5 soil data."""
	print("="*80)
	print("MARYLAND SOIL COMPOSITION PREPROCESSING (Band-5 Soybeans)")
	print("="*80)

	datasets = [
		('data/soybeanSoilCompositionPerCounty2018band5.csv', '2018band5'),
		('data/soybeanSoilCompositionPerCounty2020band5.csv', '2020band5'),
	]

	for input_file, year_suffix in datasets:
		print(f"\n🔄 Processing {input_file}...")
		processed_df, soil_type_mapping = load_and_preprocess_soil_data(input_file)
		save_processed_data(processed_df, soil_type_mapping, year_suffix)
		print_summary_statistics(processed_df, soil_type_mapping)

	print(f"\n✅ All band5 soil data preprocessing complete!")
	print(f"📁 Output directory: data/processed_band5/")
	print("="*80)


if __name__ == "__main__":
	main()
