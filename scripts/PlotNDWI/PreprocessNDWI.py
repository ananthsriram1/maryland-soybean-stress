import pandas as pd
import os
import re
import numpy as np
from datetime import datetime

# =================================================================
#      SETUP: Define your data paths and county structure
# =================================================================

# The folder containing your many 10-day interval CSV files
data_folder = 'data/ndwi_ten_day_interval' 

# The name for the final, cleaned output file
output_file = 'data/maryland_ndwi_10day_final_imputed.csv'

# Your defined list of Maryland counties by district (matching PlotNDWIByDistrict.py)
district_counties = {
    'WESTERN': {'Allegany', 'Garrett'},
    'UPPER EASTERN SHORE': {'Caroline', 'Cecil', 'Kent', "Queen Anne's", 'Talbot'},
    'SOUTHERN': {'Anne Arundel', 'Calvert', 'Charles', "Prince George's", "St. Mary's"},
    'NORTH CENTRAL': {'Baltimore', 'Baltimore City', 'Carroll', 'Frederick', 'Harford', 'Howard', 'Montgomery', 'Washington'},
    'LOWER EASTERN SHORE': {'Dorchester', 'Somerset', 'Wicomico', 'Worcester'}
}

# Create a flat list of all valid Maryland county names for easy filtering
maryland_county_list = [county for district in district_counties.values() for county in district]

print(f"Target Maryland counties: {len(maryland_county_list)}")
print(f"Counties: {sorted(maryland_county_list)}")

# --- DEBUG: Check if we're missing any counties from the expected list ---
print(f"\n🔍 DEBUG: Checking for missing counties in target list...")
print(f"   Note: We expect 24 counties but only found 23 in the data")
print(f"   This suggests one county might be missing from the source data")

# =================================================================
#      PART 1: Combine, Clean, and Filter the Data
# =================================================================

def parse_filename_to_date(filename):
    """Parse filename like 'md_county_soybean_ndwi_April_Start_2023.csv' to sortable date"""
    # Remove prefix and suffix
    clean_name = filename.replace('md_county_soybean_ndwi_', '').replace('.csv', '')
    parts = clean_name.split('_')
    
    if len(parts) == 3:
        month, period, year = parts
        
        # Month mapping
        month_map = {
            'April': '04', 'May': '05', 'June': '06', 'July': '07', 
            'August': '08', 'September': '09', 'October': '10'
        }
        
        # Period mapping (Start=1, Mid=2, End=3)
        period_map = {'Start': '1', 'Mid': '2', 'End': '3'}
        
        if month in month_map and period in period_map:
            # Create sortable date string like '2023-04-1' for April_Start_2023
            sortable_date = f"{year}-{month_map[month]}-{period_map[period]}"
            return sortable_date, month, period, year
    
    return None, None, None, None

try:
    all_files = os.listdir(data_folder)
    csv_files = [f for f in all_files if f.endswith('.csv')]
    print(f"Found {len(csv_files)} NDWI CSV files to process.")
except FileNotFoundError:
    print(f"Error: The folder '{data_folder}' was not found.")
    csv_files = []

