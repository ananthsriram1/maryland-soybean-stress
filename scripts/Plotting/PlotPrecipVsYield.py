#!/usr/bin/env python3
"""
Precipitation vs Yield Correlation Analysis by Agricultural District

Creates scatter plots showing growing season precipitation against soybean yield
for each Maryland agricultural district, highlighting individual counties.

Author: Analysis for Maryland Soybean Stress Project
"""

import os
import warnings
from calendar import month_abbr
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
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
        print("⚠️  Using default matplotlib style")

sns.set_palette("husl")


def format_month_range(months):
    months = sorted(set(months))
    if not months:
        return ""

    consecutive = all(b - a == 1 for a, b in zip(months, months[1:]))
    month_names = [month_abbr[m] for m in months]

    if consecutive:
        return f"{month_names[0]}-{month_names[-1]}"

    return ", ".join(month_names)

# Agricultural district mapping (shared with other scripts)
district_counties = {
    'WESTERN': {'Allegany', 'Garrett'},
    'UPPER EASTERN SHORE': {'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'},
    'SOUTHERN': {'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"},
    'NORTH CENTRAL': {'Baltimore', 'Baltimore City', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 'Washington'},
    'LOWER EASTERN SHORE': {'Dorchester', 'Somerset', 'Wicomico', 'Worcester'}
}

district_codes = {
    10: 'WESTERN',
    20: 'NORTH CENTRAL',
    30: 'UPPER EASTERN SHORE',
    80: 'SOUTHERN',
    90: 'LOWER EASTERN SHORE'
}

UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',
    'SOUTHERN': '#90EE90',
    'LOWER EASTERN SHORE': '#4ECDC4',
    'UPPER EASTERN SHORE': '#9370DB',
    'WESTERN': '#FFD700'
}


def load_and_prepare_yield_data():
    """Load and prepare NASS soybean yield data."""
    print("🔄 Loading yield data...")

    try:
        yield_df = pd.read_csv('data/nass/Soybean_Yield_BU:Acre_By_County.csv')
        yield_df = yield_df[yield_df['Year'] != 'Year']
        yield_df['Year'] = yield_df['Year'].astype(str).str.strip()
        yield_df = yield_df[yield_df['Year'].str.isdigit()]
        yield_df['Year'] = yield_df['Year'].astype(int)
        yield_df = yield_df[(yield_df['Year'] >= 2014) & (yield_df['Year'] <= 2024)]
        yield_df['County'] = yield_df['County'].astype(str).str.strip()
        yield_df['Ag District'] = yield_df['Ag District'].astype(str).str.strip()
        yield_df['Value'] = pd.to_numeric(yield_df['Value'], errors='coerce')
        yield_df = yield_df.dropna(subset=['Value', 'County', 'Ag District'])

        other_mask = yield_df['County'].str.contains('OTHER', case=False, na=False)
        if other_mask.any():
            print(f"   🚫 Removing {other_mask.sum()} 'Other (Combined)' county records")
            yield_df = yield_df[~other_mask]

        print(f"   ✅ Yield data loaded: {len(yield_df)} records")
        print(f"   📅 Years: {sorted(yield_df['Year'].unique())}")
        print(f"   🏛️  Districts: {sorted(yield_df['Ag District'].unique())}")
        print(f"   📍 Counties: {len(yield_df['County'].unique())}")

        return yield_df

    except Exception as exc:
        print(f"   ❌ Error loading yield data: {exc}")
        return None


