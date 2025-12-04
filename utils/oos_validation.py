import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from glob import glob
from typing import Dict, List
import seaborn as sns
from matplotlib.gridspec import GridSpec

def read_and_concatenate_parquet(folder_path):
    """
    Read all parquet files in a folder and concatenate them into a single DataFrame.
    """
    # Get all parquet files in the folder
    parquet_files = glob(os.path.join(folder_path, "*.parquet"))

    if not parquet_files:
        print(f"No parquet files found in {folder_path}")
        return None

    # print(f"Found {len(parquet_files)} parquet files")

    # Read and concatenate all files
    dfs = []
    for file in parquet_files:
        df = pd.read_parquet(file)
        dfs.append(df)

    # Concatenate all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)

    # print(f"Combined DataFrame shape: {combined_df.shape}")

    return combined_df


def calculate_BIC_full(group: pd.DataFrame) -> pd.Series:
    """Calculate BIC and all components for one group"""
    group = group.sort_values('month_day')

    percentages = group['context_zero_pct'].values
    binary = group['is_out_of_season'].astype(int).values

    # Identify runs
    runs = []
    current_run = []
    for i, val in enumerate(binary):
        if val == 1:
            current_run.append(i)
        elif current_run:
            runs.append(current_run)
            current_run = []
    if current_run:
        runs.append(current_run)

    min_len = group['min_oos_run_length'].iloc[0]
    valid_runs = [r for r in runs if len(r) >= min_len]

    k = len(valid_runs)

    result = {
        'iso3': group['iso3'].iloc[0],
        'adm_level': group['adm_level'].iloc[0],
        'rolling_sum_days': group['rolling_sum_days'].iloc[0],
        'min_oos_run_length': group['min_oos_run_length'].iloc[0],
        'data': group['data'].iloc[0],
        'k': k,
        'n': 0,
        'SS_W': np.nan,
        'BIC': np.inf
    }

    if k == 0:
        return pd.Series(result)

    n = sum(len(r) for r in valid_runs)

    # Calculate SS_W
    SS_W = 0.0
    for run in valid_runs:
        run_vals = percentages[run]
        run_mean = run_vals.mean()
        SS_W += ((run_vals - run_mean) ** 2).sum()

    # BIC with special handling for perfect fit
    if n > k:
        if SS_W < 1e-10:  # Perfect fit
            # Use minimal variance as floor
            BIC = k * np.log(n) + n * np.log(1e-10)
        else:
            BIC = k * np.log(n) + n * np.log(SS_W / n)
    else:
        BIC = np.inf

    result.update({
        'n': n,
        'SS_W': SS_W,  # Keep original (can be 0)
        'BIC': BIC
    })

    return pd.Series(result)

