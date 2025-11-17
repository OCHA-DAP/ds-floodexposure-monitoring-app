import pandas as pd
import ocha_stratus as stratus   # need v 0.1.5
from constants import ISO3S
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from itertools import product
import os

"""
DEFAULT
container = "dev"
adm_level = 1
rolling_sum_days = 5 
context_window_days = 30 # Number of days before and after to consider
percentage_threshold = 99 # Threshold for out of season classification (%)
min_oss_run_length = 30 # Minimum consecutive days to consider a period as OOS
"""

# ==================== PARAMETER GRID ====================
PERCENTAGE_GRID = [95, 96, 97, 98, 99]
WINDOW_DAYS_GRID = [10, 15, 20, 25, 30]
ADM_LEVEL_GRID = [0, 1, 2]
MIN_OOS_RUN_LENGTH_GRID = [15, 30]
# =======================================================


def process_pcode(pcode, df, iso3, rolling_sum_days, context_window_days, percentage_threshold, min_oos_run_length):
    """Process a single pcode - helper function for parallelization"""
    pc_data = df.loc[df["pcode"] == pcode].copy()
    
    # Perform analysis
    zero_pct_data, _ = calculate_zero_percentage_data(pc_data, rolling_sum_days)
    context_data = detect_OOS(zero_pct_data, context_window_days, percentage_threshold, min_oos_run_length)
    
    # Add iso3 column
    context_data["iso3"] = iso3
    
    return context_data


def run_analysis(
        container="dev",
        adm_level=1,
        rolling_sum_days=5, 
        context_window_days=30, 
        percentage_threshold=99, 
        min_oos_run_length=30, 
        max_workers=4,
        verbose=True
        ):
    """
    Run analysis with parallelization and progress tracking.
    
    Parameters:
    -----------
    max_workers : int
        Number of parallel workers (default: 4)
    """
    all_states_results = []

    # Loop through countries (serial - database reads)
    for iso3_l in (tqdm(ISO3S, desc="Processing countries") if verbose else ISO3S):
        iso3 = iso3_l.upper()
        df = get_iso3_data(iso3, container)

        # Filter for adm_level
        df = df.loc[df['adm_level'] == adm_level].copy()
        
        pcodes = df["pcode"].unique()
        
        # Parallelize pcode processing (CPU-bound calculations)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_pcode = {
                executor.submit(process_pcode, pcode, df, iso3, rolling_sum_days, context_window_days, percentage_threshold, min_oos_run_length): pcode 
                for pcode in pcodes
            }
            
            # Collect results with progress bar
            for future in tqdm(
                as_completed(future_to_pcode), 
                total=len(pcodes),
                desc=f"Processing {iso3} pcodes",
                leave=False
            ) if verbose else as_completed(future_to_pcode):
                try:
                    context_data = future.result()
                    all_states_results.append(context_data)
                except Exception as e:
                    pcode = future_to_pcode[future]
                    print(f"Error processing {iso3} - {pcode}: {e}")

    # Concatenate to unique dataframe
    final_df = pd.concat(all_states_results, ignore_index=True)

    final_df["data"] = container
    final_df["adm_level"] = adm_level
    final_df["rolling_sum_days"] = rolling_sum_days
    final_df["context_window_days"] = context_window_days
    final_df["percentage_threshold"] = percentage_threshold
    final_df["min_oos_run_length"] = min_oos_run_length

    
    # Sort columns
    columns_order = ["iso3", "adm_level", "pcode", "month_day", "zero_pct", 
                     "context_zero_pct", "is_out_of_season_raw", "is_out_of_season", 
                      "rolling_sum_days", "context_window_days",
                      "percentage_threshold", "min_oos_run_length", "data"]
    
    final_df = final_df[columns_order]
    
    # Sort rows
    final_df = final_df.sort_values(["iso3", "pcode", "month_day"]).reset_index(drop=True)

    return final_df


def get_iso3_data(iso3, container):
    engine = stratus.get_engine(container)

    with engine.connect() as conn:
        df = pd.read_sql(
            f"""
            SELECT * FROM app.floodscan_exposure 
            WHERE iso3 = '{iso3}'
            """,
            con=conn,
        )

    return df