def load_and_prepare_precip_data(months=None, label_suffix=""):
    """Load and prepare precipitation data for selected months."""
    if months is None:
        months = [4, 5, 6, 7, 8, 9, 10]

    month_label = "-".join(str(m) for m in sorted(months))
    if label_suffix:
        month_label = label_suffix

    print(f"🔄 Loading precipitation data for months: {sorted(months)} ({month_label})")

    try:
        precip_df = pd.read_csv('data/maryland_precipitation_combined_wide.csv', index_col='County')
        print(f"   ✅ Precipitation data loaded: {len(precip_df)} counties")
        print(f"   📅 Date columns: {len(precip_df.columns)}")

        precip_long = precip_df.reset_index().melt(
            id_vars='County',
            var_name='date_col',
            value_name='Precipitation'
        )

        precip_long['date'] = precip_long['date_col'].str.replace('Precip_', '')
        precip_long['date'] = pd.to_datetime(precip_long['date'])
        precip_long['Year'] = precip_long['date'].dt.year
        precip_long = precip_long[(precip_long['Year'] >= 2014) & (precip_long['Year'] <= datetime.now().year)]
        precip_long = precip_long[precip_long['date'].dt.month.isin(months)]
        precip_long['County'] = precip_long['County'].str.upper().str.strip()
        precip_long['Precipitation'] = pd.to_numeric(precip_long['Precipitation'], errors='coerce')
        precip_long = precip_long.dropna(subset=['Precipitation'])

        print(f"   ✅ Precipitation data processed: {len(precip_long)} records")
        print(f"   📅 Years: {sorted(precip_long['Year'].unique())}")
        print(f"   📍 Counties: {len(precip_long['County'].unique())}")

        return precip_long

    except Exception as exc:
        print(f"   ❌ Error loading precipitation data: {exc}")
        return None


def map_counties_to_districts(df, county_col='County'):
    """Attach agricultural district labels to a dataframe using county names or codes."""
    print("🔄 Mapping counties to agricultural districts...")

    if 'Ag District' in df.columns and 'Ag District Code' in df.columns:
        print("   📊 Using existing Ag District and Ag District Code columns...")
        df['Ag District Code'] = pd.to_numeric(df['Ag District Code'], errors='coerce')
        df['Ag District'] = df['Ag District Code'].map(district_codes)

        missing_districts = df['Ag District'].isna() & df['Ag District Code'].notna()
        if missing_districts.any():
            print(f"   ⚠️  Found {missing_districts.sum()} records with codes but missing district names")
    else:
        print("   📊 Using county name mapping...")
        county_to_district = {}
        for district, county_set in district_counties.items():
            for county in county_set:
                county_to_district[county.upper()] = district
                if county == "Queen Anne's":
                    county_to_district['QUEEN ANNES'] = district
                elif county == "Prince George's":
                    county_to_district['PRINCE GEORGES'] = district
                elif county == "St. Mary's":
                    county_to_district['ST MARYS'] = district

        df['Ag District'] = df[county_col].str.upper().map(county_to_district)

    df = df.dropna(subset=['Ag District'])

    print(f"   ✅ District mapping completed: {len(df)} records with districts")
    print(f"   🏛️  Districts: {sorted(df['Ag District'].unique())}")
    print("   📍 Counties per district:")
    for district in sorted(df['Ag District'].unique()):
        district_counties_found = df[df['Ag District'] == district][county_col].unique()
        print(f"      {district}: {len(district_counties_found)} counties")
        for county in sorted(district_counties_found):
            print(f"        - {county}")

    return df


def prepare_combined_data(yield_df, precip_long, label_suffix=""):
    """Combine yield and precipitation data by county and year."""
    print("🔄 Combining yield and precipitation data...")

    precip_avg = precip_long.groupby(['County', 'Year'])['Precipitation'].mean().reset_index()
    precip_avg = precip_avg.rename(columns={'Precipitation': 'Avg_Growing_Season_Precip'})

    combined_df = pd.merge(yield_df, precip_avg, on=['County', 'Year'], how='inner')

    if label_suffix:
        print(f"   ✅ Combined data prepared ({label_suffix}): {len(combined_df)} records")
    else:
        print(f"   ✅ Combined data prepared: {len(combined_df)} records")
    print(f"   📅 Years: {sorted(combined_df['Year'].unique())}")
    print(f"   🏛️  Districts: {sorted(combined_df['Ag District'].unique())}")
    print("   📍 Records per district:")
    for district in sorted(combined_df['Ag District'].unique()):
        district_data = combined_df[combined_df['Ag District'] == district]
        print(f"      {district}: {len(district_data)} records")
        for county in sorted(district_data['County'].unique()):
            count = len(district_data[district_data['County'] == county])
            print(f"        - {county}: {count} records")

    return combined_df


