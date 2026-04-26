"""Combine NCEI county-level Palmer drought index CSVs into a wide pivot.

Consolidated replacement for the three legacy scripts:
  archive/combine_drought_legacy/CombinePDSIData.py
  archive/combine_drought_legacy/CombinePHDIData.py
  archive/combine_drought_legacy/CombinePMDIData.py
which were byte-identical except for the input folder, output filename, and
column prefix. Behavior is otherwise unchanged: same skiprows, same Date
parsing, same pivot_table aggregation (mean), same column renaming.

Usage
-----
  python -m analysis.preprocessing.combine_palmer_index --index PDSI
  python -m analysis.preprocessing.combine_palmer_index --index PHDI
  python -m analysis.preprocessing.combine_palmer_index --index PMDI

Inputs
------
  data/{pdsi|phdi|pmdi}/<County>.csv
      One CSV per Maryland county exported from the NOAA NCEI "Climate at a
      Glance / County / Time Series" interface. The first row is a header
      banner that is skipped (skiprows=1). The county name is taken from the
      filename stem.

Outputs
-------
  data/maryland_{pdsi|phdi|pmdi}_combined_wide.csv
      Wide-format CSV with index='County' and columns named
      '{INDEX}_YYYY-MM' (e.g. 'PDSI_2012-07').

Provenance
----------
  This script was introduced during the JAG manuscript code-release reorg
  (Phase 3). Output is byte-identical to the three legacy scripts; this is
  enforced by an SHA256 byte-match check immediately after consolidation.
"""

import argparse
import os
import pandas as pd

INDEX_CONFIG = {
    "PDSI": {
        "data_folder": "data/pdsi",
        "output_file": "data/maryland_pdsi_combined_wide.csv",
        "column_prefix": "PDSI_",
    },
    "PHDI": {
        "data_folder": "data/phdi",
        "output_file": "data/maryland_phdi_combined_wide.csv",
        "column_prefix": "PHDI_",
    },
    "PMDI": {
        "data_folder": "data/pmdi",
        "output_file": "data/maryland_pmdi_combined_wide.csv",
        "column_prefix": "PMDI_",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--index",
        required=True,
        choices=sorted(INDEX_CONFIG),
        help="Which Palmer drought index to combine (PDSI, PHDI, or PMDI).",
    )
    args = parser.parse_args()
    cfg = INDEX_CONFIG[args.index]

    data_folder = cfg["data_folder"]
    output_file = cfg["output_file"]
    column_prefix = cfg["column_prefix"]

    try:
        all_files = os.listdir(data_folder)
        csv_files = [f for f in all_files if f.endswith('.csv')]
        print(f"Found {len(csv_files)} files in '{data_folder}' to process.")
    except FileNotFoundError:
        print(f"Error: The folder '{data_folder}' was not found.")
        csv_files = []

    if csv_files:
        all_data_list = []

        for filename in csv_files:
            file_path = os.path.join(data_folder, filename)

            df = pd.read_csv(file_path, skiprows=1)

            county_name = filename.replace('.csv', '')
            df['County'] = county_name
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m').dt.strftime('%Y-%m')

            all_data_list.append(df)

        long_df = pd.concat(all_data_list, ignore_index=True)
        print("\nSuccessfully combined all files into a single long-format table.")

        print(f"Pivoting the {column_prefix.strip('_')} table to a wide format...")
        wide_df = long_df.pivot_table(index='County', columns='Date', values='Value', aggfunc='mean')

        wide_df.columns = [column_prefix + str(col) for col in wide_df.columns]

        print("Pivoting complete.")

        wide_df.to_csv(output_file)
        print(f"\n✅ Success! The combined data has been saved to: '{output_file}'")


if __name__ == "__main__":
    main()