def calculate_zero_percentage_data(df_adm_filtered, rolling_sum_days=5):

    df_adm_filtered["year"] = pd.to_datetime(df_adm_filtered["valid_date"]).dt.year

    df_adm_filtered = df_adm_filtered.sort_values(
        by=["pcode", "year", "valid_date"]
    )
    df_adm_filtered["rolling_sum_5day"] = df_adm_filtered.groupby(
        ["pcode", "year"]
    )["sum"].transform(lambda x: x.rolling(window=rolling_sum_days, min_periods=1).sum())

    # Extract month and day
    df_adm_filtered["valid_date"] = pd.to_datetime(df_adm_filtered["valid_date"])
    df_adm_filtered["month_day"] = df_adm_filtered["valid_date"].dt.strftime(
        "%m-%d"
    )

    # Ensure month_day exists and is sorted
    df_adm_filtered["month_day"] = pd.to_datetime(
        df_adm_filtered["valid_date"]
    ).dt.strftime("%m-%d")

    # Calculate zero percentage for each pcode-month_day combination
    zero_pct_data = (
        df_adm_filtered.groupby(["pcode", "month_day"])["rolling_sum_5day"]
        .apply(lambda x: (x == 0).sum() / len(x) * 100)
        .reset_index()
    )
    zero_pct_data.columns = ["pcode", "month_day", "zero_pct"]

    # Sort by month_day to ensure chronological order
    zero_pct_data = zero_pct_data.sort_values(["pcode", "month_day"])

    return zero_pct_data, df_adm_filtered


def detect_OOS(zero_pct_data, context_window_days=30, percentage_threshold=99, min_oos_run_length=30):

    context_results = []
    for pcode in zero_pct_data["pcode"].unique():
        pcode_group = zero_pct_data[zero_pct_data["pcode"] == pcode]
        pcode_result = calculate_context_zero_pct(
            pcode_group, window=context_window_days
        )
        context_results.append(pcode_result)

    context_data = pd.concat(context_results, ignore_index=True)

    # Classify as out_of_season if context zero percentage >= PERCENTAGE_THRESHOLD
    context_data["is_out_of_season_raw"] = (
        context_data["context_zero_pct"] >= percentage_threshold
    )

    # Apply minimum cluster length filter per pcode
    filtered_oos = []
    for pcode in context_data["pcode"].unique():
        pcode_mask = context_data["pcode"] == pcode
        pcode_data = context_data[pcode_mask].sort_values("month_day").copy()

        # Filter short periods
        pcode_data["is_out_of_season"] = filter_short_oos_periods(
            pcode_data["is_out_of_season_raw"], min_length=min_oos_run_length
        )

        filtered_oos.append(pcode_data)

    context_data = pd.concat(filtered_oos, ignore_index=True)

    return context_data


# Function to calculate rolling mean of zero percentage around each day
def calculate_context_zero_pct(group, window=30):
    """
    Calculate the mean zero percentage in a ±window day window around each day
    """
    # Convert month_day to ordinal for easier calculation
    group = group.copy()
    group["day_of_year"] = pd.to_datetime(
        "2020-" + group["month_day"]
    ).dt.dayofyear
    group = group.sort_values("day_of_year")

    result = []
    for idx, row in group.iterrows():
        current_day = row["day_of_year"]

        # Calculate days in window (handling year wraparound)
        days_in_window = []
        for day in group["day_of_year"]:
            # Calculate circular distance (accounting for year boundary)
            dist = min(abs(day - current_day), 365 - abs(day - current_day))
            if dist <= window:
                days_in_window.append(day)

        # Get zero_pct for days in window
        window_data = group[group["day_of_year"].isin(days_in_window)]
        context_zero_pct = window_data["zero_pct"].mean()

        result.append(
            {
                "pcode": row["pcode"],
                "month_day": row["month_day"],
                "zero_pct": row["zero_pct"],
                "context_zero_pct": context_zero_pct,
            }
        )

    return pd.DataFrame(result)