def create_precip_vs_yield_plots(combined_df, months, label_suffix=""):
    """Generate district-level scatter plots of precipitation vs yield."""
    if label_suffix:
        print(f"\n📊 Creating Precipitation vs Yield plots ({label_suffix}) by district...")
    else:
        print("\n📊 Creating Precipitation vs Yield correlation plots by district...")

    output_dir = 'outputs/YieldAnalysis'
    os.makedirs(output_dir, exist_ok=True)

    precip_min = combined_df['Avg_Growing_Season_Precip'].min() - 0.5
    precip_max = combined_df['Avg_Growing_Season_Precip'].max() + 0.5
    yield_min = combined_df['Value'].min() - 2
    yield_max = combined_df['Value'].max() + 2

    print("   📏 Setting consistent axis ranges:")
    print(f"      Precipitation: {precip_min:.1f} to {precip_max:.1f} inches")
    print(f"      Yield: {yield_min:.1f} to {yield_max:.1f} Bu/Acre")

    month_label = format_month_range(months)

    for district in sorted(combined_df['Ag District'].unique()):
        district_data = combined_df[combined_df['Ag District'] == district]
        if district_data.empty:
            continue

        fig, ax = plt.subplots(figsize=(10, 8))
        district_color = UNIVERSAL_DISTRICT_COLORS.get(district, '#808080')

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
                county_data['Avg_Growing_Season_Precip'],
                county_data['Value'],
                s=110,
                alpha=0.85,
                edgecolors='black',
                linewidth=0.9,
                color=county_color,
                label=label
            )

            if label:
                labels_added.add(county)

            if not county_data.empty:
                latest_idx = county_data['Year'].idxmax()
                latest_point = county_data.loc[latest_idx]
                ax.annotate(
                    county,
                    xy=(latest_point['Avg_Growing_Season_Precip'], latest_point['Value']),
                    xytext=(6, 6),
                    textcoords='offset points',
                    fontsize=9,
                    fontweight='semibold',
                    color=county_color,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.7)
                )

        if (
            len(district_data) >= 2 and
            district_data['Avg_Growing_Season_Precip'].nunique() > 1 and
            district_data['Value'].nunique() > 1
        ):
            correlation, p_value = stats.pearsonr(
                district_data['Avg_Growing_Season_Precip'],
                district_data['Value']
            )
        else:
            correlation, p_value = (np.nan, np.nan)

        if not np.isnan(correlation):
            z = np.polyfit(
                district_data['Avg_Growing_Season_Precip'],
                district_data['Value'],
                1
            )
            trend_fn = np.poly1d(z)
            x_vals = np.linspace(precip_min, precip_max, 200)
            ax.plot(
                x_vals,
                trend_fn(x_vals),
                color=district_color,
                linestyle='--',
                linewidth=2.2,
                alpha=0.9,
                label='Trend line'
            )

        title_suffix = f" ({label_suffix})" if label_suffix else ""
        ax.set_title(
            f'Precipitation vs Soybean Yield{title_suffix}\n{district} Agricultural District',
            fontsize=16,
            fontweight='bold',
            pad=20
        )
        ax.set_xlabel(f'Average Precipitation ({month_label}, inches)', fontsize=12)
        ax.set_ylabel('Yield (Bu/Acre)', fontsize=12)
        ax.set_xlim(precip_min, precip_max)
        ax.set_ylim(yield_min, yield_max)
        ax.grid(True, alpha=0.3)

        n_counties = district_data['County'].nunique()
        n_years = district_data['Year'].nunique()
        avg_precip = district_data['Avg_Growing_Season_Precip'].mean()
        avg_yield = district_data['Value'].mean()

        stats_text = 'District Statistics:\n'
        stats_text += f'Counties: {n_counties}\n'
        stats_text += f'Years: {n_years}\n'
        stats_text += f'Data Points: {len(district_data)}\n'
        stats_text += f'Avg Precip: {avg_precip:.1f} in\n'
        stats_text += f'Avg Yield: {avg_yield:.1f} Bu/Acre\n\n'
        stats_text += 'Correlation Analysis:\n'

        if np.isnan(correlation):
            stats_text += 'Correlation: N/A\n'
            stats_text += 'P-value: N/A\n'
            stats_text += 'R²: N/A'
            interpretation = 'Insufficient variation\n(Correlation not available)'
        else:
            stats_text += f'Correlation: {correlation:.3f}\n'
            stats_text += f'P-value: {p_value:.3f}\n'
            stats_text += f'R²: {correlation**2:.3f}'

            if correlation > 0.3:
                interpretation = "Strong positive correlation\n(Wetter seasons = Higher yield)"
            elif correlation > 0.1:
                interpretation = "Moderate positive correlation"
            elif correlation > -0.1:
                interpretation = "Weak correlation\n(Little relationship)"
            elif correlation > -0.3:
                interpretation = "Moderate negative correlation"
            else:
                interpretation = "Strong negative correlation"

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

        if len(counties) <= 15:
            ax.legend(loc='lower left', bbox_to_anchor=(0, -0.25), ncol=3, fontsize=9)

        plt.tight_layout()

        filename_suffix = f'_{label_suffix}' if label_suffix else ''
        filename = f"{output_dir}/Precip_vs_Yield_{district.replace(' ', '_')}{filename_suffix}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   💾 Saved: {filename}")

        plt.show()
        plt.close()


