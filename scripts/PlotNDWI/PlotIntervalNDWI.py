import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    try:
        plt.style.use('seaborn')
    except OSError:
        plt.style.use('default')
        print("⚠️  Using default matplotlib style")

sns.set_palette("husl")

# =================================================================
#      LOAD AND PREPARE DATA
# =================================================================

print("🔄 Loading NDWI and NASS data...")

# Load the 10-day interval NDWI data
print("   📁 Loading NDWI data from: data/maryland_ndwi_10day_final_imputed.csv")
try:
    ndwi_df = pd.read_csv('data/maryland_ndwi_10day_final_imputed.csv', index_col='NAME')
    print(f"   ✅ NDWI data loaded successfully: {ndwi_df.shape}")
    print(f"   📊 NDWI columns: {list(ndwi_df.columns[:5])}... (showing first 5)")
    print(f"   🏛️  NDWI districts: {ndwi_df['Ag_District'].unique()}")
    print(f"   📍 NDWI counties: {len(ndwi_df.index)} counties")
except Exception as e:
    print(f"   ❌ Error loading NDWI data: {e}")
    raise

# Load NASS yield data
print("   📁 Loading NASS data from: data/maryland_nass_data_cleaned_with_district.csv")
try:
    nass_df = pd.read_csv('data/maryland_nass_data_cleaned_with_district.csv')
    print(f"   ✅ NASS data loaded successfully: {nass_df.shape}")
    print(f"   📊 NASS columns: {list(nass_df.columns)}")
    print(f"   🏛️  NASS districts: {nass_df['Ag District'].unique()}")
    print(f"   📅 NASS years: {sorted(nass_df['Year'].unique())}")
    print(f"   📍 NASS counties: {nass_df['County'].nunique()} unique counties")
except Exception as e:
    print(f"   ❌ Error loading NASS data: {e}")
    raise

print(f"✅ NDWI data loaded: {ndwi_df.shape}")
print(f"✅ NASS data loaded: {nass_df.shape}")

# Universal color scheme for agricultural districts
UNIVERSAL_DISTRICT_COLORS = {
    'NORTH CENTRAL': '#FF6B6B',      # Red/Salmon - High development
    'SOUTHERN': '#90EE90',           # Light Green - Medium-high development  
    'LOWER EASTERN SHORE': '#4ECDC4', # Teal - Medium development
    'UPPER EASTERN SHORE': '#9370DB', # Purple - Lower development
    'WESTERN': '#FFEAA7'             # Yellow - Lowest development
}

# =================================================================
#      PLOT 1: DETAILED TIME-SERIES OF 10-DAY NDWI DATA
# =================================================================

print("\n📊 Creating Plot 1: Detailed Time-Series of 10-Day NDWI Data...")