if csv_files:
    all_data_list = []
    processed_files = 0
    skipped_files = 0
    
    for filename in sorted(csv_files):  # Sort for consistent processing
        file_path = os.path.join(data_folder, filename)
        
        # Parse filename to get date information
        sortable_date, month, period, year = parse_filename_to_date(filename)
        
        if sortable_date is None:
            print(f"⚠️  Skipping file with unexpected format: {filename}")
            skipped_files += 1
            continue
            
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Check if required columns exist
            if 'NAME' not in df.columns or 'meanSoybeanNDWI' not in df.columns:
                print(f"⚠️  Skipping file missing required columns: {filename}")
                skipped_files += 1
                continue
            
            # Clean the data
            df = df.copy()
            df['NAME'] = df['NAME'].str.strip()  # Remove any whitespace
            
            # Convert meanSoybeanNDWI to numeric, replacing empty strings and 'N/A' with NaN
            df['meanSoybeanNDWI'] = pd.to_numeric(df['meanSoybeanNDWI'], errors='coerce')
            
            # Filter for Maryland counties only
            df_maryland = df[df['NAME'].isin(maryland_county_list)].copy()
            
            if len(df_maryland) == 0:
                print(f"⚠️  No Maryland counties found in: {filename}")
                skipped_files += 1
                continue
            
            # Add date information
            df_maryland['date'] = sortable_date
            df_maryland['month'] = month
            df_maryland['period'] = period
            df_maryland['year'] = year
            
            # --- DEBUG: Check for duplicates within this file ---
            if len(df_maryland) != len(df_maryland.drop_duplicates(subset=['NAME'])):
                print(f"⚠️  WARNING: {filename} contains duplicate counties!")
                dup_counties = df_maryland[df_maryland.duplicated(subset=['NAME'], keep=False)]['NAME'].unique()
                print(f"   Duplicate counties: {dup_counties}")
                # Show the duplicate records
                for county in dup_counties:
                    dup_records = df_maryland[df_maryland['NAME'] == county]
                    print(f"   {county} appears {len(dup_records)} times:")
                    print(dup_records[['NAME', 'meanSoybeanNDWI']].to_string())
            
            # --- DEBUG: Check for any unexpected county names ---
            unexpected_counties = set(df_maryland['NAME']) - set(maryland_county_list)
            if unexpected_counties:
                print(f"⚠️  WARNING: {filename} contains unexpected counties: {unexpected_counties}")
            
            all_data_list.append(df_maryland)
            processed_files += 1
            
            if processed_files % 20 == 0:  # Progress indicator
                print(f"Processed {processed_files} files...")
                
        except Exception as e:
            print(f"⚠️  Error processing {filename}: {str(e)}")
            skipped_files += 1
            continue

    print(f"\n📊 Processing Summary:")
    print(f"   Successfully processed: {processed_files} files")
    print(f"   Skipped: {skipped_files} files")
    
    if not all_data_list:
        print("❌ No data files were successfully processed!")
        exit(1)
    
    # --- Combine into a long-format DataFrame ---
    long_df = pd.concat(all_data_list, ignore_index=True)
    
    print(f"\n📈 Data Statistics:")
    print(f"   Total records: {len(long_df)}")
    print(f"   Unique counties: {long_df['NAME'].nunique()}")
    print(f"   Date range: {long_df['date'].min()} to {long_df['date'].max()}")
    print(f"   Missing values before imputation: {long_df['meanSoybeanNDWI'].isna().sum()}")
    
    # --- DEBUG: Identify missing counties ---
    actual_counties = set(long_df['NAME'].unique())
    expected_counties = set(maryland_county_list)
    missing_counties = expected_counties - actual_counties
    extra_counties = actual_counties - expected_counties
    
    print(f"\n🔍 DEBUG: County analysis:")
    print(f"   Counties found in data: {len(actual_counties)}")
    print(f"   Counties expected: {len(expected_counties)}")
    
    if missing_counties:
        print(f"   Missing counties: {sorted(missing_counties)}")
    if extra_counties:
        print(f"   Extra counties (not in target list): {sorted(extra_counties)}")
    
    print(f"   Counties in data: {sorted(actual_counties)}")
    print(f"   Counties expected: {sorted(expected_counties)}")
    
    # --- DEBUG: Check for duplicates before pivoting ---
    print(f"\n🔍 DEBUG: Checking for duplicate entries...")
    
    # Check for duplicate county-date combinations
    duplicate_check = long_df.groupby(['NAME', 'date']).size()
    duplicates = duplicate_check[duplicate_check > 1]
    
    if len(duplicates) > 0:
        print(f"❌ Found {len(duplicates)} duplicate county-date combinations:")
        for (county, date), count in duplicates.head(10).items():
            print(f"   {county} - {date}: {count} records")
        
        # Show the actual duplicate records
        print(f"\n🔍 DEBUG: Showing duplicate records:")
        for (county, date), count in duplicates.head(5).items():
            dup_records = long_df[(long_df['NAME'] == county) & (long_df['date'] == date)]
            print(f"\n   Duplicates for {county} - {date}:")
            print(dup_records[['NAME', 'date', 'meanSoybeanNDWI', 'month', 'period', 'year']].to_string())
        
        # Handle duplicates by taking the mean of duplicate values
        print(f"\n🔧 DEBUG: Aggregating duplicates by taking mean...")
        long_df_clean = long_df.groupby(['NAME', 'date']).agg({
            'meanSoybeanNDWI': 'mean',  # Take mean of duplicate values
            'month': 'first',           # Keep first occurrence for metadata
            'period': 'first',
            'year': 'first'
        }).reset_index()
        
        print(f"   Records before deduplication: {len(long_df)}")
        print(f"   Records after deduplication: {len(long_df_clean)}")
        print(f"   Removed {len(long_df) - len(long_df_clean)} duplicate records")
        
        long_df = long_df_clean
    else:
        print(f"✅ No duplicate county-date combinations found")