def plot_bic_components(results, length, admin_level, save_plot=True):
    """
    Plot BIC components vs parameters.

    Parameters:
    -----------
    results : pd.DataFrame
        DataFrame containing results with columns: k, n, SS_W, BIC,
        percentage_threshold, context_window_days
    length : int or str
        Length parameter for filename
    admin_level : int or str
        Administrative level for filename
    save_plot : bool, optional
        If True, save the plot to PNG (default: True)

    Returns:
    --------
    None
        The plot is displayed automatically in interactive mode (e.g., Jupyter notebooks)
    """
    results_valid = results[results['k'] > 0].copy()

    # Create figure with 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(8, 6), dpi=150)
    fig.suptitle('BIC Components vs Parameters', fontsize=16, fontweight='bold')

    # Prepare data for heatmaps
    metrics = ['k', 'n', 'SS_W', 'BIC']
    titles = [
        'Number of Runs (k)',
        'Total Days in Runs (n)',
        'Within-Run Sum of Squares (SS_W)',
        'BIC Score (lower is better)'
    ]

    for idx, (metric, title) in enumerate(zip(metrics, titles)):
        ax = axes[idx // 2, idx % 2]

        # Pivot table: rows=threshold, cols=window
        pivot = results_valid.pivot_table(
            values=metric,
            index='percentage_threshold',
            columns='context_window_days',
            aggfunc='mean'  # Average across pcodes
        )

        # Create heatmap
        sns.heatmap(
            pivot,
            annot=True,
            fmt='.2f' if metric in ['SS_W', 'BIC'] else '.1f',
            cmap='RdYlGn_r' if metric in ['SS_W', 'BIC', 'k'] else 'RdYlGn',
            ax=ax,
            cbar_kws={'label': metric}
        )

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Context Window (days)', fontsize=10)
        ax.set_ylabel('Percentage Threshold (%)', fontsize=10)

    plt.tight_layout()

    # Save if requested
    if save_plot:
        filename = f'bic_components_length_{length}_admin_{admin_level}.png'
        fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Plot saved as: {filename}")

def analyze_bic_grid_search(
    length: int,
    adm_level: int,
    base_folder: str = "grid_search_results"
) -> pd.DataFrame:
    """
    Analyze BIC grid search results for given parameters.
    
    Parameters:
    -----------
    length : int
        Rolling sum days length
    adm_level : int
        Administrative level to analyze
    base_folder : str, optional
        Base folder containing grid search results (default: "grid_search_results")
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with BIC analysis results, columns:
        ['iso3', 'pcode', 'adm_level', 'rolling_sum_days',
         'context_window_days', 'percentage_threshold', 'min_oos_run_length',
         'data', 'k', 'n', 'SS_W', 'BIC']
    """
    # Build folder path
    folder_path = Path(base_folder) / f"adm{adm_level}" / f"length{length}"
    
    # Read data
    df = read_and_concatenate_parquet(str(folder_path))

    if df is None:
        raise FileNotFoundError(
            f"No data found in {folder_path}"
        )
    
    # Filter by admin level
    df_filtered = df.loc[df['adm_level'] == adm_level].copy()  # type: ignore
    
    # Group by relevant columns
    grouped = df_filtered.groupby([
        'pcode', 
        'context_window_days', 
        'percentage_threshold'
    ])
    
    # Calculate BIC for each group
    results = grouped.apply(
        calculate_BIC_full
    ).reset_index()
    
    # Reorder columns for better readability
    column_order = [
        'iso3', 'pcode', 'adm_level', 'rolling_sum_days',
        'context_window_days', 'percentage_threshold', 'min_oos_run_length',
        'data', 'k', 'n', 'SS_W', 'BIC'
    ]
    results = results[column_order]
    
    return results

def get_bic_summary_stats(results: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate summary statistics by parameter combination.
    """
    results = results[results['k'] > 0].copy()

    summary = results.groupby(['percentage_threshold', 'context_window_days']).agg({
        'k': ['mean', 'std'],
        'n': ['mean', 'std'],
        'SS_W': ['mean', 'std'],
        'BIC': ['mean', 'median', 'std']  # Added median
    }).round(2)
    
    return summary

def get_best_config_per_pcode(results: pd.DataFrame) -> pd.DataFrame:
    """
    Get best configuration (minimum BIC) for each pcode.
    
    Parameters:
    -----------
    results : pd.DataFrame
        BIC analysis results
        
    Returns:
    --------
    pd.DataFrame
        Best configuration per pcode with columns:
        ['pcode', 'percentage_threshold', 'context_window_days', 'k', 'n', 'BIC', ...]
    """
    results = results[results['k'] > 0].copy()

    best_per_pcode = results.sort_values('BIC').groupby('pcode').first().reset_index()
    return best_per_pcode


def get_most_common_combinations(results: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Find most common best parameter combinations across pcodes.
    
    Parameters:
    -----------
    results : pd.DataFrame
        BIC analysis results
        
    Returns:
    --------
    dict
        Dictionary containing:
        - 'threshold': Series with threshold frequencies
        - 'window': Series with window frequencies
        - 'combination': Series with (threshold, window) combination frequencies
    """
    results = results[results['k'] > 0].copy()

    best_per_pcode = get_best_config_per_pcode(results)
    
    return {
        'threshold': best_per_pcode['percentage_threshold'].value_counts(),
        'window': best_per_pcode['context_window_days'].value_counts(),
        'combination': best_per_pcode.groupby(
            ['percentage_threshold', 'context_window_days']
        ).size().sort_values(ascending=False)
    }


def get_average_bic_by_params(results: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average BIC for each parameter combination.
    
    Parameters:
    -----------
    results : pd.DataFrame
        BIC analysis results
        
    Returns:
    --------
    pd.DataFrame
        Average BIC grouped by threshold and window, sorted ascending
    """
    results = results[results['k'] > 0].copy()

    avg_bic = results.groupby(
        ['percentage_threshold', 'context_window_days']
    )['BIC'].mean().sort_values().to_frame('avg_BIC')
    
    return avg_bic


def find_best_average_config(
    results: pd.DataFrame,
    adm_level: int,
    length: int
):
    """
    Find the best configuration based on median BIC across all pcodes.
    
    Parameters:
    -----------
    results : pd.DataFrame
        BIC analysis results
    adm_level : int
        Administrative level
    length : int
        Rolling sum days length
        
    Returns:
    --------
    dict
        Best configuration with keys:
        - 'adm_level': int
        - 'length': int
        - 'percentage_threshold': float
        - 'context_window_days': int
        - 'median_BIC': float
        - 'avg_BIC': float
    """
    results = results[results['k'] > 0].copy()

    # Group by parameter configuration
    grouped = results.groupby(['percentage_threshold', 'context_window_days'])['BIC']
    
    # Calculate both median and mean
    median_bic = grouped.median()
    avg_bic = grouped.mean()

    if len(median_bic) == 0:
        raise ValueError(
            f"No parameter combinations with valid BIC for adm_level={adm_level}, length={length}"
        )
    
    # Select best config based on median BIC (more robust)
    best_idx = median_bic.idxmin()
    best_threshold, best_window = best_idx # type: ignore
    
    return {
        'adm_level': adm_level,
        'length': length,
        'percentage_threshold': best_threshold,
        'context_window_days': best_window,
        'median_BIC': median_bic.min(),
        'avg_BIC': avg_bic[best_idx]
    }


def print_bic_analysis_report(
    results: pd.DataFrame,
    adm_level: int,
    length: int
) -> None:
    """
    Print comprehensive BIC analysis report.
    
    Parameters:
    -----------
    results : pd.DataFrame
        BIC analysis results
    adm_level : int
        Administrative level
    length : int
        Rolling sum days length
    """

    results = results[results['k'] > 0].copy()

    # Best overall
    best_overall = results.loc[results['BIC'].idxmin()]
    
    print("=" * 70)
    print("BEST CONFIGURATION (Minimum BIC across all pcodes)")
    print("=" * 70)
    print(f"Pcode: {best_overall['pcode']}")
    print(f"Percentage Threshold: {best_overall['percentage_threshold']}%")
    print(f"Context Window: {best_overall['context_window_days']} days")
    print(f"Number of runs (k): {best_overall['k']}")
    print(f"Total OOS days (n): {best_overall['n']}")
    print(f"Within-run variance (SS_W): {best_overall['SS_W']:.4f}")
    print(f"BIC: {best_overall['BIC']:.2f}")
    
    # Best per pcode
    print("\n" + "=" * 70)
    print("BEST CONFIGURATION PER PCODE (Top 10)")
    print("=" * 70)
    best_per_pcode = get_best_config_per_pcode(results)
    print(best_per_pcode[[
        'pcode', 'percentage_threshold', 'context_window_days', 'k', 'n', 'BIC'
    ]].head(10))
    
    # Most common
    print("\n" + "=" * 70)
    print("MOST COMMON BEST PARAMETERS")
    print("=" * 70)
    common = get_most_common_combinations(results)
    print("\nMost common threshold:")
    print(common['threshold'])
    print("\nMost common window:")
    print(common['window'])
    print("\nMost common combination:")
    print(common['combination'].head())
    
    # Average and Median BIC
    print("\n" + "=" * 70)
    print("AVERAGE & MEDIAN BIC BY PARAMETER COMBINATION")
    print("=" * 70)
    grouped = results.groupby(['percentage_threshold', 'context_window_days'])['BIC']
    bic_stats = pd.DataFrame({
        'median_BIC': grouped.median(),
        'avg_BIC': grouped.mean()
    }).sort_values('median_BIC')
    print(bic_stats)
    
    # Best average (now based on median)
    best_avg = find_best_average_config(results, adm_level, length)
    print(f"\nBest configuration (by median BIC):")
    print(f"  Admin Level: {best_avg['adm_level']}")
    print(f"  Length: {best_avg['length']}")
    print(f"  Threshold: {best_avg['percentage_threshold']}%")
    print(f"  Window: {best_avg['context_window_days']} days")
    print(f"  Median BIC: {best_avg['median_BIC']:.2f}")
    print(f"  Avg BIC: {best_avg['avg_BIC']:.2f}")
    
    # Summary stats
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS BY PARAMETER COMBINATION")
    print("=" * 70)
    summary = get_bic_summary_stats(results)
    print(summary)

def run_comprehensive_bic_analysis(
    adm_levels: List[int] = [0, 1, 2],
    lengths: List[int] = [15, 30],
    base_folder: str = "grid_search_results",
    verbose = True
) -> pd.DataFrame:
    """
    Run BIC analysis for multiple admin levels and lengths, returning best configs.
    
    Parameters:
    -----------
    adm_levels : List[int], optional
        List of administrative levels to analyze (default: [0, 1, 2])
    lengths : List[int], optional
        List of rolling sum lengths to analyze (default: [15, 30])
    base_folder : str, optional
        Base folder containing grid search results (default: "grid_search_results")
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with best configuration (by median BIC) for each combination:
        ['adm_level', 'length', 'percentage_threshold', 'context_window_days', 
         'avg_BIC', 'median_BIC']
    """
    best_configs = []
    
    for adm_level in adm_levels:
        for length in lengths:
            try:
                print(f"Processing adm_level={adm_level}, length={length}...")
                
                # Run analysis
                results = analyze_bic_grid_search(
                    length=length,
                    adm_level=adm_level,
                    base_folder=base_folder
                )

                results_valid = results[results['k'] > 0].copy()
                
                # Get best config (by median BIC)
                best_config = find_best_average_config(results_valid, adm_level, length)
                best_configs.append(best_config)
            
                if verbose:
                    print(f"  ✓ Best config: threshold={best_config['percentage_threshold']}%, "
                        f"window={best_config['context_window_days']} days, "
                        f"median BIC={best_config['median_BIC']:.2f}, "
                        f"avg BIC={best_config['avg_BIC']:.2f}\n")
                    
            except (ValueError, FileNotFoundError) as e:
                print(f"  ✗ Skipped: {e}\n")
                continue
            except Exception as e:
                print(f"  ✗ Error: {type(e).__name__}: {e}\n")
                continue
    
    # Convert to DataFrame
    df_best_configs = pd.DataFrame(best_configs)
    
    # Sort by median_BIC (primary criterion) to see best overall
    df_best_configs = df_best_configs.sort_values('median_BIC').reset_index(drop=True)
    
    return df_best_configs

def create_compact_bic_figure(
    results_dict: dict,
    save_plot: bool = True,
    dpi: int = 300
):
    """
    Create compact 1x3 figure showing key BIC model selection insights.
    
    Parameters:
    -----------
    results_dict : dict
        Dictionary with keys (adm_level, length) and DataFrames from analyze_bic_grid_search()
        Must include all combinations: (1,15), (1,30), (2,15), (2,30)
    save_plot : bool, optional
        If True, save the plot (default: True)
    dpi : int, optional
        Resolution for saved figure (default: 300)
    """
    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Define colors
    colors = {
        'admin1': '#2E86AB',
        'admin2': '#A23B72',
        'median': '#2A9D8F',
        'mean': '#E63946'
    }
    
    # ========================================================================
    # PANEL C: SCATTER MEDIAN VS MEAN
    # ========================================================================
    
    ax_e = axes[0]
    
    results_1_30 = results_dict[(1, 30)]
    
    # Aggregate stats for all configs (threshold=99%, min_length=30)
    scatter_data = []
    for adm in [1, 2]:
        results = results_dict[(adm, 30)]
        results_99 = results[(results['percentage_threshold'] == 99) & 
                            (results['k'] > 0)].copy()
        
        for window in results_99['context_window_days'].unique():
            bic_vals = results_99[
                results_99['context_window_days'] == window
            ]['BIC'].values
            
            scatter_data.append({
                'adm': adm,
                'window': window,
                'median': np.median(bic_vals),
                'mean': np.mean(bic_vals)
            })
    
    df_scatter = pd.DataFrame(scatter_data)
    
    for adm in [1, 2]:
        df_adm = df_scatter[df_scatter['adm'] == adm]
        color = colors['admin1'] if adm == 1 else colors['admin2']
        ax_e.scatter(df_adm['mean'], df_adm['median'], 
                    s=120, alpha=0.7, color=color, 
                    label=f'Admin {adm}', edgecolors='black', linewidth=1.5)
        
        # Annotate window values
        for idx, (_, row) in enumerate(df_adm.iterrows()):
            window = int(row['window'])
            if adm == 1:
                if window == 10:
                    offset_x, offset_y = -20, -15
                elif window == 15:
                    offset_x, offset_y = 10, 10
                elif window == 20:
                    offset_x, offset_y = -20, 10
                elif window == 25:
                    offset_x, offset_y = 10, -15
                else:
                    offset_x, offset_y = 10, 10
            else:
                if window == 10:
                    offset_x, offset_y = 10, -15
                elif window == 15:
                    offset_x, offset_y = -20, 10
                elif window == 20:
                    offset_x, offset_y = 10, 10
                elif window == 25:
                    offset_x, offset_y = -20, -15
                else:
                    offset_x, offset_y = 10, 10
                    
            ax_e.annotate(f"{window}d", 
                         xy=(row['mean'], row['median']),
                         xytext=(offset_x, offset_y), textcoords='offset points',
                         fontsize=8, fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', 
                                  facecolor='white', edgecolor=color, alpha=0.9))
    
    # Add diagonal line
    lims = [min(ax_e.get_xlim()[0], ax_e.get_ylim()[0]),
            max(ax_e.get_xlim()[1], ax_e.get_ylim()[1])]
    ax_e.plot(lims, lims, 'k--', alpha=0.5, linewidth=1.5, label='Mean = Median')
    
    ax_e.set_xlabel('Mean BIC', fontsize=11, fontweight='bold')
    ax_e.set_ylabel('Median BIC', fontsize=11, fontweight='bold')
    ax_e.set_title('A) Mean vs Median Divergence\n(threshold=99%, min_length=30d)',
                   fontsize=12, fontweight='bold', pad=10)
    ax_e.legend(fontsize=9, loc='lower right', framealpha=0.95)
    ax_e.grid(True, alpha=0.3)
    
    # ========================================================================
    # PANEL D: INVERSE RELATIONSHIP
    # ========================================================================
    
    ax_g = axes[1]
    
    inverse_data = []
    for (adm, length), results in results_dict.items():
        results_valid = results[results['k'] > 0].copy()
        grouped = results_valid.groupby(['percentage_threshold', 'context_window_days'])['BIC']
        median_bic = grouped.median()
        best_idx = median_bic.idxmin()
        
        inverse_data.append({
            'adm': adm,
            'length': length,
            'window': best_idx[1]
        })
    
    df_inverse = pd.DataFrame(inverse_data)
    
    for adm, color_key in [(1, 'admin1'), (2, 'admin2')]:
        df_adm = df_inverse[df_inverse['adm'] == adm].sort_values('length')
        
        ax_g.plot(df_adm['length'], df_adm['window'],
                 marker='o', markersize=14, linewidth=3,
                 color=colors[color_key], label=f'Admin Level {adm}',
                 alpha=0.8)
        
        # Add value labels
        for _, row in df_adm.iterrows():
            if adm == 1:
                y_offset = 18
            else:
                y_offset = 18 if row['length'] == 30 else -22
                
            ax_g.annotate(f"{int(row['window'])}d",
                         xy=(row['length'], row['window']),
                         xytext=(0, y_offset), textcoords='offset points',
                         fontsize=10, fontweight='bold',
                         color=colors[color_key],
                         ha='center',
                         bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                                  edgecolor=colors[color_key], alpha=0.9, linewidth=2))
    
    ax_g.set_xlabel('Min OOS Run Length (days)', fontsize=11, fontweight='bold')
    ax_g.set_ylabel('Optimal Context Window (days)', fontsize=11, fontweight='bold')
    ax_g.set_title('B) Inverse Relationship\nMin Length vs Optimal Window',
                   fontsize=12, fontweight='bold', pad=10)
    ax_g.set_xticks([15, 30])
    ax_g.legend(fontsize=10, loc='upper right', framealpha=0.95)
    ax_g.grid(True, alpha=0.3)
    ax_g.set_ylim(8, 27)
    
    # ========================================================================
    # PANEL E: SENSITIVITY CURVES
    # ========================================================================
    
    ax_f = axes[2]
    
    for adm, color_key in [(1, 'admin1'), (2, 'admin2')]:
        results = results_dict[(adm, 30)]
        results_99 = results[(results['percentage_threshold'] == 99) & 
                            (results['k'] > 0)].copy()
        
        stats = results_99.groupby('context_window_days')['BIC'].agg(['median', 'mean'])
        stats = stats.sort_index()
        
        ax_f.plot(stats.index, stats['median'], 
                 marker='o', markersize=10, linewidth=2.5, 
                 color=colors[color_key], alpha=0.9,
                 label=f'Admin {adm} (median)', linestyle='-')
        ax_f.plot(stats.index, stats['mean'],
                 marker='s', markersize=7, linewidth=2, 
                 color=colors[color_key], alpha=0.5,
                 label=f'Admin {adm} (mean)', linestyle='--')
        
        # Mark best median
        best_median = stats['median'].idxmin()
        ax_f.scatter(best_median, stats.loc[best_median, 'median'],
                    s=300, color=colors[color_key], marker='*',
                    edgecolors='black', linewidths=2.5, zorder=5)
    
    ax_f.set_xlabel('Context Window (days)', fontsize=11, fontweight='bold')
    ax_f.set_ylabel('BIC', fontsize=11, fontweight='bold')
    ax_f.set_title('C) BIC Sensitivity to Window\n(threshold=99%, min_length=30d)',
                   fontsize=12, fontweight='bold', pad=10)
    ax_f.legend(fontsize=8, loc='lower right', framealpha=0.95)
    ax_f.grid(True, alpha=0.3)
    
    # Overall title
    fig.suptitle('Model Selection via BIC Analysis',
                 fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    
    if save_plot:
        filename = 'bic_model_selection_compact.png'
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"Figure saved as: {filename}")
    
    plt.show()