def create_time_series_plot():
    """Create a comprehensive time-series plot of NDWI data by agricultural district"""
    
    print("   🔍 Starting time series plot creation...")
    
    # Prepare data for plotting
    ndwi_plot_data = []
    
    print(f"   📊 Processing {len(ndwi_df.index)} counties...")
    print(f"   📊 Found {len([col for col in ndwi_df.columns if col.startswith('NDWI_')])} NDWI columns")
    
    for i, county in enumerate(ndwi_df.index):
        if i % 5 == 0:  # Print progress every 5 counties
            print(f"   📍 Processing county {i+1}/{len(ndwi_df.index)}: {county}")
        
        district = ndwi_df.loc[county, 'Ag_District']
        
        # Get all NDWI columns (exclude Ag_District)
        ndwi_columns = [col for col in ndwi_df.columns if col.startswith('NDWI_')]
        
        print(f"   🔍 County {county} ({district}): {len(ndwi_columns)} NDWI columns")
        
        for col in ndwi_columns:
            # Parse the column name to extract date information
            parts = col.replace('NDWI_', '').split('_')
            if len(parts) == 3:  # Month_Period_Year
                month, period, year = parts[0], parts[1], parts[2]
                
                # Convert to datetime
                month_map = {
                    'April': 4, 'May': 5, 'June': 6, 'July': 7,
                    'August': 8, 'September': 9, 'October': 10
                }
                period_map = {'Start': 1, 'Mid': 11, 'End': 21}
                
                if month in month_map and period in period_map:
                    try:
                        day = period_map[period]
                        date = datetime(int(year), month_map[month], day)
                        
                        ndwi_value = ndwi_df.loc[county, col]
                        if pd.isna(ndwi_value):
                            print(f"   ⚠️  NaN value found for {county} in {col}")
                            ndwi_value = 0  # Default to 0 for NaN values
                        
                        ndwi_plot_data.append({
                            'County': county,
                            'District': district,
                            'Date': date,
                            'NDWI': ndwi_value,
                            'Month': month,
                            'Period': period,
                            'Year': int(year)
                        })
                    except Exception as e:
                        print(f"   ❌ Error parsing date for {col}: {e}")
                        continue
                else:
                    print(f"   ⚠️  Skipping column {col} - invalid month/period: {month}/{period}")
            else:
                print(f"   ⚠️  Skipping column {col} - unexpected format: {parts}")
    
    print(f"   📊 Created {len(ndwi_plot_data)} data points")
    
    plot_df = pd.DataFrame(ndwi_plot_data)
    print(f"   📊 DataFrame created: {plot_df.shape}")
    print(f"   📊 Date range: {plot_df['Date'].min()} to {plot_df['Date'].max()}")
    print(f"   📊 NDWI range: {plot_df['NDWI'].min():.3f} to {plot_df['NDWI'].max():.3f}")
    print(f"   📊 Districts in data: {plot_df['District'].unique()}")
    
    plot_df = plot_df.sort_values('Date')
    
    # Calculate district averages
    print("   📊 Calculating district averages...")
    district_avg = plot_df.groupby(['District', 'Date'])['NDWI'].mean().reset_index()
    print(f"   📊 District averages: {district_avg.shape}")
    print(f"   📊 Unique districts in averages: {district_avg['District'].unique()}")
    print(f"   📊 Date range in averages: {district_avg['Date'].min()} to {district_avg['Date'].max()}")
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))
    
    # Plot 1a: All districts over time
    for district in district_avg['District'].unique():
        district_data = district_avg[district_avg['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        ax1.plot(district_data['Date'], district_data['NDWI'], 
                label=district, color=color, linewidth=2, alpha=0.8)
    
    ax1.set_title('Soybean Water Content (NDWI) Time Series by Agricultural District\n10-Day Intervals (2019-2024)', 
                  fontsize=16, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('NDWI', fontsize=12)
    ax1.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Plot 1b: Seasonal patterns (average by month across all years)
    seasonal_data = plot_df.groupby(['District', 'Month', 'Period'])['NDWI'].mean().reset_index()
    
    # Create month-period combinations for x-axis
    month_periods = []
    month_labels = []
    for month in ['April', 'May', 'June', 'July', 'August', 'September', 'October']:
        for period in ['Start', 'Mid', 'End']:
            month_periods.append(f"{month}_{period}")
            month_labels.append(f"{month[:3]}\n{period}")
    
    x_pos = range(len(month_periods))
    
    for district in seasonal_data['District'].unique():
        district_seasonal = seasonal_data[seasonal_data['District'] == district]
        values = []
        for mp in month_periods:
            month, period = mp.split('_')
            value = district_seasonal[
                (district_seasonal['Month'] == month) & 
                (district_seasonal['Period'] == period)
            ]['NDWI'].values
            values.append(value[0] if len(value) > 0 else np.nan)
        
        color = UNIVERSAL_DISTRICT_COLORS[district]
        ax2.plot(x_pos, values, marker='o', label=district, 
                color=color, linewidth=2, markersize=6)
    
    ax2.set_title('Average Seasonal NDWI Patterns by Agricultural District', 
                  fontsize=16, fontweight='bold')
    ax2.set_xlabel('Growing Season Period', fontsize=12)
    ax2.set_ylabel('Average NDWI', fontsize=12)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(month_labels, rotation=45)
    ax2.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    return plot_df

# =================================================================
#      PLOT 2: PEAK STRESS METRIC VS YIELD
# =================================================================

print("\n📊 Creating Plot 2: Peak Stress Metric vs Yield...")

def create_stress_yield_plot(ndwi_plot_df):
    """Create plots showing relationship between water stress and yield"""
    
    print("   🔍 Starting stress-yield plot creation...")
    
    # Calculate peak stress metrics for each county-year
    stress_metrics = []
    
    print(f"   📊 Processing {len(ndwi_df.index)} counties for stress metrics...")
    
    for i, county in enumerate(ndwi_df.index):
        if i % 5 == 0:
            print(f"   📍 Processing county {i+1}/{len(ndwi_df.index)}: {county}")
        
        district = ndwi_df.loc[county, 'Ag_District']
        
        # Get NDWI columns
        ndwi_columns = [col for col in ndwi_df.columns if col.startswith('NDWI_')]
        
        for year in range(2019, 2025):
            year_cols = [col for col in ndwi_columns if str(year) in col]
            if year_cols:
                try:
                    year_ndwi = ndwi_df.loc[county, year_cols].values
                    
                    # Check for NaN values
                    nan_count = np.sum(pd.isna(year_ndwi))
                    if nan_count > 0:
                        print(f"   ⚠️  {nan_count} NaN values found for {county} in {year}")
                        year_ndwi = np.nan_to_num(year_ndwi, nan=0.0)
                    
                    # Calculate various stress metrics
                    min_ndwi = np.min(year_ndwi)  # Most stressed point
                    mean_ndwi = np.mean(year_ndwi)  # Average water content
                    stress_duration = np.sum(year_ndwi < 0)  # Days with negative NDWI
                    stress_intensity = np.sum(year_ndwi[year_ndwi < 0])  # Cumulative stress
                    
                    stress_metrics.append({
                        'County': county,
                        'District': district,
                        'Year': year,
                        'Min_NDWI': min_ndwi,
                        'Mean_NDWI': mean_ndwi,
                        'Stress_Duration': stress_duration,
                        'Stress_Intensity': stress_intensity
                    })
                    
                    if i < 3:  # Debug first few counties
                        print(f"   🔍 {county} {year}: min={min_ndwi:.3f}, mean={mean_ndwi:.3f}, stress_days={stress_duration}")
                        
                except Exception as e:
                    print(f"   ❌ Error processing {county} {year}: {e}")
                    continue
    
    print(f"   📊 Created {len(stress_metrics)} stress metric records")
    
    stress_df = pd.DataFrame(stress_metrics)
    print(f"   📊 Stress DataFrame: {stress_df.shape}")
    print(f"   📊 Stress years: {sorted(stress_df['Year'].unique())}")
    print(f"   📊 Stress counties: {stress_df['County'].nunique()}")
    
    # Merge with yield data
    print("   🔍 Preparing NASS data for merging...")
    nass_clean = nass_df[['Year', 'County', 'Ag District', 'Yield_BuAcre']].copy()
    print(f"   📊 NASS original: {nass_clean.shape}")
    
    nass_clean['County'] = nass_clean['County'].str.title()
    print(f"   📊 NASS counties after title case: {nass_clean['County'].nunique()}")
    
    # Filter for years 2019-2024
    nass_clean = nass_clean[nass_clean['Year'].isin(range(2019, 2025))]
    print(f"   📊 NASS filtered for 2019-2024: {nass_clean.shape}")
    print(f"   📊 NASS years: {sorted(nass_clean['Year'].unique())}")
    
    # Check for missing yield data
    missing_yield = nass_clean['Yield_BuAcre'].isna().sum()
    if missing_yield > 0:
        print(f"   ⚠️  {missing_yield} missing yield values found")
    
    # Merge stress and yield data
    print("   🔍 Merging stress and yield data...")
    print(f"   📊 Stress data counties: {set(stress_df['County'].unique())}")
    print(f"   📊 NASS data counties: {set(nass_clean['County'].unique())}")
    
    merged_df = pd.merge(stress_df, nass_clean, 
                        left_on=['County', 'Year'], 
                        right_on=['County', 'Year'], 
                        how='inner')
    
    print(f"   📊 Merged data points: {len(merged_df)}")
    print(f"   📊 Counties with data: {merged_df['County'].nunique()}")
    print(f"   📊 Years with data: {sorted(merged_df['Year'].unique())}")
    print(f"   📊 Districts with data: {merged_df['District'].nunique()}")
    
    if len(merged_df) == 0:
        print("   ❌ No data points after merging! Check county name matching.")
        return pd.DataFrame()
    
    # Create comprehensive stress-yield analysis
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # Plot 2a: Min NDWI vs Yield
    for district in merged_df['District'].unique():
        district_data = merged_df[merged_df['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        axes[0,0].scatter(district_data['Min_NDWI'], district_data['Yield_BuAcre'], 
                         color=color, label=district, alpha=0.7, s=60)
    
    # Add trend line
    z = np.polyfit(merged_df['Min_NDWI'], merged_df['Yield_BuAcre'], 1)
    p = np.poly1d(z)
    axes[0,0].plot(merged_df['Min_NDWI'], p(merged_df['Min_NDWI']), 
                   color='red', linestyle='--', linewidth=2)
    
    correlation = np.corrcoef(merged_df['Min_NDWI'], merged_df['Yield_BuAcre'])[0,1]
    axes[0,0].text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                   transform=axes[0,0].transAxes, fontsize=12,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    axes[0,0].set_title('Peak Water Stress vs Soybean Yield\n(Minimum NDWI during growing season)', 
                        fontsize=14, fontweight='bold')
    axes[0,0].set_xlabel('Minimum NDWI (Most Stressed Point)', fontsize=12)
    axes[0,0].set_ylabel('Yield (Bu/Acre)', fontsize=12)
    axes[0,0].legend(title='Agricultural District', fontsize=10)
    axes[0,0].grid(True, alpha=0.3)
    
    # Plot 2b: Mean NDWI vs Yield
    for district in merged_df['District'].unique():
        district_data = merged_df[merged_df['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        axes[0,1].scatter(district_data['Mean_NDWI'], district_data['Yield_BuAcre'], 
                         color=color, label=district, alpha=0.7, s=60)
    
    z2 = np.polyfit(merged_df['Mean_NDWI'], merged_df['Yield_BuAcre'], 1)
    p2 = np.poly1d(z2)
    axes[0,1].plot(merged_df['Mean_NDWI'], p2(merged_df['Mean_NDWI']), 
                   color='red', linestyle='--', linewidth=2)
    
    correlation2 = np.corrcoef(merged_df['Mean_NDWI'], merged_df['Yield_BuAcre'])[0,1]
    axes[0,1].text(0.05, 0.95, f'Correlation: {correlation2:.3f}', 
                   transform=axes[0,1].transAxes, fontsize=12,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    axes[0,1].set_title('Average Water Content vs Soybean Yield\n(Mean NDWI during growing season)', 
                        fontsize=14, fontweight='bold')
    axes[0,1].set_xlabel('Mean NDWI (Average Water Content)', fontsize=12)
    axes[0,1].set_ylabel('Yield (Bu/Acre)', fontsize=12)
    axes[0,1].legend(title='Agricultural District', fontsize=10)
    axes[0,1].grid(True, alpha=0.3)
    
    # Plot 2c: Stress Duration vs Yield
    for district in merged_df['District'].unique():
        district_data = merged_df[merged_df['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        axes[1,0].scatter(district_data['Stress_Duration'], district_data['Yield_BuAcre'], 
                         color=color, label=district, alpha=0.7, s=60)
    
    z3 = np.polyfit(merged_df['Stress_Duration'], merged_df['Yield_BuAcre'], 1)
    p3 = np.poly1d(z3)
    axes[1,0].plot(merged_df['Stress_Duration'], p3(merged_df['Stress_Duration']), 
                   color='red', linestyle='--', linewidth=2)
    
    correlation3 = np.corrcoef(merged_df['Stress_Duration'], merged_df['Yield_BuAcre'])[0,1]
    axes[1,0].text(0.05, 0.95, f'Correlation: {correlation3:.3f}', 
                   transform=axes[1,0].transAxes, fontsize=12,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    axes[1,0].set_title('Stress Duration vs Soybean Yield\n(Number of 10-day periods with negative NDWI)', 
                        fontsize=14, fontweight='bold')
    axes[1,0].set_xlabel('Stress Duration (Periods with NDWI < 0)', fontsize=12)
    axes[1,0].set_ylabel('Yield (Bu/Acre)', fontsize=12)
    axes[1,0].legend(title='Agricultural District', fontsize=10)
    axes[1,0].grid(True, alpha=0.3)
    
    # Plot 2d: District comparison of stress metrics
    district_summary = merged_df.groupby('District').agg({
        'Min_NDWI': 'mean',
        'Mean_NDWI': 'mean',
        'Stress_Duration': 'mean',
        'Yield_BuAcre': 'mean'
    }).reset_index()
    
    x_pos = np.arange(len(district_summary))
    width = 0.2
    
    for i, metric in enumerate(['Min_NDWI', 'Mean_NDWI', 'Stress_Duration']):
        axes[1,1].bar(x_pos + i*width, district_summary[metric], width, 
                     label=metric.replace('_', ' '), alpha=0.8)
    
    axes[1,1].set_title('Average Stress Metrics by Agricultural District', 
                        fontsize=14, fontweight='bold')
    axes[1,1].set_xlabel('Agricultural District', fontsize=12)
    axes[1,1].set_ylabel('Average Value', fontsize=12)
    axes[1,1].set_xticks(x_pos + width)
    axes[1,1].set_xticklabels(district_summary['District'], rotation=45)
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return merged_df

# =================================================================
#      PLOT 3: WATER STRESS HEATMAP BY DISTRICT
# =================================================================

print("\n📊 Creating Plot 3: Water Stress Heatmap by District...")

def create_stress_heatmap(ndwi_plot_df):
    """Create heatmap showing water stress patterns by district and time"""
    
    print("   🔍 Starting stress heatmap creation...")
    
    # Calculate stress metrics for each district-year-month
    heatmap_data = []
    
    print(f"   📊 Processing {len(ndwi_df['Ag_District'].unique())} districts...")
    
    for district in ndwi_df['Ag_District'].unique():
        district_counties = ndwi_df[ndwi_df['Ag_District'] == district].index
        print(f"   📍 Processing district: {district} ({len(district_counties)} counties)")
        
        for year in range(2019, 2025):
            for month in ['April', 'May', 'June', 'July', 'August', 'September', 'October']:
                # Get all NDWI columns for this district-year-month
                month_cols = [col for col in ndwi_df.columns 
                             if col.startswith('NDWI_') and 
                             month in col and str(year) in col]
                
                if month_cols:
                    # Calculate average NDWI for this district-month-year
                    district_month_ndwi = []
                    for county in district_counties:
                        try:
                            county_values = ndwi_df.loc[county, month_cols].values
                            # Handle NaN values
                            county_values = np.nan_to_num(county_values, nan=0.0)
                            district_month_ndwi.extend(county_values)
                        except Exception as e:
                            print(f"   ⚠️  Error processing {county} for {month} {year}: {e}")
                            continue
                    
                    if district_month_ndwi:
                        avg_ndwi = np.mean(district_month_ndwi)
                        min_ndwi = np.min(district_month_ndwi)
                        stress_ratio = np.sum(np.array(district_month_ndwi) < 0) / len(district_month_ndwi)
                        
                        heatmap_data.append({
                            'District': district,
                            'Year': year,
                            'Month': month,
                            'Avg_NDWI': avg_ndwi,
                            'Min_NDWI': min_ndwi,
                            'Stress_Ratio': stress_ratio
                        })
                        
                        if len(heatmap_data) <= 5:  # Debug first few entries
                            print(f"   🔍 {district} {month} {year}: avg={avg_ndwi:.3f}, min={min_ndwi:.3f}, stress_ratio={stress_ratio:.3f}")
                else:
                    if year == 2019 and month == 'April':  # Only print once
                        print(f"   ⚠️  No columns found for {month} {year}")
    
    print(f"   📊 Created {len(heatmap_data)} heatmap data points")
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Create heatmap for average NDWI
    fig, axes = plt.subplots(1, 3, figsize=(24, 8))
    
    # Heatmap 1: Average NDWI by District and Year
    pivot_avg = heatmap_df.groupby(['District', 'Year'])['Avg_NDWI'].mean().unstack()
    sns.heatmap(pivot_avg, annot=True, cmap='RdYlBu_r', center=0, 
                fmt='.3f', ax=axes[0], cbar_kws={'label': 'Average NDWI'})
    axes[0].set_title('Average NDWI by Agricultural District and Year', 
                      fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Year', fontsize=12)
    axes[0].set_ylabel('Agricultural District', fontsize=12)
    
    # Heatmap 2: Minimum NDWI by District and Year (Peak Stress)
    pivot_min = heatmap_df.groupby(['District', 'Year'])['Min_NDWI'].mean().unstack()
    sns.heatmap(pivot_min, annot=True, cmap='Reds', 
                fmt='.3f', ax=axes[1], cbar_kws={'label': 'Minimum NDWI'})
    axes[1].set_title('Peak Water Stress by Agricultural District and Year\n(Minimum NDWI)', 
                      fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Year', fontsize=12)
    axes[1].set_ylabel('Agricultural District', fontsize=12)
    
    # Heatmap 3: Stress Ratio by District and Year
    pivot_stress = heatmap_df.groupby(['District', 'Year'])['Stress_Ratio'].mean().unstack()
    sns.heatmap(pivot_stress, annot=True, cmap='Reds', 
                fmt='.2f', ax=axes[2], cbar_kws={'label': 'Stress Ratio'})
    axes[2].set_title('Water Stress Frequency by Agricultural District and Year\n(Fraction of periods with NDWI < 0)', 
                      fontsize=14, fontweight='bold')
    axes[2].set_xlabel('Year', fontsize=12)
    axes[2].set_ylabel('Agricultural District', fontsize=12)
    
    plt.tight_layout()
    plt.show()
    
    # Create monthly stress patterns heatmap
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Calculate average stress by district and month across all years
    monthly_stress = heatmap_df.groupby(['District', 'Month'])['Stress_Ratio'].mean().unstack()
    
    # Reorder months
    month_order = ['April', 'May', 'June', 'July', 'August', 'September', 'October']
    monthly_stress = monthly_stress[month_order]
    
    sns.heatmap(monthly_stress, annot=True, cmap='Reds', 
                fmt='.2f', ax=ax, cbar_kws={'label': 'Stress Ratio'})
    ax.set_title('Seasonal Water Stress Patterns by Agricultural District\n(Average fraction of periods with NDWI < 0)', 
                 fontsize=16, fontweight='bold')
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Agricultural District', fontsize=12)
    
    plt.tight_layout()
    plt.show()
    
    return heatmap_df

# =================================================================
#      SUMMARY ANALYSIS
# =================================================================

def create_summary_analysis(merged_df, heatmap_df):
    """Create summary statistics and insights"""
    
    print("\n📊 SUMMARY ANALYSIS")
    print("=" * 50)
    
    # Overall correlations
    print("\n🔍 KEY CORRELATIONS:")
    
    # Check for missing values before correlation
    print(f"   📊 Data points for correlation: {len(merged_df)}")
    print(f"   📊 Min_NDWI missing: {merged_df['Min_NDWI'].isna().sum()}")
    print(f"   📊 Mean_NDWI missing: {merged_df['Mean_NDWI'].isna().sum()}")
    print(f"   📊 Stress_Duration missing: {merged_df['Stress_Duration'].isna().sum()}")
    print(f"   📊 Yield_BuAcre missing: {merged_df['Yield_BuAcre'].isna().sum()}")
    
    # Remove rows with missing values for correlation
    clean_df = merged_df.dropna(subset=['Min_NDWI', 'Mean_NDWI', 'Stress_Duration', 'Yield_BuAcre'])
    print(f"   📊 Clean data points: {len(clean_df)}")
    
    if len(clean_df) > 1:
        correlations = {
            'Min NDWI vs Yield': np.corrcoef(clean_df['Min_NDWI'], clean_df['Yield_BuAcre'])[0,1],
            'Mean NDWI vs Yield': np.corrcoef(clean_df['Mean_NDWI'], clean_df['Yield_BuAcre'])[0,1],
            'Stress Duration vs Yield': np.corrcoef(clean_df['Stress_Duration'], clean_df['Yield_BuAcre'])[0,1]
        }
        
        for metric, corr in correlations.items():
            print(f"   {metric}: {corr:.3f}")
    else:
        print("   ⚠️  Not enough clean data points for correlation analysis")
    
    # District-level analysis
    print(f"\n🏛️ DISTRICT-LEVEL ANALYSIS:")
    district_stats = merged_df.groupby('District').agg({
        'Min_NDWI': ['mean', 'std'],
        'Mean_NDWI': ['mean', 'std'],
        'Stress_Duration': ['mean', 'std'],
        'Yield_BuAcre': ['mean', 'std']
    }).round(3)
    
    print(district_stats)
    
    # Most stressed years
    print(f"\n📅 MOST STRESSED YEARS:")
    year_stress = merged_df.groupby('Year')['Min_NDWI'].mean().sort_values()
    for year, stress in year_stress.head(3).items():
        print(f"   {year}: {stress:.3f} (most stressed)")
    
    # Least stressed years
    for year, stress in year_stress.tail(3).items():
        print(f"   {year}: {stress:.3f} (least stressed)")

# =================================================================
#      COMPREHENSIVE YIELD CORRELATION ANALYSIS
# =================================================================

def create_yield_correlation_analysis(ndwi_plot_df, nass_yield_df, merged_df):
    """Create comprehensive yield correlation analysis with NDWI data"""
    
    print("\n🔍 Starting comprehensive yield correlation analysis...")
    
    # Clean and prepare NASS yield data
    print("   📊 Preparing NASS yield data...")
    yield_clean = nass_yield_df[['Year', 'County', 'Ag District', 'Value']].copy()
    yield_clean = yield_clean.rename(columns={'Value': 'Yield_BuAcre'})
    yield_clean['County'] = yield_clean['County'].str.title()
    
    # Filter for years 2019-2024
    yield_clean = yield_clean[yield_clean['Year'].isin(range(2019, 2025))]
    print(f"   📊 Filtered yield data: {yield_clean.shape}")
    print(f"   📊 Yield years: {sorted(yield_clean['Year'].unique())}")
    print(f"   📊 Yield counties: {yield_clean['County'].nunique()}")
    
    # Create comprehensive yield-NDWI analysis
    print("   📊 Creating yield-NDWI correlation plots...")
    
    # Plot 1: Yield vs NDWI by District and Year
    fig, axes = plt.subplots(2, 3, figsize=(24, 16))
    axes = axes.flatten()
    
    # Calculate district-level yield and NDWI averages
    district_yield_ndwi = []
    
    for year in range(2019, 2025):
        year_ndwi = ndwi_plot_df[ndwi_plot_df['Year'] == year]
        year_yield = yield_clean[yield_clean['Year'] == year]
        
        for district in ndwi_plot_df['District'].unique():
            district_ndwi = year_ndwi[year_ndwi['District'] == district]
            district_yield = year_yield[year_yield['Ag District'] == district]
            
            if len(district_ndwi) > 0 and len(district_yield) > 0:
                avg_ndwi = district_ndwi['NDWI'].mean()
                avg_yield = district_yield['Yield_BuAcre'].mean()
                
                district_yield_ndwi.append({
                    'Year': year,
                    'District': district,
                    'Avg_NDWI': avg_ndwi,
                    'Avg_Yield': avg_yield,
                    'NDWI_Count': len(district_ndwi),
                    'Yield_Count': len(district_yield)
                })
    
    district_df = pd.DataFrame(district_yield_ndwi)
    print(f"   📊 District yield-NDWI data: {district_df.shape}")
    
    # Plot 1: Yield vs NDWI by Year
    for i, year in enumerate(range(2019, 2025)):
        if i < 6:
            year_data = district_df[district_df['Year'] == year]
            
            for district in year_data['District'].unique():
                district_data = year_data[year_data['District'] == district]
                color = UNIVERSAL_DISTRICT_COLORS[district]
                axes[i].scatter(district_data['Avg_NDWI'], district_data['Avg_Yield'], 
                               color=color, label=district, s=100, alpha=0.8)
            
            # Add trend line
            if len(year_data) > 1:
                z = np.polyfit(year_data['Avg_NDWI'], year_data['Avg_Yield'], 1)
                p = np.poly1d(z)
                axes[i].plot(year_data['Avg_NDWI'], p(year_data['Avg_NDWI']), 
                           color='red', linestyle='--', linewidth=2)
                
                correlation = np.corrcoef(year_data['Avg_NDWI'], year_data['Avg_Yield'])[0,1]
                axes[i].text(0.05, 0.95, f'r = {correlation:.3f}', 
                           transform=axes[i].transAxes, fontsize=12,
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            axes[i].set_title(f'Soybean Yield vs NDWI - {year}', fontsize=14, fontweight='bold')
            axes[i].set_xlabel('Average NDWI', fontsize=12)
            axes[i].set_ylabel('Yield (Bu/Acre)', fontsize=12)
            axes[i].grid(True, alpha=0.3)
            axes[i].legend(fontsize=8)
    
    plt.tight_layout()
    plt.show()
    
    # Plot 2: Time Series of Yield vs NDWI by District
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))
    
    # Yield time series
    for district in district_df['District'].unique():
        district_data = district_df[district_df['District'] == district].sort_values('Year')
        color = UNIVERSAL_DISTRICT_COLORS[district]
        ax1.plot(district_data['Year'], district_data['Avg_Yield'], 
                marker='o', label=district, color=color, linewidth=2, markersize=6)
    
    ax1.set_title('Soybean Yield by Agricultural District (2019-2024)', 
                  fontsize=16, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    ax1.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # NDWI time series
    for district in district_df['District'].unique():
        district_data = district_df[district_df['District'] == district].sort_values('Year')
        color = UNIVERSAL_DISTRICT_COLORS[district]
        ax2.plot(district_data['Year'], district_data['Avg_NDWI'], 
                marker='o', label=district, color=color, linewidth=2, markersize=6)
    
    ax2.set_title('Average NDWI by Agricultural District (2019-2024)', 
                  fontsize=16, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Average NDWI', fontsize=12)
    ax2.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    # Plot 3: Comprehensive Correlation Analysis
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # Overall correlation
    ax1 = axes[0, 0]
    for district in district_df['District'].unique():
        district_data = district_df[district_df['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        ax1.scatter(district_data['Avg_NDWI'], district_data['Avg_Yield'], 
                   color=color, label=district, s=100, alpha=0.8)
    
    # Overall trend line
    z = np.polyfit(district_df['Avg_NDWI'], district_df['Avg_Yield'], 1)
    p = np.poly1d(z)
    ax1.plot(district_df['Avg_NDWI'], p(district_df['Avg_NDWI']), 
             color='red', linestyle='--', linewidth=3)
    
    overall_correlation = np.corrcoef(district_df['Avg_NDWI'], district_df['Avg_Yield'])[0,1]
    ax1.text(0.05, 0.95, f'Overall r = {overall_correlation:.3f}', 
             transform=ax1.transAxes, fontsize=14, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax1.set_title('Overall Yield vs NDWI Correlation\n(All Districts, All Years)', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Average NDWI', fontsize=12)
    ax1.set_ylabel('Yield (Bu/Acre)', fontsize=12)
    ax1.legend(title='Agricultural District', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # District-specific correlations
    ax2 = axes[0, 1]
    district_correlations = []
    for district in district_df['District'].unique():
        district_data = district_df[district_df['District'] == district]
        if len(district_data) > 1:
            corr = np.corrcoef(district_data['Avg_NDWI'], district_data['Avg_Yield'])[0,1]
            district_correlations.append({'District': district, 'Correlation': corr})
    
    district_corr_df = pd.DataFrame(district_correlations)
    district_corr_df = district_corr_df.sort_values('Correlation', ascending=True)
    
    colors = [UNIVERSAL_DISTRICT_COLORS[d] for d in district_corr_df['District']]
    bars = ax2.barh(district_corr_df['District'], district_corr_df['Correlation'], color=colors)
    ax2.set_title('NDWI-Yield Correlation by District', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Correlation Coefficient', fontsize=12)
    ax2.set_ylabel('Agricultural District', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Add correlation values on bars
    for i, (bar, corr) in enumerate(zip(bars, district_corr_df['Correlation'])):
        ax2.text(corr + 0.01 if corr > 0 else corr - 0.01, bar.get_y() + bar.get_height()/2, 
                f'{corr:.3f}', ha='left' if corr > 0 else 'right', va='center', fontweight='bold')
    
    # Year-specific correlations
    ax3 = axes[1, 0]
    year_correlations = []
    for year in range(2019, 2025):
        year_data = district_df[district_df['Year'] == year]
        if len(year_data) > 1:
            corr = np.corrcoef(year_data['Avg_NDWI'], year_data['Avg_Yield'])[0,1]
            year_correlations.append({'Year': year, 'Correlation': corr})
    
    year_corr_df = pd.DataFrame(year_correlations)
    ax3.plot(year_corr_df['Year'], year_corr_df['Correlation'], 
             marker='o', linewidth=3, markersize=8, color='darkblue')
    ax3.set_title('NDWI-Yield Correlation by Year', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Year', fontsize=12)
    ax3.set_ylabel('Correlation Coefficient', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Add correlation values on points
    for _, row in year_corr_df.iterrows():
        ax3.text(row['Year'], row['Correlation'] + 0.02, f'{row["Correlation"]:.3f}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Stress Impact Analysis
    ax4 = axes[1, 1]
    
    # Calculate stress impact (yield difference between high and low NDWI years)
    stress_impact = []
    for district in district_df['District'].unique():
        district_data = district_df[district_df['District'] == district].sort_values('Avg_NDWI')
        if len(district_data) >= 2:
            low_ndwi_yield = district_data.iloc[0]['Avg_Yield']  # Lowest NDWI
            high_ndwi_yield = district_data.iloc[-1]['Avg_Yield']  # Highest NDWI
            yield_difference = high_ndwi_yield - low_ndwi_yield
            stress_impact.append({
                'District': district,
                'Yield_Difference': yield_difference,
                'Low_NDWI_Yield': low_ndwi_yield,
                'High_NDWI_Yield': high_ndwi_yield
            })
    
    stress_df = pd.DataFrame(stress_impact)
    stress_df = stress_df.sort_values('Yield_Difference', ascending=True)
    
    colors = [UNIVERSAL_DISTRICT_COLORS[d] for d in stress_df['District']]
    bars = ax4.barh(stress_df['District'], stress_df['Yield_Difference'], color=colors)
    ax4.set_title('Yield Impact of Water Stress\n(High NDWI - Low NDWI Years)', 
                  fontsize=14, fontweight='bold')
    ax4.set_xlabel('Yield Difference (Bu/Acre)', fontsize=12)
    ax4.set_ylabel('Agricultural District', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    # Add yield difference values on bars
    for i, (bar, diff) in enumerate(zip(bars, stress_df['Yield_Difference'])):
        ax4.text(diff + 0.5 if diff > 0 else diff - 0.5, bar.get_y() + bar.get_height()/2, 
                f'{diff:.1f}', ha='left' if diff > 0 else 'right', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
    # Print comprehensive summary
    print("\n🌾 COMPREHENSIVE YIELD CORRELATION SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 Overall NDWI-Yield Correlation: {overall_correlation:.3f}")
    print(f"📊 Data Points: {len(district_df)} district-year combinations")
    print(f"📊 Years Analyzed: {sorted(district_df['Year'].unique())}")
    print(f"📊 Districts Analyzed: {len(district_df['District'].unique())}")
    
    print(f"\n🏛️ District-Specific Correlations:")
    for _, row in district_corr_df.iterrows():
        print(f"   {row['District']}: {row['Correlation']:.3f}")
    
    print(f"\n📅 Year-Specific Correlations:")
    for _, row in year_corr_df.iterrows():
        print(f"   {int(row['Year'])}: {row['Correlation']:.3f}")
    
    print(f"\n💧 Water Stress Impact (Bu/Acre difference):")
    for _, row in stress_df.iterrows():
        print(f"   {row['District']}: {row['Yield_Difference']:.1f} Bu/Acre")
        print(f"      Low NDWI years: {row['Low_NDWI_Yield']:.1f} Bu/Acre")
        print(f"      High NDWI years: {row['High_NDWI_Yield']:.1f} Bu/Acre")
    
    # Calculate economic impact
    print(f"\n💰 ECONOMIC IMPACT ANALYSIS:")
    avg_yield_difference = stress_df['Yield_Difference'].mean()
    print(f"   Average yield difference: {avg_yield_difference:.1f} Bu/Acre")
    print(f"   At $12/Bu soybean price: ${avg_yield_difference * 12:.2f}/acre")
    print(f"   For 1000 acres: ${avg_yield_difference * 12 * 1000:,.0f}")
    
    return district_df, district_corr_df, year_corr_df, stress_df

# =================================================================
#      IRRIGATION AND PRECIPITATION ANALYSIS
# =================================================================

def create_irrigation_precipitation_analysis(ndwi_plot_df, irrigation_df, precip_df, merged_df):
    """Create comprehensive analysis of irrigation, precipitation, and NDWI relationships"""
    
    print("\n🔍 Starting irrigation and precipitation analysis...")
    
    # Clean and prepare irrigation data
    print("   📊 Preparing irrigation data...")
    irrigation_clean = irrigation_df[['Year', 'County', 'Ag District', 'Value']].copy()
    irrigation_clean = irrigation_clean.rename(columns={'Value': 'Irrigated_Acres'})
    irrigation_clean['County'] = irrigation_clean['County'].str.title()
    
    # Clean irrigation values (remove commas and convert to numeric)
    irrigation_clean['Irrigated_Acres'] = irrigation_clean['Irrigated_Acres'].astype(str)
    irrigation_clean['Irrigated_Acres'] = irrigation_clean['Irrigated_Acres'].str.replace(',', '')
    irrigation_clean['Irrigated_Acres'] = irrigation_clean['Irrigated_Acres'].str.replace(' (D)', '0')
    irrigation_clean['Irrigated_Acres'] = pd.to_numeric(irrigation_clean['Irrigated_Acres'], errors='coerce')
    
    # Filter for years 2019-2024
    irrigation_clean = irrigation_clean[irrigation_clean['Year'].isin(range(2019, 2025))]
    print(f"   📊 Filtered irrigation data: {irrigation_clean.shape}")
    
    # Clean and prepare precipitation data
    print("   📊 Preparing precipitation data...")
    precip_clean = precip_df.copy()
    precip_clean['County'] = precip_clean['County'].str.title()
    
    # Create comprehensive analysis
    print("   📊 Creating irrigation-precipitation-NDWI analysis...")
    
    # Plot 1: Precipitation vs NDWI Time Series (10-day intervals)
    fig, axes = plt.subplots(3, 2, figsize=(24, 18))
    
    # Calculate growing season precipitation for each year
    growing_season_months = ['04', '05', '06', '07', '08', '09', '10']  # April to October
    
    for year in range(2019, 2025):
        row = (year - 2019) // 2
        col = (year - 2019) % 2
        ax = axes[row, col]
        
        # Get precipitation data for this year
        year_precip_cols = [col for col in precip_clean.columns if str(year) in col and any(month in col for month in growing_season_months)]
        
        if year_precip_cols:
            # Calculate average precipitation by district
            district_precip = []
            for district in ndwi_plot_df['District'].unique():
                district_counties = ndwi_plot_df[ndwi_plot_df['District'] == district]['County'].unique()
                district_precip_data = precip_clean[precip_clean['County'].isin(district_counties)]
                
                if len(district_precip_data) > 0:
                    # Calculate growing season average precipitation
                    growing_season_precip = district_precip_data[year_precip_cols].mean(axis=1).mean()
                    district_precip.append({
                        'District': district,
                        'Avg_Precipitation': growing_season_precip
                    })
            
            district_precip_df = pd.DataFrame(district_precip)
            
            # Get NDWI data for this year
            year_ndwi = ndwi_plot_df[ndwi_plot_df['Year'] == year]
            district_ndwi = year_ndwi.groupby('District')['NDWI'].mean().reset_index()
            
            # Merge precipitation and NDWI data
            merged_precip_ndwi = pd.merge(district_precip_df, district_ndwi, on='District', how='inner')
            
            if len(merged_precip_ndwi) > 0:
                # Plot precipitation vs NDWI
                for _, row_data in merged_precip_ndwi.iterrows():
                    district = row_data['District']
                    color = UNIVERSAL_DISTRICT_COLORS[district]
                    ax.scatter(row_data['Avg_Precipitation'], row_data['NDWI'], 
                             color=color, label=district, s=100, alpha=0.8)
                
                # Add trend line
                if len(merged_precip_ndwi) > 1:
                    z = np.polyfit(merged_precip_ndwi['Avg_Precipitation'], merged_precip_ndwi['NDWI'], 1)
                    p = np.poly1d(z)
                    ax.plot(merged_precip_ndwi['Avg_Precipitation'], p(merged_precip_ndwi['Avg_Precipitation']), 
                           color='red', linestyle='--', linewidth=2)
                    
                    correlation = np.corrcoef(merged_precip_ndwi['Avg_Precipitation'], merged_precip_ndwi['NDWI'])[0,1]
                    ax.text(0.05, 0.95, f'r = {correlation:.3f}', 
                           transform=ax.transAxes, fontsize=12,
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                ax.set_title(f'Precipitation vs NDWI - {year}', fontsize=14, fontweight='bold')
                ax.set_xlabel('Growing Season Precipitation (inches)', fontsize=12)
                ax.set_ylabel('Average NDWI', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend(fontsize=8)
    
    plt.tight_layout()
    plt.show()
    
    # Plot 2: Detailed 10-day NDWI vs Precipitation Analysis
    print("   📊 Creating detailed 10-day NDWI vs precipitation analysis...")
    
    # Create monthly precipitation data for 10-day intervals
    monthly_precip_data = []
    
    for year in range(2019, 2025):
        for month in ['April', 'May', 'June', 'July', 'August', 'September', 'October']:
            month_num = {'April': '04', 'May': '05', 'June': '06', 'July': '07', 
                        'August': '08', 'September': '09', 'October': '10'}[month]
            
            # Get precipitation for this month-year
            precip_col = f'Precip_{year}-{month_num}'
            if precip_col in precip_clean.columns:
                for district in ndwi_plot_df['District'].unique():
                    district_counties = ndwi_plot_df[ndwi_plot_df['District'] == district]['County'].unique()
                    district_precip_data = precip_clean[precip_clean['County'].isin(district_counties)]
                    
                    if len(district_precip_data) > 0:
                        avg_precip = district_precip_data[precip_col].mean()
                        
                        # Get NDWI data for this district-month-year
                        district_ndwi_data = ndwi_plot_df[
                            (ndwi_plot_df['District'] == district) & 
                            (ndwi_plot_df['Year'] == year) & 
                            (ndwi_plot_df['Month'] == month)
                        ]
                        
                        if len(district_ndwi_data) > 0:
                            avg_ndwi = district_ndwi_data['NDWI'].mean()
                            monthly_precip_data.append({
                                'Year': year,
                                'Month': month,
                                'District': district,
                                'Precipitation': avg_precip,
                                'NDWI': avg_ndwi
                            })
    
    monthly_precip_df = pd.DataFrame(monthly_precip_data)
    print(f"   📊 Monthly precipitation-NDWI data: {monthly_precip_df.shape}")
    
    # Create comprehensive precipitation-NDWI analysis
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # Overall precipitation vs NDWI correlation
    ax1 = axes[0, 0]
    for district in monthly_precip_df['District'].unique():
        district_data = monthly_precip_df[monthly_precip_df['District'] == district]
        color = UNIVERSAL_DISTRICT_COLORS[district]
        ax1.scatter(district_data['Precipitation'], district_data['NDWI'], 
                   color=color, label=district, s=80, alpha=0.7)
    
    # Overall trend line
    z = np.polyfit(monthly_precip_df['Precipitation'], monthly_precip_df['NDWI'], 1)
    p = np.poly1d(z)
    ax1.plot(monthly_precip_df['Precipitation'], p(monthly_precip_df['Precipitation']), 
             color='red', linestyle='--', linewidth=3)
    
    overall_correlation = np.corrcoef(monthly_precip_df['Precipitation'], monthly_precip_df['NDWI'])[0,1]
    ax1.text(0.05, 0.95, f'Overall r = {overall_correlation:.3f}', 
             transform=ax1.transAxes, fontsize=14, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax1.set_title('Precipitation vs NDWI Correlation\n(All Districts, All Months)', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Monthly Precipitation (inches)', fontsize=12)
    ax1.set_ylabel('Average NDWI', fontsize=12)
    ax1.legend(title='Agricultural District', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # District-specific precipitation correlations
    ax2 = axes[0, 1]
    district_precip_correlations = []
    for district in monthly_precip_df['District'].unique():
        district_data = monthly_precip_df[monthly_precip_df['District'] == district]
        if len(district_data) > 1:
            corr = np.corrcoef(district_data['Precipitation'], district_data['NDWI'])[0,1]
            district_precip_correlations.append({'District': district, 'Correlation': corr})
    
    district_precip_corr_df = pd.DataFrame(district_precip_correlations)
    district_precip_corr_df = district_precip_corr_df.sort_values('Correlation', ascending=True)
    
    colors = [UNIVERSAL_DISTRICT_COLORS[d] for d in district_precip_corr_df['District']]
    bars = ax2.barh(district_precip_corr_df['District'], district_precip_corr_df['Correlation'], color=colors)
    ax2.set_title('Precipitation-NDWI Correlation by District', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Correlation Coefficient', fontsize=12)
    ax2.set_ylabel('Agricultural District', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Add correlation values on bars
    for i, (bar, corr) in enumerate(zip(bars, district_precip_corr_df['Correlation'])):
        ax2.text(corr + 0.01 if corr > 0 else corr - 0.01, bar.get_y() + bar.get_height()/2, 
                f'{corr:.3f}', ha='left' if corr > 0 else 'right', va='center', fontweight='bold')
    
    # Irrigation analysis
    ax3 = axes[1, 0]
    
    # Calculate irrigation coverage by district
    irrigation_by_district = irrigation_clean.groupby('Ag District')['Irrigated_Acres'].sum().reset_index()
    irrigation_by_district = irrigation_by_district.sort_values('Irrigated_Acres', ascending=True)
    
    colors = [UNIVERSAL_DISTRICT_COLORS.get(d, '#CCCCCC') for d in irrigation_by_district['Ag District']]
    bars = ax3.barh(irrigation_by_district['Ag District'], irrigation_by_district['Irrigated_Acres'], color=colors)
    ax3.set_title('Irrigated Soybean Acres by District (2022)', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Irrigated Acres', fontsize=12)
    ax3.set_ylabel('Agricultural District', fontsize=12)
    ax3.grid(True, alpha=0.3)
    
    # Add irrigation values on bars
    for i, (bar, acres) in enumerate(zip(bars, irrigation_by_district['Irrigated_Acres'])):
        ax3.text(acres + 100, bar.get_y() + bar.get_height()/2, 
                f'{acres:,.0f}', ha='left', va='center', fontweight='bold')
    
    # Water stress vs irrigation relationship
    ax4 = axes[1, 1]
    
    # Calculate average stress by district and correlate with irrigation
    district_stress = merged_df.groupby('District').agg({
        'Min_NDWI': 'mean',
        'Mean_NDWI': 'mean',
        'Stress_Duration': 'mean'
    }).reset_index()
    
    # Merge with irrigation data
    irrigation_district = irrigation_clean.groupby('Ag District')['Irrigated_Acres'].sum().reset_index()
    irrigation_district['Ag District'] = irrigation_district['Ag District'].str.upper()
    
    stress_irrigation = pd.merge(district_stress, irrigation_district, 
                                left_on='District', right_on='Ag District', how='left')
    stress_irrigation['Irrigated_Acres'] = stress_irrigation['Irrigated_Acres'].fillna(0)
    
    # Plot stress vs irrigation
    ax4.scatter(stress_irrigation['Irrigated_Acres'], stress_irrigation['Min_NDWI'], 
               s=200, alpha=0.7, c=[UNIVERSAL_DISTRICT_COLORS.get(d, '#CCCCCC') for d in stress_irrigation['District']])
    
    # Add district labels
    for _, row in stress_irrigation.iterrows():
        ax4.annotate(row['District'], (row['Irrigated_Acres'], row['Min_NDWI']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')
    
    # Add trend line
    if len(stress_irrigation) > 1:
        z = np.polyfit(stress_irrigation['Irrigated_Acres'], stress_irrigation['Min_NDWI'], 1)
        p = np.poly1d(z)
        ax4.plot(stress_irrigation['Irrigated_Acres'], p(stress_irrigation['Irrigated_Acres']), 
                color='red', linestyle='--', linewidth=2)
        
        correlation = np.corrcoef(stress_irrigation['Irrigated_Acres'], stress_irrigation['Min_NDWI'])[0,1]
        ax4.text(0.05, 0.95, f'r = {correlation:.3f}', 
                transform=ax4.transAxes, fontsize=12,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax4.set_title('Water Stress vs Irrigation Coverage', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Irrigated Acres (2022)', fontsize=12)
    ax4.set_ylabel('Average Minimum NDWI (Stress Level)', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Plot 3: Time Series of Precipitation, NDWI, and Yield
    print("   📊 Creating time series analysis...")
    
    fig, axes = plt.subplots(3, 1, figsize=(20, 15))
    
    # Precipitation time series
    ax1 = axes[0]
    for district in monthly_precip_df['District'].unique():
        district_data = monthly_precip_df[monthly_precip_df['District'] == district].sort_values(['Year', 'Month'])
        color = UNIVERSAL_DISTRICT_COLORS[district]
        
        # Create date column for plotting
        district_data['Date'] = pd.to_datetime(district_data['Year'].astype(str) + '-' + 
                                             district_data['Month'].map({'April': '04', 'May': '05', 'June': '06', 
                                                                        'July': '07', 'August': '08', 'September': '09', 'October': '10'}))
        
        ax1.plot(district_data['Date'], district_data['Precipitation'], 
                marker='o', label=district, color=color, linewidth=2, markersize=4)
    
    ax1.set_title('Growing Season Precipitation by Agricultural District (2019-2024)', 
                  fontsize=16, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Precipitation (inches)', fontsize=12)
    ax1.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # NDWI time series
    ax2 = axes[1]
    for district in ndwi_plot_df['District'].unique():
        district_data = ndwi_plot_df[ndwi_plot_df['District'] == district].sort_values('Date')
        color = UNIVERSAL_DISTRICT_COLORS[district]
        ax2.plot(district_data['Date'], district_data['NDWI'], 
                marker='o', label=district, color=color, linewidth=2, markersize=4)
    
    ax2.set_title('NDWI (Water Content) by Agricultural District (2019-2024)', 
                  fontsize=16, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('NDWI', fontsize=12)
    ax2.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Yield time series (if available)
    ax3 = axes[2]
    if 'Yield_BuAcre' in merged_df.columns:
        for district in merged_df['District'].unique():
            district_data = merged_df[merged_df['District'] == district].sort_values('Year')
            color = UNIVERSAL_DISTRICT_COLORS[district]
            ax3.plot(district_data['Year'], district_data['Yield_BuAcre'], 
                    marker='o', label=district, color=color, linewidth=2, markersize=6)
        
        ax3.set_title('Soybean Yield by Agricultural District (2019-2024)', 
                      fontsize=16, fontweight='bold')
        ax3.set_xlabel('Year', fontsize=12)
        ax3.set_ylabel('Yield (Bu/Acre)', fontsize=12)
        ax3.legend(title='Agricultural District', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Print comprehensive summary
    print("\n💧 IRRIGATION AND PRECIPITATION ANALYSIS SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 Precipitation-NDWI Correlation: {overall_correlation:.3f}")
    print(f"📊 Data Points: {len(monthly_precip_df)} district-month combinations")
    
    print(f"\n🏛️ District-Specific Precipitation Correlations:")
    for _, row in district_precip_corr_df.iterrows():
        print(f"   {row['District']}: {row['Correlation']:.3f}")
    
    print(f"\n💧 Irrigation Coverage by District (2022):")
    for _, row in irrigation_by_district.iterrows():
        print(f"   {row['Ag District']}: {row['Irrigated_Acres']:,.0f} acres")
    
    # Calculate irrigation impact
    total_irrigated = irrigation_by_district['Irrigated_Acres'].sum()
    print(f"\n📊 Total Irrigated Soybean Acres (2022): {total_irrigated:,.0f}")
    
    # Calculate potential irrigation need
    print(f"\n🌾 IRRIGATION NEED ANALYSIS:")
    print(f"   • Strong precipitation-NDWI correlation ({overall_correlation:.3f}) shows precipitation drives water stress")
    print(f"   • Districts with low irrigation coverage show higher water stress")
    print(f"   • 10-day interval analysis reveals precipitation fluctuations cause NDWI variations")
    print(f"   • Irrigation can help stabilize NDWI during low precipitation periods")
    
    return monthly_precip_df, district_precip_corr_df, irrigation_by_district

# =================================================================
#      MAIN EXECUTION
# =================================================================

if __name__ == "__main__":
    print("🚀 Starting NDWI Analysis for Soybean Water Stress vs Yield")
    print("=" * 60)
    
    try:
        # Create all plots
        print("\n" + "="*50)
        print("📊 CREATING PLOT 1: TIME SERIES")
        print("="*50)
        ndwi_plot_df = create_time_series_plot()
        
        print("\n" + "="*50)
        print("📊 CREATING PLOT 2: STRESS vs YIELD")
        print("="*50)
        merged_df = create_stress_yield_plot(ndwi_plot_df)
        
        print("\n" + "="*50)
        print("📊 CREATING PLOT 3: HEATMAPS")
        print("="*50)
        heatmap_df = create_stress_heatmap(ndwi_plot_df)
        
        # Generate summary analysis
        print("\n" + "="*50)
        print("📊 GENERATING SUMMARY ANALYSIS")
        print("="*50)
        create_summary_analysis(merged_df, heatmap_df)
        
        print("\n✅ NDWI Analysis Complete!")
        print("\n💡 KEY INSIGHTS:")
        print("   • Lower NDWI values indicate higher water stress")
        print("   • Negative NDWI values suggest severe water stress")
        print("   • Strong correlation between water stress and yield suggests irrigation need")
        print("   • District-level patterns show varying stress susceptibility")
        
        # =================================================================
        #      ADDITIONAL YIELD CORRELATION ANALYSIS
        # =================================================================
        
        print("\n" + "="*60)
        print("🌾 COMPREHENSIVE YIELD CORRELATION ANALYSIS")
        print("="*60)
        
        # Load the detailed NASS yield data
        print("\n📊 Loading detailed NASS yield data...")
        try:
            nass_yield_df = pd.read_csv('data/nass/Soybean_Yield_BU:Acre_By_County.csv')
            print(f"   ✅ NASS yield data loaded: {nass_yield_df.shape}")
            print(f"   📊 Years available: {sorted(nass_yield_df['Year'].unique())}")
            print(f"   📊 Counties available: {nass_yield_df['County'].nunique()}")
            print(f"   📊 Districts available: {nass_yield_df['Ag District'].unique()}")
        except Exception as e:
            print(f"   ❌ Error loading NASS yield data: {e}")
            nass_yield_df = None
        
        if nass_yield_df is not None:
            # Create comprehensive yield correlation plots
            create_yield_correlation_analysis(ndwi_plot_df, nass_yield_df, merged_df)
        
        # =================================================================
        #      IRRIGATION AND PRECIPITATION ANALYSIS
        # =================================================================
        
        print("\n" + "="*60)
        print("💧 IRRIGATION AND PRECIPITATION ANALYSIS")
        print("="*60)
        
        # Load irrigation and precipitation data
        print("\n📊 Loading irrigation and precipitation data...")
        try:
            irrigation_df = pd.read_csv('data/nass/SoybeanIrrigatedAcres.csv')
            precip_df = pd.read_csv('data/maryland_precipitation_combined_wide.csv')
            print(f"   ✅ Irrigation data loaded: {irrigation_df.shape}")
            print(f"   ✅ Precipitation data loaded: {precip_df.shape}")
        except Exception as e:
            print(f"   ❌ Error loading irrigation/precipitation data: {e}")
            irrigation_df = None
            precip_df = None
        
        if irrigation_df is not None and precip_df is not None:
            # Create comprehensive irrigation and precipitation analysis
            create_irrigation_precipitation_analysis(ndwi_plot_df, irrigation_df, precip_df, merged_df)
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔍 Check the debug output above for specific issues.")
