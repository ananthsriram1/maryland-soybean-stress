#!/usr/bin/env python3
"""
Create multiple clear variations of the enhanced Option 2 figure.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle

OUT_DIR = "outputs/YieldAnalysis/StudyArea/Options/Variations"
os.makedirs(OUT_DIR, exist_ok=True)

# SI: soybean yield bu/acre → kg/ha (1 bu = 27.2155 kg; 1 ac = 0.404685642 ha)
BUAC_TO_KGHA = 67.251

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
    district = load_district_yield()
    nat = load_national_yield()
    state = calculate_state_yield_from_districts(district)
    
    merged = district.merge(nat, on="Year", how="inner")
    merged = merged.merge(state, on="Year", how="left")
    
    def assign_block(year):
        for i, (start, end) in enumerate(time_blocks):
            if start <= year <= end:
                return i
        return None
    
    merged["block_idx"] = merged["Year"].apply(assign_block)
    merged = merged.dropna(subset=["block_idx"])
    merged["block_idx"] = merged["block_idx"].astype(int)
    merged["block_label"] = merged["block_idx"].apply(lambda i: f"{time_blocks[i][0]}–{time_blocks[i][1]}")
    
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
    
    reference_stats = (
        merged.groupby(["block_idx", "block_label"], as_index=False)
        .agg(
            National_Avg=("National_Yield", "mean"),
            State_Avg=("State_Yield", "mean"),
        )
    )
    
    return stats, reference_stats, time_blocks


def variation1_background_shading():
    """Variation 1: Add background shading for visual grouping"""
    time_blocks = [(1997, 2006), (2007, 2012), (2013, 2018), (2019, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(18, 9))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#f39c12', '#e74c3c', '#2ecc71']
    width = 0.18
    offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    # Add background shading between national and state lines for each period
    for block_idx in range(len(blocks)):
        nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
        state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
        ax.axhspan(state_val, nat_val, alpha=0.08, color=block_colors[block_idx], zorder=0)
    
    # Plot district data points with larger markers
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + offsets[block_idx], y, yerr=yerr,
            fmt='o', markersize=12, capsize=5, capthick=2.5,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=2.5, alpha=0.9, label=block_labels[block_idx], zorder=5
        )
    
    # Plot reference lines with thicker lines
    x_min, x_max = x.min() - 0.5, x.max() + 0.5
    
    for block_idx in range(len(blocks)):
        nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
        state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
        
        # National line (thicker)
        ax.plot([x_min, x_max], [nat_val, nat_val], 
               color=block_colors[block_idx], linestyle='--', 
               linewidth=3.5, alpha=0.8, zorder=2)
        
        # Label at right
        ax.text(x_max + 0.2, nat_val, f"US\n{blocks[block_idx][0]}-{blocks[block_idx][1]}", 
               va='center', ha='left', fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                        edgecolor=block_colors[block_idx], alpha=0.95, linewidth=2.5))
        
        # State line (thicker)
        ax.plot([x_min, x_max], [state_val, state_val],
               color=block_colors[block_idx], linestyle=':', 
               linewidth=3.5, alpha=0.8, zorder=2)
        
        # Label at left
        ax.text(x_min - 0.2, state_val, f"MD\n{blocks[block_idx][0]}-{blocks[block_idx][1]}", 
               va='center', ha='right', fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                        edgecolor=block_colors[block_idx], alpha=0.95, linewidth=2.5))
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=16, fontweight='bold')
    ax.set_title("District Soybean Yield Across Four Time Periods", 
                fontsize=18, fontweight='bold', pad=25)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.5)
    ax.set_ylim(20, 55)
    ax.set_xlim(x_min - 1.0, x_max + 1.8)
    
    legend_handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=block_colors[i], 
                  markeredgecolor='black', markersize=11, linewidth=2,
                  label=f"{block_labels[i]}")
        for i in range(len(blocks))
    ]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=12, framealpha=0.97, 
             ncol=2, title="Time Periods", title_fontsize=13)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "V1_BackgroundShading.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Variation 1: Background shading")


def variation2_larger_bolder():
    """Variation 2: Larger, bolder everything - maximum clarity"""
    time_blocks = [(1997, 2006), (2007, 2012), (2013, 2018), (2019, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(20, 10))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#f39c12', '#e74c3c', '#2ecc71']
    width = 0.18
    offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    # Plot district data with extra large markers
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + offsets[block_idx], y, yerr=yerr,
            fmt='o', markersize=16, capsize=6, capthick=3,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=3, alpha=0.9, label=block_labels[block_idx], zorder=5
        )
    
    x_min, x_max = x.min() - 0.5, x.max() + 0.5
    
    for block_idx in range(len(blocks)):
        nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
        state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
        
        # Extra thick lines
        ax.plot([x_min, x_max], [nat_val, nat_val], 
               color=block_colors[block_idx], linestyle='--', 
               linewidth=4.5, alpha=0.85, zorder=2)
        
        ax.text(x_max + 0.25, nat_val, f"US\n{blocks[block_idx][0]}-\n{blocks[block_idx][1]}", 
               va='center', ha='left', fontsize=13, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor=block_colors[block_idx], 
                        edgecolor='black', alpha=0.85, linewidth=3))
        
        ax.plot([x_min, x_max], [state_val, state_val],
               color=block_colors[block_idx], linestyle=':', 
               linewidth=4.5, alpha=0.85, zorder=2)
        
        ax.text(x_min - 0.25, state_val, f"MD\n{blocks[block_idx][0]}-\n{blocks[block_idx][1]}", 
               va='center', ha='right', fontsize=13, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor=block_colors[block_idx], 
                        edgecolor='black', alpha=0.85, linewidth=3))
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=20, fontweight='bold')
    ax.set_title("District Soybean Yield Across Four Time Periods", 
                fontsize=22, fontweight='bold', pad=30)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=15, fontweight='bold')
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=2)
    ax.set_ylim(20, 55)
    ax.set_xlim(x_min - 1.2, x_max + 2.0)
    
    legend_handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=block_colors[i], 
                  markeredgecolor='black', markersize=13, linewidth=2.5,
                  label=f"{block_labels[i]}")
        for i in range(len(blocks))
    ]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=14, framealpha=0.97, 
             ncol=2, title="Time Periods", title_fontsize=16, edgecolor='black', fancybox=True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "V2_LargerBolder.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Variation 2: Larger and bolder")


def variation3_separated_panels():
    """Variation 3: Separate each district into its own mini-panel"""
    time_blocks = [(1997, 2006), (2007, 2012), (2013, 2018), (2019, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    # Convert to SI (kg/ha)
    stats = stats.copy()
    ref_stats = ref_stats.copy()
    stats["Yield_mean"] *= BUAC_TO_KGHA
    stats["Yield_sd"] *= BUAC_TO_KGHA
    ref_stats["National_Avg"] *= BUAC_TO_KGHA
    ref_stats["State_Avg"] *= BUAC_TO_KGHA

    fig, axes = plt.subplots(1, 5, figsize=(20, 6), sharey=True)
    
    block_colors = ['#3498db', '#f39c12', '#e74c3c', '#2ecc71']
    x = np.arange(len(blocks))
    
    for idx, district in enumerate(DISTRICT_ORDER):
        ax = axes[idx]
        sub = stats[stats["District"] == district].sort_values("block_idx")
        
        # Get data for all blocks
        y = []
        yerr = []
        for block_idx in range(len(blocks)):
            block_data = sub[sub["block_idx"] == block_idx]
            if len(block_data) > 0:
                y.append(block_data["Yield_mean"].iloc[0])
                yerr.append(block_data["Yield_sd"].iloc[0])
            else:
                y.append(np.nan)
                yerr.append(0)
        
        # Plot district points
        for i in range(len(blocks)):
            if not np.isnan(y[i]):
                ax.errorbar(i, y[i], yerr=yerr[i], fmt='o', markersize=14, 
                           capsize=5, capthick=2.5, color=block_colors[i],
                           ecolor=block_colors[i], elinewidth=2.5, alpha=0.9)
        
        # Add reference lines for each period
        for block_idx in range(len(blocks)):
            nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
            state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
            
            # Show reference line only in relevant x-position
            ax.plot([block_idx - 0.4, block_idx + 0.4], [nat_val, nat_val],
                   color='red', linestyle='--', linewidth=3, alpha=0.7)
            ax.plot([block_idx - 0.4, block_idx + 0.4], [state_val, state_val],
                   color='navy', linestyle=':', linewidth=3, alpha=0.7)
        
        ax.set_title(district.title(), fontsize=13, fontweight='bold', pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{b[0]}-\n{b[1]}" for b in blocks], fontsize=9, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linewidth=1.2)
        ax.set_ylim(20 * BUAC_TO_KGHA, 55 * BUAC_TO_KGHA)
        
        if idx == 0:
            ax.set_ylabel("Yield (kg/ha)", fontsize=14, fontweight='bold')
    
    # Add legend to first panel
    legend_handles = [
        plt.Line2D([0], [0], color='red', linewidth=3, linestyle='--', label='US National'),
        plt.Line2D([0], [0], color='navy', linewidth=3, linestyle=':', label='MD State')
    ]
    axes[0].legend(handles=legend_handles, loc='upper left', fontsize=10, framealpha=0.95)
    
    fig.suptitle("District Soybean Yield by Time Period\n(Red dashed = US National, Navy dotted = MD State)", 
                 fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "V3_SeparatedPanels.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Variation 3: Separated panels")


def variation4_color_coded_boxes():
    """Variation 4: Color-coded boxes around reference labels matching line colors"""
    time_blocks = [(1997, 2006), (2007, 2012), (2013, 2018), (2019, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(18, 9))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#f39c12', '#e74c3c', '#2ecc71']
    width = 0.18
    offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    # Plot district data
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + offsets[block_idx], y, yerr=yerr,
            fmt='o', markersize=13, capsize=5, capthick=2.5,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=2.5, alpha=0.9, label=block_labels[block_idx], zorder=5
        )
    
    x_min, x_max = x.min() - 0.5, x.max() + 0.5
    
    # Reference lines with matching colored boxes
    for block_idx in range(len(blocks)):
        nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
        state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
        
        # National line
        ax.plot([x_min, x_max], [nat_val, nat_val], 
               color=block_colors[block_idx], linestyle='--', 
               linewidth=3.5, alpha=0.85, zorder=2)
        
        # Box with matching color fill
        ax.text(x_max + 0.22, nat_val, f"US {blocks[block_idx][0]}-{blocks[block_idx][1]}", 
               va='center', ha='left', fontsize=11, fontweight='bold', color='white',
               bbox=dict(boxstyle='round,pad=0.5', facecolor=block_colors[block_idx], 
                        edgecolor='black', alpha=0.95, linewidth=2.5))
        
        # State line
        ax.plot([x_min, x_max], [state_val, state_val],
               color=block_colors[block_idx], linestyle=':', 
               linewidth=3.5, alpha=0.85, zorder=2)
        
        # Darker shade for state boxes
        import matplotlib.colors as mcolors
        darker_color = mcolors.to_rgb(block_colors[block_idx])
        darker_color = tuple(c * 0.7 for c in darker_color)
        
        ax.text(x_min - 0.22, state_val, f"MD {blocks[block_idx][0]}-{blocks[block_idx][1]}", 
               va='center', ha='right', fontsize=11, fontweight='bold', color='white',
               bbox=dict(boxstyle='round,pad=0.5', facecolor=darker_color, 
                        edgecolor='black', alpha=0.95, linewidth=2.5))
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=16, fontweight='bold')
    ax.set_title("District Soybean Yield Across Four Time Periods\n(Dashed = US National, Dotted = MD State)", 
                fontsize=18, fontweight='bold', pad=25)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.5)
    ax.set_ylim(20, 55)
    ax.set_xlim(x_min - 1.1, x_max + 1.9)
    
    legend_handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=block_colors[i], 
                  markeredgecolor='black', markersize=12, linewidth=2,
                  label=f"{block_labels[i]}")
        for i in range(len(blocks))
    ]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=13, framealpha=0.97, 
             ncol=2, title="Time Periods", title_fontsize=14, edgecolor='black', fancybox=True)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "V4_ColorCodedBoxes.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Variation 4: Color-coded boxes")


def variation5_simplified_minimal():
    """Variation 5: Simplified - show only most recent period's reference lines prominently"""
    time_blocks = [(1997, 2006), (2007, 2012), (2013, 2018), (2019, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(18, 9))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#f39c12', '#e74c3c', '#2ecc71']
    width = 0.18
    offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    # Plot district data
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + offsets[block_idx], y, yerr=yerr,
            fmt='o', markersize=13, capsize=5, capthick=2.5,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=2.5, alpha=0.9, label=block_labels[block_idx], zorder=5
        )
    
    x_min, x_max = x.min() - 0.5, x.max() + 0.5
    
    # Show all reference lines but make older ones lighter
    for block_idx in range(len(blocks)):
        nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
        state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
        
        # Fade older periods
        alpha_val = 0.3 if block_idx < 3 else 0.9
        linewidth_val = 2 if block_idx < 3 else 4
        
        ax.plot([x_min, x_max], [nat_val, nat_val], 
               color=block_colors[block_idx], linestyle='--', 
               linewidth=linewidth_val, alpha=alpha_val, zorder=2)
        
        ax.plot([x_min, x_max], [state_val, state_val],
               color=block_colors[block_idx], linestyle=':', 
               linewidth=linewidth_val, alpha=alpha_val, zorder=2)
        
        # Only label the most recent period prominently
        if block_idx == 3:
            ax.text(x_max + 0.25, nat_val, f"US National\n{blocks[block_idx][0]}-{blocks[block_idx][1]}", 
                   va='center', ha='left', fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='red', 
                            edgecolor='black', alpha=0.9, linewidth=2.5))
            
            ax.text(x_min - 0.25, state_val, f"MD State\n{blocks[block_idx][0]}-{blocks[block_idx][1]}", 
                   va='center', ha='right', fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='navy', 
                            edgecolor='black', alpha=0.9, linewidth=2.5))
        else:
            # Small labels for older periods
            ax.text(x_max + 0.08, nat_val, f"{blocks[block_idx][0]}-{blocks[block_idx][1]}", 
                   va='center', ha='left', fontsize=8, alpha=0.6)
            ax.text(x_min - 0.08, state_val, f"{blocks[block_idx][0]}-{blocks[block_idx][1]}", 
                   va='center', ha='right', fontsize=8, alpha=0.6)
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=16, fontweight='bold')
    ax.set_title("District Soybean Yield Across Four Time Periods\n(Most recent period 2019-2025 highlighted)", 
                fontsize=18, fontweight='bold', pad=25)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.5)
    ax.set_ylim(20, 55)
    ax.set_xlim(x_min - 1.2, x_max + 2.0)
    
    legend_handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=block_colors[i], 
                  markeredgecolor='black', markersize=12, linewidth=2,
                  label=f"{block_labels[i]}")
        for i in range(len(blocks))
    ]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=13, framealpha=0.97, 
             ncol=2, title="Time Periods", title_fontsize=14)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "V5_SimplifiedMinimal.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Variation 5: Simplified minimal")


