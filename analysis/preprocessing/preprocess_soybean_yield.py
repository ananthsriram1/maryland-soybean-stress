#!/usr/bin/env python3
"""
Preprocess soybean yield data (1997-2024) into the canonical county-year tables.

Inputs:
  data/nass/YieldBu:Acre97to25.csv
    NASS Quick Stats county-level export with Year, County, Ag District,
    and Value (Bu/Acre).

Outputs:
  data/county_yield_all.csv (canonical per-county dataset)
  data/processed_yield/yield_clean_long_format.csv
  data/processed_yield/yield_wide_by_county.csv
  data/processed_yield/yield_<district>.csv (one per ag district)
  data/processed_yield/by_county/<county>.csv (one per county)
  data/processed_yield/yield_summary_by_county.csv
  data/processed_yield/yield_district_averages_by_year.csv
  data/processed_yield/yield_district_wide.csv
  data/processed_yield/yield_2014_2024.csv
  data/processed_yield/yield_census_years.csv
  data/processed_yield/yield_data_quality_report.csv

Paper figures:
  - Feeds Figure 4 (historical yield trends by district;
    analysis/figures/figure04_yield_4block.py).
  - Feeds Figure 6 (yield by drought class boxplots;
    analysis/figures/figure06_drought_class_yield_boxplots.py).
  - Feeds Figure 10 (>8% sandy loam counties yield;
    analysis/figures/figure10_salo_counties_yield.py).
  - Feeds the supporting yield-vs-drought analyses under
    analysis/stress_analysis/.

Author: Maryland Soybean Stress Project
"""

import os
import pandas as pd
import numpy as np

# District mapping
district_codes = {
    10: 'WESTERN',
    20: 'NORTH CENTRAL',
    30: 'UPPER EASTERN SHORE',
    80: 'SOUTHERN',
    90: 'LOWER EASTERN SHORE',
    99: 'OTHER'
}

district_counties = {
    'WESTERN': {'Allegany', 'Garrett'},
    'UPPER EASTERN SHORE': {'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'},
    'SOUTHERN': {'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"},
    'NORTH CENTRAL': {'Baltimore', 'Baltimore City', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 'Washington'},
    'LOWER EASTERN SHORE': {'Dorchester', 'Somerset', 'Wicomico', 'Worcester'}
}


def load_and_clean_yield_data():
    """Load and clean the comprehensive yield dataset."""
    print("🔄 Loading yield data (1997-2024)...")
    
    df = pd.read_csv('data/nass/YieldBu:Acre97to25.csv')
    
    print(f"   📊 Raw data: {len(df)} records")
    print(f"   📅 Years: {df['Year'].min()} to {df['Year'].max()}")
    
    # Clean year
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['Year'])
    df['Year'] = df['Year'].astype(int)
    
    # Clean county names
    df['County'] = df['County'].astype(str).str.strip()
    
    # Standardize county name variations
    df['County'] = df['County'].str.replace('QUEEN ANNES', "QUEEN ANNE'S", regex=False)
    df['County'] = df['County'].str.replace('PRINCE GEORGES', "PRINCE GEORGE'S", regex=False)
    df['County'] = df['County'].str.replace('ST MARYS', "ST. MARY'S", regex=False)
    
    # Clean yield values
    df['Value'] = df['Value'].astype(str).str.strip()
    df['Value'] = df['Value'].str.replace(',', '', regex=False)
    df['Yield'] = pd.to_numeric(df['Value'], errors='coerce')
    
    # Clean CV values
    df['CV'] = pd.to_numeric(df['CV (%)'], errors='coerce')
    
    # Map district codes to names
    df['Ag District Code'] = pd.to_numeric(df['Ag District Code'], errors='coerce')
    df['District'] = df['Ag District Code'].map(district_codes)
    
    # For counties without district codes, map by name
    county_to_district = {}
    for district, counties in district_counties.items():
        for county in counties:
            county_to_district[county.upper()] = district
    
    missing_district = df['District'].isna()
    df.loc[missing_district, 'District'] = df.loc[missing_district, 'County'].str.upper().map(county_to_district)
    
    # Create clean dataframe
    clean_df = df[[
        'Year', 'County', 'District', 'Ag District Code', 
        'Yield', 'CV', 'Program'
    ]].copy()
    
    # Remove records with missing yield
    clean_df = clean_df.dropna(subset=['Yield'])
    
    # Flag "OTHER" counties
    clean_df['Is_Other_Combined'] = clean_df['County'].str.contains('OTHER', case=False, na=False)
    
    print(f"   ✅ Clean data: {len(clean_df)} records")
    print(f"   📍 Counties: {clean_df['County'].nunique()}")
    print(f"   🏛️  Districts: {sorted(clean_df['District'].dropna().unique())}")
    
    return clean_df


