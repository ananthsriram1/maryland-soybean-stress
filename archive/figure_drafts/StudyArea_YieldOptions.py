#!/usr/bin/env python3
"""
Generate multiple visualization options for district soybean yield by time blocks.
Creates 6 different designs to choose from.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT_DIR = "outputs/YieldAnalysis/StudyArea/Options"
os.makedirs(OUT_DIR, exist_ok=True)

DISTRICT_ORDER = [
    "WESTERN",
    "NORTH CENTRAL",
    "SOUTHERN",
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
]

def load_national_yield():
    df = pd.read_csv("data/NationalAveragesSoybeanAcreageYield.csv")
    df = df[(df["Geo Level"] == "NATIONAL") & (df["Period"] == "YEAR")]
    df = df[df["Data Item"] == "SOYBEANS - YIELD, MEASURED IN BU / ACRE"][["Year", "Value"]].copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["National_Yield"] = pd.to_numeric(df["Value"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    return df[["Year", "National_Yield"]].dropna().sort_values("Year")

def load_district_yield():
    d = pd.read_csv("data/processed_yield/yield_district_averages_by_year.csv")
    d = d.rename(columns={"Yield_mean": "District_Yield"})
    d["Year"] = pd.to_numeric(d["Year"], errors="coerce")
    d["District"] = d["District"].astype(str)
    return d[["District", "Year", "District_Yield"]].dropna().sort_values(["District", "Year"])

def calculate_state_yield_from_districts(district_df):
    state = district_df.groupby("Year", as_index=False)["District_Yield"].mean()
    state = state.rename(columns={"District_Yield": "State_Yield"})
    return state


def prepare_data(time_blocks):
    """
    Prepare data aggregated by time blocks.
    time_blocks: list of tuples [(start1, end1), (start2, end2), ...]
    """
    district = load_district_yield()
    nat = load_national_yield()
    state = calculate_state_yield_from_districts(district)
    
    merged = district.merge(nat, on="Year", how="inner")
    merged = merged.merge(state, on="Year", how="left")
    
    # Assign blocks
    def assign_block(year):
        for i, (start, end) in enumerate(time_blocks):
            if start <= year <= end:
                return i
        return None
    
    merged["block_idx"] = merged["Year"].apply(assign_block)
    merged = merged.dropna(subset=["block_idx"])
    merged["block_idx"] = merged["block_idx"].astype(int)
    merged["block_label"] = merged["block_idx"].apply(lambda i: f"{time_blocks[i][0]}–{time_blocks[i][1]}")
    
    # Calculate statistics
    stats = (
        merged.groupby(["District", "block_idx", "block_label"], as_index=False)
        .agg(
            Yield_mean=("District_Yield", "mean"),
            Yield_sd=("District_Yield", "std"),
            N_years=("Year", "nunique"),
        )
    )
    stats["District"] = pd.Categorical(stats["District"], categories=DISTRICT_ORDER, ordered=True)
    stats = stats.sort_values(["District", "block_idx"])
    
    # Reference stats
    reference_stats = (
        merged.groupby(["block_idx", "block_label"], as_index=False)
        .agg(
            National_Avg=("National_Yield", "mean"),
            State_Avg=("State_Yield", "mean"),
        )
    )
    
    return stats, reference_stats, time_blocks


def option1_three_blocks_clean():
    """Option 1: 3 time blocks (original), cleaner styling"""
    time_blocks = [(1997, 2006), (2007, 2016), (2017, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#e74c3c', '#2ecc71']
    offsets = [-0.25, 0, 0.25]
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + offsets[block_idx], y, yerr=yerr,
            fmt='o', markersize=10, capsize=4, capthick=2,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=2, alpha=0.8, label=block_labels[block_idx]
        )
    
    # Reference lines
    for block_idx in range(len(blocks)):
        nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
        state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
        ax.axhline(nat_val, color='red', linestyle='--', linewidth=2.5, alpha=0.7)
        ax.axhline(state_val, color='navy', linestyle=':', linewidth=2.5, alpha=0.7)
    
    # Labels
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=13, fontweight='bold')
    ax.set_title("District Soybean Yield by Time Period", fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(20, 55)
    
    # Legend
    handles, labels = ax.get_legend_handles_labels()
    handles.extend([
        plt.Line2D([0], [0], color='red', linewidth=2.5, linestyle='--', label='US National'),
        plt.Line2D([0], [0], color='navy', linewidth=2.5, linestyle=':', label='MD State')
    ])
    ax.legend(handles=handles, loc='upper left', fontsize=11, framealpha=0.95)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "Option1_ThreeBlocks_Clean.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Option 1: 3 time blocks (clean design)")


def option2_four_blocks():
    """Option 2: 4 time blocks for more temporal resolution"""
    time_blocks = [(1997, 2006), (2007, 2012), (2013, 2018), (2019, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(15, 7))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#f39c12', '#e74c3c', '#2ecc71']
    width = 0.18
    offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + offsets[block_idx], y, yerr=yerr,
            fmt='o', markersize=9, capsize=4, capthick=1.8,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=1.8, alpha=0.85, label=block_labels[block_idx]
        )
    
    # National reference (single line)
    nat_latest = ref_stats[ref_stats["block_idx"] == len(blocks)-1]["National_Avg"].values[0]
    ax.axhline(nat_latest, color='red', linestyle='--', linewidth=2, alpha=0.6, label='US National (latest)')
    
    state_latest = ref_stats[ref_stats["block_idx"] == len(blocks)-1]["State_Avg"].values[0]
    ax.axhline(state_latest, color='navy', linestyle=':', linewidth=2, alpha=0.6, label='MD State (latest)')
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=13, fontweight='bold')
    ax.set_title("District Soybean Yield: Four Time Periods", fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(20, 55)
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95, ncol=2)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "Option2_FourBlocks.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Option 2: 4 time blocks")


def option3_five_year_blocks():
    """Option 3: 5-year blocks for highest temporal detail"""
    time_blocks = [(1997, 2001), (2002, 2006), (2007, 2011), (2012, 2016), (2017, 2021), (2022, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = plt.cm.viridis(np.linspace(0, 0.9, len(blocks)))
    width = 0.12
    start_offset = -width * (len(blocks) - 1) / 2
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + start_offset + block_idx * width, y, yerr=yerr,
            fmt='o', markersize=7, capsize=3, capthick=1.5,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=1.5, alpha=0.85, label=block_labels[block_idx]
        )
    
    # National and state references (latest only)
    nat_latest = ref_stats[ref_stats["block_idx"] == len(blocks)-1]["National_Avg"].values[0]
    ax.axhline(nat_latest, color='red', linestyle='--', linewidth=2, alpha=0.5, label='US National (2022-25)')
    
    state_latest = ref_stats[ref_stats["block_idx"] == len(blocks)-1]["State_Avg"].values[0]
    ax.axhline(state_latest, color='darkblue', linestyle=':', linewidth=2, alpha=0.5, label='MD State (2022-25)')
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=13, fontweight='bold')
    ax.set_title("District Soybean Yield: Five-Year Blocks", fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(20, 55)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.95, ncol=3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "Option3_FiveYearBlocks.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Option 3: 5-year blocks (high detail)")


def option4_connected_progression():
    """Option 4: Connected line plot showing progression"""
    time_blocks = [(1997, 2006), (2007, 2016), (2017, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    district_colors = {
        "WESTERN": "#e74c3c",
        "NORTH CENTRAL": "#3498db",
        "SOUTHERN": "#2ecc71",
        "UPPER EASTERN SHORE": "#9b59b6",
        "LOWER EASTERN SHORE": "#f39c12",
    }
    
    x = np.arange(len(blocks))
    
    for district in DISTRICT_ORDER:
        sub = stats[stats["District"] == district].sort_values("block_idx")
        if len(sub) == 0:
            continue
        
        # Ensure we have data for all blocks (fill with NaN if missing)
        y = []
        yerr = []
        for block_idx in range(len(blocks)):
            block_data = sub[sub["block_idx"] == block_idx]
            if len(block_data) > 0:
                y.append(block_data["Yield_mean"].iloc[0])
                yerr.append(block_data["Yield_sd"].iloc[0])
            else:
                y.append(np.nan)
                yerr.append(np.nan)
        
        y = np.array(y)
        yerr = np.array(yerr)
        
        ax.plot(x, y, 'o-', color=district_colors[district], linewidth=2.5, 
                markersize=10, label=district.title(), alpha=0.8)
        ax.errorbar(x, y, yerr=yerr, fmt='none', ecolor=district_colors[district], 
                    elinewidth=1.5, capsize=4, alpha=0.6)
    
    # National reference
    nat_vals = ref_stats["National_Avg"].values
    ax.plot(x, nat_vals, 'r--', linewidth=3, label='US National', alpha=0.7)
    
    state_vals = ref_stats["State_Avg"].values
    ax.plot(x, state_vals, 'k:', linewidth=3, label='MD State', alpha=0.7)
    
    ax.set_xlabel("Time Period", fontsize=13, fontweight='bold')
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=13, fontweight='bold')
    ax.set_title("District Yield Progression Over Time", fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{b[0]}–{b[1]}" for b in blocks], fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(25, 55)
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95, ncol=2)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "Option4_ConnectedProgression.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Option 4: Connected progression lines")


def option5_small_multiples():
    """Option 5: Small multiples - one subplot per district"""
    time_blocks = [(1997, 2006), (2007, 2016), (2017, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, axes = plt.subplots(1, 5, figsize=(18, 5), sharey=True)
    
    block_colors = ['#3498db', '#f39c12', '#2ecc71']
    x = np.arange(len(blocks))
    
    for idx, district in enumerate(DISTRICT_ORDER):
        ax = axes[idx]
        sub = stats[stats["District"] == district].sort_values("block_idx")
        
        # Ensure we have data for all blocks
        y = []
        yerr = []
        for block_idx in range(len(blocks)):
            block_data = sub[sub["block_idx"] == block_idx]
            if len(block_data) > 0:
                y.append(block_data["Yield_mean"].iloc[0])
                yerr.append(block_data["Yield_sd"].iloc[0])
            else:
                y.append(0)
                yerr.append(0)
        
        for i, (xi, yi, yerri) in enumerate(zip(x, y, yerr)):
            if yi > 0:  # Only plot if we have data
                ax.bar(xi, yi, color=block_colors[i], alpha=0.85, edgecolor='black', linewidth=1.2)
                if np.isfinite(yerri) and yerri > 0:
                    ax.errorbar(xi, yi, yerr=yerri, fmt='none', ecolor='black', 
                               elinewidth=2, capsize=5, capthick=2)
        
        # National reference
        for i, nat_val in enumerate(ref_stats["National_Avg"].values):
            ax.axhline(nat_val, color='red', linestyle='--', linewidth=1.5, alpha=0.5)
        
        ax.set_title(district.title(), fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f"{b[0]}-{b[1]}" for b in blocks], rotation=45, ha='right', fontsize=9)
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(20, 55)
        
        if idx == 0:
            ax.set_ylabel("Yield (bu/acre)", fontsize=12, fontweight='bold')
    
    fig.suptitle("District Soybean Yield by Time Period (bars) vs US National (dashed lines)", 
                 fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "Option5_SmallMultiples.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Option 5: Small multiples (one panel per district)")


def option6_two_blocks_simple():
    """Option 6: Just 2 blocks - historical vs recent (simplest comparison)"""
    time_blocks = [(1997, 2010), (2011, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#e74c3c']
    width = 0.35
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        offset = -width/2 if block_idx == 0 else width/2
        ax.bar(x + offset, y, width, yerr=yerr, 
               color=block_colors[block_idx], alpha=0.85,
               edgecolor='black', linewidth=1.5, capsize=5,
               error_kw={'elinewidth': 2, 'capthick': 2},
               label=block_labels[block_idx])
    
    # Reference lines
    nat_early = ref_stats[ref_stats["block_idx"] == 0]["National_Avg"].values[0]
    nat_recent = ref_stats[ref_stats["block_idx"] == 1]["National_Avg"].values[0]
    ax.axhline(nat_early, color='darkred', linestyle='--', linewidth=2, alpha=0.6, label='US National (1997-2010)')
    ax.axhline(nat_recent, color='red', linestyle='--', linewidth=2.5, alpha=0.7, label='US National (2011-2025)')
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=14, fontweight='bold')
    ax.set_title("Historical vs Recent District Soybean Yield", fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(20, 55)
    ax.legend(loc='upper left', fontsize=12, framealpha=0.95)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "Option6_TwoBlocks_Simple.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Option 6: 2 blocks (simplest - historical vs recent)")


def main():
    print("\n" + "="*60)
    print("Generating visualization options...")
    print("="*60 + "\n")
    
    option1_three_blocks_clean()
    option2_four_blocks()
    option3_five_year_blocks()
    option4_connected_progression()
    option5_small_multiples()
    option6_two_blocks_simple()
    
    print("\n" + "="*60)
    print(f"✓ All 6 options saved to: {OUT_DIR}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