def variation6_annotated_values():
    """Variation 6: Add text annotations showing actual yield values"""
    time_blocks = [(1997, 2006), (2007, 2012), (2013, 2018), (2019, 2025)]
    stats, ref_stats, blocks = prepare_data(time_blocks)
    
    fig, ax = plt.subplots(figsize=(20, 10))
    
    x = np.arange(len(DISTRICT_ORDER))
    block_colors = ['#3498db', '#f39c12', '#e74c3c', '#2ecc71']
    width = 0.18
    offsets = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    block_labels = [f"{b[0]}–{b[1]}" for b in blocks]
    
    # Plot district data with value annotations
    for block_idx in range(len(blocks)):
        sub = stats[stats["block_idx"] == block_idx].set_index("District").reindex(DISTRICT_ORDER)
        y = sub["Yield_mean"].to_numpy(dtype=float)
        yerr = sub["Yield_sd"].to_numpy(dtype=float)
        yerr = np.where(np.isfinite(yerr), yerr, 0.0)
        
        ax.errorbar(
            x + offsets[block_idx], y, yerr=yerr,
            fmt='o', markersize=14, capsize=5, capthick=2.5,
            color=block_colors[block_idx], ecolor=block_colors[block_idx],
            elinewidth=2.5, alpha=0.9, label=block_labels[block_idx], zorder=5
        )
        
        # Add value labels above error bars for most recent period
        if block_idx == 3:  # Latest period
            for xi, yi in zip(x + offsets[block_idx], y):
                if np.isfinite(yi):
                    ax.text(xi, yi + 3, f"{yi:.1f}", ha='center', va='bottom',
                           fontsize=10, fontweight='bold', 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                                   edgecolor=block_colors[block_idx], alpha=0.9))
    
    x_min, x_max = x.min() - 0.5, x.max() + 0.5
    
    for block_idx in range(len(blocks)):
        nat_val = ref_stats[ref_stats["block_idx"] == block_idx]["National_Avg"].values[0]
        state_val = ref_stats[ref_stats["block_idx"] == block_idx]["State_Avg"].values[0]
        
        ax.plot([x_min, x_max], [nat_val, nat_val], 
               color=block_colors[block_idx], linestyle='--', 
               linewidth=3.5, alpha=0.85, zorder=2)
        
        ax.text(x_max + 0.25, nat_val, f"US {blocks[block_idx][0]}-{blocks[block_idx][1]}\n{nat_val:.1f} bu/ac", 
               va='center', ha='left', fontsize=11, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                        edgecolor=block_colors[block_idx], alpha=0.95, linewidth=2.5))
        
        ax.plot([x_min, x_max], [state_val, state_val],
               color=block_colors[block_idx], linestyle=':', 
               linewidth=3.5, alpha=0.85, zorder=2)
        
        ax.text(x_min - 0.25, state_val, f"MD {blocks[block_idx][0]}-{blocks[block_idx][1]}\n{state_val:.1f} bu/ac", 
               va='center', ha='right', fontsize=11, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                        edgecolor=block_colors[block_idx], alpha=0.95, linewidth=2.5))
    
    ax.set_ylabel("Soybean Yield (bu/acre)", fontsize=18, fontweight='bold')
    ax.set_title("District Soybean Yield Across Four Time Periods\n(with actual yield values)", 
                fontsize=20, fontweight='bold', pad=30)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(" ", "\n") for d in DISTRICT_ORDER], fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.5)
    ax.set_ylim(20, 58)
    ax.set_xlim(x_min - 1.3, x_max + 2.2)
    
    legend_handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=block_colors[i], 
                  markeredgecolor='black', markersize=13, linewidth=2,
                  label=f"{block_labels[i]}")
        for i in range(len(blocks))
    ]
    ax.legend(handles=legend_handles, loc='upper left', fontsize=13, framealpha=0.97, 
             ncol=2, title="Time Periods", title_fontsize=15)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "V6_AnnotatedValues.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Variation 6: Annotated values")


def main():
    print("\n" + "="*60)
    print("Generating clarity-enhanced variations...")
    print("="*60 + "\n")
    
    variation1_background_shading()
    variation2_larger_bolder()
    variation3_separated_panels()
    variation4_color_coded_boxes()
    variation5_simplified_minimal()
    variation6_annotated_values()
    
    print("\n" + "="*60)
    print(f"✓ All 6 variations saved to: {OUT_DIR}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