def create_output_formats(df):
    """Generate multiple clean CSV formats."""
    print("\n📁 Creating output CSV files...")
    
    output_base = 'data/processed_yield'
    os.makedirs(output_base, exist_ok=True)
    
    # Remove OTHER counties for most outputs
    df_no_other = df[~df['Is_Other_Combined']].copy()
    
    # Format 0: Canonical per-county yield dataset (all numbers, one file)
    print("   📄 Format 0: Per-county yield dataset (data/county_yield_all.csv)...")
    out_cols = df_no_other[['Year', 'County', 'District', 'Ag District Code', 'Yield', 'CV', 'Program']].copy()
    out_cols = out_cols.rename(columns={'Ag District Code': 'Ag_District_Code', 'Yield': 'Yield_Bu_Acre', 'CV': 'CV_Pct'})
    out_cols.to_csv('data/county_yield_all.csv', index=False)
    print(f"      💾 Saved: data/county_yield_all.csv ({len(out_cols)} records)")

    # Format 1: Clean long format (all data)
    print("   📄 Format 1: Clean long format...")
    df_no_other.to_csv(f'{output_base}/yield_clean_long_format.csv', index=False)
    print(f"      💾 Saved: yield_clean_long_format.csv ({len(df_no_other)} records)")
    
    # Format 2: Wide format by county (years as columns)
    print("   📄 Format 2: Wide format (counties x years)...")
    wide_df = df_no_other.pivot_table(
        index='County', 
        columns='Year', 
        values='Yield', 
        aggfunc='first'
    )
    wide_df.to_csv(f'{output_base}/yield_wide_by_county.csv')
    print(f"      💾 Saved: yield_wide_by_county.csv ({len(wide_df)} counties x {len(wide_df.columns)} years)")
    
    # Format 3: One file per district
    print("   📄 Format 3: Separate files by district...")
    for district in sorted(df_no_other['District'].dropna().unique()):
        district_df = df_no_other[df_no_other['District'] == district].copy()
        filename = f"{output_base}/yield_{district.lower().replace(' ', '_')}.csv"
        district_df.to_csv(filename, index=False)
        print(f"      💾 Saved: {os.path.basename(filename)} ({len(district_df)} records)")
    
    # Format 4: One file per county
    print("   📄 Format 4: Separate files by county...")
    county_dir = f'{output_base}/by_county'
    os.makedirs(county_dir, exist_ok=True)
    
    for county in sorted(df_no_other['County'].unique()):
        if county not in ['OTHER COUNTIES', 'OTHER (COMBINED) COUNTIES']:
            county_df = df_no_other[df_no_other['County'] == county].copy()
            county_clean = county.lower().replace(' ', '_').replace("'", '')
            filename = f"{county_dir}/yield_{county_clean}.csv"
            county_df.to_csv(filename, index=False)
    print(f"      💾 Saved {df_no_other['County'].nunique()} county files")
    
    # Format 5: Summary statistics by county
    print("   📄 Format 5: Summary statistics by county...")
    summary = df_no_other.groupby(['County', 'District']).agg({
        'Yield': ['count', 'mean', 'std', 'min', 'max', 'median'],
        'CV': 'mean',
        'Year': ['min', 'max']
    }).round(2)
    summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
    summary = summary.reset_index()
    summary.to_csv(f'{output_base}/yield_summary_by_county.csv', index=False)
    print(f"      💾 Saved: yield_summary_by_county.csv")
    
    # Format 6: District averages by year
    print("   📄 Format 6: District averages by year...")
    district_avg = df_no_other.groupby(['District', 'Year']).agg({
        'Yield': ['mean', 'std', 'count'],
        'CV': 'mean'
    }).round(2)
    district_avg.columns = ['_'.join(col).strip() for col in district_avg.columns.values]
    district_avg = district_avg.reset_index()
    district_avg.to_csv(f'{output_base}/yield_district_averages_by_year.csv', index=False)
    print(f"      💾 Saved: yield_district_averages_by_year.csv")
    
    # Format 7: Wide format by district (years as columns)
    print("   📄 Format 7: Wide format by district...")
    district_wide = district_avg.pivot_table(
        index='District',
        columns='Year',
        values='Yield_mean',
        aggfunc='first'
    )
    district_wide.to_csv(f'{output_base}/yield_district_wide.csv')
    print(f"      💾 Saved: yield_district_wide.csv")
    
    # Format 8: Recent years only (2014-2024)
    print("   📄 Format 8: Recent period (2014-2024) subset...")
    recent_df = df_no_other[df_no_other['Year'] >= 2014].copy()
    recent_df.to_csv(f'{output_base}/yield_2014_2024.csv', index=False)
    print(f"      💾 Saved: yield_2014_2024.csv ({len(recent_df)} records)")
    
    # Format 9: Census years only (to match irrigation data)
    print("   📄 Format 9: Census years only (1997, 2002, 2007, 2012, 2017, 2022)...")
    census_years = [1997, 2002, 2007, 2012, 2017, 2022]
    census_df = df_no_other[df_no_other['Year'].isin(census_years)].copy()
    census_df.to_csv(f'{output_base}/yield_census_years.csv', index=False)
    print(f"      💾 Saved: yield_census_years.csv ({len(census_df)} records)")
    
    # Format 10: Data quality report
    print("   📄 Format 10: Data quality report...")
    quality = []
    for county in sorted(df_no_other['County'].unique()):
        county_data = df_no_other[df_no_other['County'] == county]
        quality.append({
            'County': county,
            'District': county_data['District'].iloc[0] if len(county_data) > 0 else None,
            'Years_Available': len(county_data),
            'First_Year': county_data['Year'].min(),
            'Last_Year': county_data['Year'].max(),
            'Missing_Years': 28 - len(county_data),  # 1997-2024 = 28 years
            'Avg_Yield': county_data['Yield'].mean(),
            'Yield_Std': county_data['Yield'].std(),
            'Avg_CV': county_data['CV'].mean()
        })
    quality_df = pd.DataFrame(quality).round(2)
    quality_df.to_csv(f'{output_base}/yield_data_quality_report.csv', index=False)
    print(f"      💾 Saved: yield_data_quality_report.csv")
    
    print(f"\n✅ All formats created in: {output_base}/")


def main():
    """Run the preprocessing workflow."""
    print("=" * 80)
    print("YIELD DATA PREPROCESSING (1997-2024)")
    print("=" * 80)
    
    clean_df = load_and_clean_yield_data()
    create_output_formats(clean_df)
    
    print("\n" + "=" * 80)
    print("✅ Preprocessing complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