# =================================================================
#      PART 2: Pivot, Impute Missing Values, and Save
# =================================================================

    # --- DEBUG: Final check before pivoting ---
    print(f"\n🔍 DEBUG: Final data check before pivoting...")
    print(f"   Unique counties: {sorted(long_df['NAME'].unique())}")
    print(f"   Unique dates: {len(long_df['date'].unique())}")
    print(f"   Expected combinations: {len(long_df['NAME'].unique())} counties × {len(long_df['date'].unique())} dates = {len(long_df['NAME'].unique()) * len(long_df['date'].unique())}")
    print(f"   Actual records: {len(long_df)}")
    
    # Check if we have the expected number of records
    expected_records = len(long_df['NAME'].unique()) * len(long_df['date'].unique())
    if len(long_df) != expected_records:
        print(f"⚠️  WARNING: Expected {expected_records} records but have {len(long_df)}")
        
        # Show missing combinations
        all_combinations = pd.MultiIndex.from_product([
            long_df['NAME'].unique(), 
            long_df['date'].unique()
        ], names=['NAME', 'date'])
        
        actual_combinations = pd.MultiIndex.from_frame(long_df[['NAME', 'date']])
        missing_combinations = all_combinations.difference(actual_combinations)
        
        print(f"   Missing {len(missing_combinations)} county-date combinations:")
        for county, date in list(missing_combinations)[:10]:  # Show first 10
            print(f"     {county} - {date}")
        if len(missing_combinations) > 10:
            print(f"     ... and {len(missing_combinations) - 10} more")

    # --- Pivot to wide format for time-series imputation ---
    print(f"\n🔄 Attempting to pivot data...")
    try:
        wide_df = long_df.pivot(index='NAME', columns='date', values='meanSoybeanNDWI')
        print(f"✅ Pivot successful!")
    except Exception as e:
        print(f"❌ Pivot failed: {str(e)}")
        print(f"\n🔍 DEBUG: Detailed analysis of the issue...")
        
        # Check for any remaining duplicates
        duplicate_check_final = long_df.groupby(['NAME', 'date']).size()
        duplicates_final = duplicate_check_final[duplicate_check_final > 1]
        if len(duplicates_final) > 0:
            print(f"   Still have {len(duplicates_final)} duplicates after aggregation")
            for (county, date), count in duplicates_final.head(5).items():
                print(f"     {county} - {date}: {count} records")
        
        # Check data types
        print(f"   Data types:")
        print(f"     NAME: {long_df['NAME'].dtype}")
        print(f"     date: {long_df['date'].dtype}")
        print(f"     meanSoybeanNDWI: {long_df['meanSoybeanNDWI'].dtype}")
        
        # Check for any NaN values in index columns
        nan_in_name = long_df['NAME'].isna().sum()
        nan_in_date = long_df['date'].isna().sum()
        print(f"   NaN values in NAME: {nan_in_name}")
        print(f"   NaN values in date: {nan_in_date}")
        
        raise e
    
    # Sort the columns chronologically, which is critical for correct imputation
    wide_df = wide_df.sort_index(axis=1)
    
    print(f"\n🔄 Pivoted data to wide format. Shape: {wide_df.shape}")
    print(f"   Counties: {len(wide_df.index)}")
    print(f"   Time periods: {len(wide_df.columns)}")
    
    # Show missing data pattern before imputation
    missing_by_county = wide_df.isna().sum(axis=1)
    missing_by_time = wide_df.isna().sum(axis=0)
    
    print(f"\n📊 Missing Data Analysis:")
    print(f"   Counties with missing data: {(missing_by_county > 0).sum()}")
    print(f"   Time periods with missing data: {(missing_by_time > 0).sum()}")
    
    if (missing_by_county > 0).sum() > 0:
        print(f"   Counties with most missing data:")
        for county in missing_by_county.nlargest(5).index:
            print(f"     {county}: {missing_by_county[county]} missing values")

    # --- Smart Imputation Step ---
    print(f"\n🔧 Applying smart imputation...")
    
    # Forward-fill: Fills NaN with the value from the previous time step (column)
    # This handles cases like August_End missing, so it uses August_Mid
    df_imputed = wide_df.fillna(method='ffill', axis=1)
    
    # Backward-fill: Catches any NaNs at the very beginning of a series
    # This handles cases where the first time period is missing
    df_imputed = df_imputed.fillna(method='bfill', axis=1)
    
    # Final check: if there are still NaNs, fill with 0 (last resort)
    remaining_nans = df_imputed.isna().sum().sum()
    if remaining_nans > 0:
        print(f"⚠️  Warning: {remaining_nans} values still missing after imputation. Filling with 0.")
        df_imputed = df_imputed.fillna(0)
    
    print(f"✅ Imputation complete!")
    print(f"   Missing values after imputation: {df_imputed.isna().sum().sum()}")

    # --- Create a more readable column format ---
    # Convert sortable dates back to readable format
    readable_columns = []
    for col in df_imputed.columns:
        year, month_num, period_num = col.split('-')
        month_names = {'04': 'April', '05': 'May', '06': 'June', '07': 'July', 
                      '08': 'August', '09': 'September', '10': 'October'}
        period_names = {'1': 'Start', '2': 'Mid', '3': 'End'}
        
        month_name = month_names.get(month_num, month_num)
        period_name = period_names.get(period_num, period_num)
        readable_col = f"NDWI_{month_name}_{period_name}_{year}"
        readable_columns.append(readable_col)
    
    df_imputed.columns = readable_columns

    # --- Add agricultural district information ---
    # Create county to district mapping
    county_to_district = {}
    for district, counties in district_counties.items():
        for county in counties:
            county_to_district[county] = district
    
    # Add district column
    df_imputed['Ag_District'] = df_imputed.index.map(county_to_district)
    
    # Reorder columns to put Ag_District first
    cols = ['Ag_District'] + [col for col in df_imputed.columns if col != 'Ag_District']
    df_imputed = df_imputed[cols]

    # --- Save the final, clean dataset ---
    df_imputed.to_csv(output_file)
    
    print(f"\n🎉 SUCCESS! Final dataset saved to: '{output_file}'")
    print(f"   Final shape: {df_imputed.shape}")
    print(f"   Counties by district:")
    for district in sorted(df_imputed['Ag_District'].unique()):
        count = (df_imputed['Ag_District'] == district).sum()
        print(f"     {district}: {count} counties")
    
    # Show sample of final data
    print(f"\n📋 Sample of final data:")
    print(df_imputed.head())
    
    print(f"\n✅ Ten-day interval NDWI preprocessing complete!")

else:
    print("❌ No CSV files found to process.")