def print_summary_statistics(combined_df, label_suffix=""):
    """Print summary statistics for precipitation vs yield analysis."""
    if label_suffix:
        print(f"\n📊 PRECIPITATION VS YIELD CORRELATION ANALYSIS SUMMARY ({label_suffix})")
    else:
        print("\n📊 PRECIPITATION VS YIELD CORRELATION ANALYSIS SUMMARY")
    print("=" * 60)

    total_records = len(combined_df)
    total_counties = combined_df['County'].nunique()
    total_districts = combined_df['Ag District'].nunique()
    years = sorted(combined_df['Year'].unique())

    print("\n📈 Overall Statistics:")
    print(f"   Total records: {total_records}")
    print(f"   Counties: {total_counties}")
    print(f"   Districts: {total_districts}")
    print(f"   Years: {len(years)} ({min(years)}-{max(years)})")

    print("\n🔗 District Correlation Statistics:")
    for district in sorted(combined_df['Ag District'].unique()):
        district_data = combined_df[combined_df['Ag District'] == district]
        if (
            len(district_data) >= 2 and
            district_data['Avg_Growing_Season_Precip'].nunique() > 1 and
            district_data['Value'].nunique() > 1
        ):
            correlation, p_value = stats.pearsonr(
                district_data['Avg_Growing_Season_Precip'],
                district_data['Value']
            )
            print(f"   {district:20}: r={correlation:5.3f}, p={p_value:.3f}, R²={correlation**2:.3f}")
        else:
            print(f"   {district:20}: r=N/A  , p=N/A  , R²=N/A   (insufficient variation)")


def run_analysis(months=None, label_suffix=""):
    """Run the precipitation vs yield analysis workflow."""
    if months is None:
        months = [4, 5, 6, 7, 8, 9, 10]

    if label_suffix:
        print(f"🌧️  PRECIPITATION VS YIELD CORRELATION ANALYSIS ({label_suffix})")
    else:
        print("🌧️  PRECIPITATION VS YIELD CORRELATION ANALYSIS")
    print("=" * 50)

    yield_df = load_and_prepare_yield_data()
    precip_long = load_and_prepare_precip_data(months=months, label_suffix=label_suffix)

    if yield_df is None or precip_long is None:
        print("❌ Failed to load data. Exiting.")
        return

    yield_df = map_counties_to_districts(yield_df)
    precip_long = map_counties_to_districts(precip_long)

    combined_df = prepare_combined_data(yield_df, precip_long, label_suffix=label_suffix)

    create_precip_vs_yield_plots(combined_df, months=months, label_suffix=label_suffix)

    print_summary_statistics(combined_df, label_suffix=label_suffix)

    print("\n✅ Precipitation vs Yield correlation analysis completed!")
    print("📁 Output directory: outputs/YieldAnalysis/")


def main():
    run_analysis()


if __name__ == "__main__":
    main()