def filter_short_oos_periods(is_oos_series, min_length=30):
    """
    Remove OOS periods shorter than min_length consecutive days
    Handles year wraparound (Dec-Jan boundary)
    Returns a boolean series with short periods removed
    """
    if len(is_oos_series) == 0:
        return is_oos_series.copy()

    result = is_oos_series.copy()

    # Find all OOS segments
    segments = []
    in_segment = False
    start_idx = None

    for i in range(len(is_oos_series)):
        if is_oos_series.iloc[i] and not in_segment:
            # Start of new segment
            start_idx = i
            in_segment = True
        elif not is_oos_series.iloc[i] and in_segment:
            # End of segment
            segments.append((start_idx, i - 1))
            in_segment = False

    # Handle case where last day(s) are OOS
    if in_segment:
        segments.append((start_idx, len(is_oos_series) - 1))

    # Check for wraparound: if both first and last segments touch the boundaries
    if len(segments) >= 2:
        first_seg = segments[0]
        last_seg = segments[-1]

        # If first segment starts at day 0 AND last segment ends at last day
        if first_seg[0] == 0 and last_seg[1] == len(is_oos_series) - 1:
            # Merge these segments
            merged_length = (first_seg[1] - first_seg[0] + 1) + (
                last_seg[1] - last_seg[0] + 1
            )

            if merged_length >= min_length:
                # Keep both segments (they form one valid period)
                segments_to_keep = segments
            else:
                # Remove both segments (merged period too short)
                segments_to_keep = segments[1:-1]  # Keep only middle segments
        else:
            # No wraparound, filter normally
            segments_to_keep = [
                seg for seg in segments if (seg[1] - seg[0] + 1) >= min_length
            ]
    else:
        # Only 0 or 1 segment, filter normally
        segments_to_keep = [
            seg for seg in segments if (seg[1] - seg[0] + 1) >= min_length
        ]

    # Create result: set all to False, then set kept segments to True
    result[:] = False
    for start_idx, end_idx in segments_to_keep:
        result.iloc[start_idx : end_idx + 1] = True

    return result

def run_parameter_grid_search(
    container="dev",
    rolling_sum_days=5,
    output_dir="grid_search_results",
    max_workers=4
):
    """
    Run analysis across all parameter combinations in the grid.
    Skips combinations where parquet file already exists.
    """
    
    # Generate all parameter combinations
    param_combinations = list(product(
        ADM_LEVEL_GRID,
        MIN_OOS_RUN_LENGTH_GRID,
        PERCENTAGE_GRID,
        WINDOW_DAYS_GRID
    ))
    
    print(f"Total combinations: {len(param_combinations)}")
    
    # Iterate through all combinations
    for i, (adm_level, min_oos_length, pct_threshold, window_days) in enumerate(
        tqdm(param_combinations, desc="Grid Search"), 1
    ):
        try:
            # Create directory structure
            dir_path = os.path.join(output_dir, f"adm{adm_level}", f"length{min_oos_length}")
            os.makedirs(dir_path, exist_ok=True)
            
            # Create file name
            file_name = f"adm{adm_level}_length{min_oos_length}_pct{pct_threshold}_win{window_days}.parquet"
            output_file = os.path.join(dir_path, file_name)
            
            # Skip if file already exists
            if os.path.exists(output_file):
                tqdm.write(f"Skipping existing: {file_name}")
                continue
            
            tqdm.write(f"[{i}/{len(param_combinations)}] Processing adm{adm_level}, length{min_oos_length}, pct{pct_threshold}, win{window_days}")
            # Run analysis
            result_df = run_analysis(
                container=container,
                adm_level=adm_level,
                rolling_sum_days=rolling_sum_days,
                context_window_days=window_days,
                percentage_threshold=pct_threshold,
                min_oos_run_length=min_oos_length,
                max_workers=max_workers,
                verbose=False
            )
            
            # Save results
            result_df.to_parquet(output_file, index=False)
            
        except Exception as e:
            tqdm.write(f"\nError with adm{adm_level}_length{min_oos_length}_pct{pct_threshold}_win{window_days}: {e}")
    
    print(f"\nCompleted! Results saved in: {output_dir}/")