import pandas as pd
import numpy as np

filename= "sensor_data_passadis1.csv"
raw_data = pd.read_csv(filename)

raw_data["Timestamp"] = pd.to_datetime(raw_data["Timestamp"], format="ISO8601") 
"""If working with other formats, adjust the format accordingly. For instance just with sensors
raw_data["Timestamp"] = pd.to_datetime(raw_data["Timestamp"], format="%Y-%m-%d %H:%M:%S.%f") 
"""

raw_data["Time_s"] = (raw_data["Timestamp"] - raw_data["Timestamp"].iloc[0]).dt.total_seconds()

import pandas as pd
import numpy as np

def remove_drift_and_baseline_and_shift_to_raw_min(
    df,
    time_col='Timestamp',
    value_col='eCO2',
    channel_col='Channel',
    baseline_n=200  # number of first samples per channel used for baseline
):
    """
    For each channel:
      1) Remove linear drift (first-order polynomial).
      2) Compute baseline as the mean of the first `baseline_n` points
         (after detrending) and subtract it (align around 0).
      3) Shift all channels upward so the global minimum equals the
         minimum value in the original raw data (restore realistic ppm).
    """
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')

    # Global time zero
    t0 = df[time_col].min()
    df['Time_s'] = (df[time_col] - t0).dt.total_seconds().astype(float)

    # --- NEW: global minimum from the raw data ---
    raw_global_min = df[value_col].min()

    def process_channel(g):
        X = g['Time_s'].values
        y = g[value_col].values.astype(float)

        if len(X) < 2 or np.all(np.isnan(y)):
            g[channel_col] = g.name
            return g

        # 1) Fit linear drift
        try:
            m, b = np.polyfit(X, y, 1)
        except Exception:
            m, b = 0.0, np.nanmean(y)

        linear_drift = m * X
        detrended = y - linear_drift

        # 2) Compute baseline from first baseline_n samples (after detrending)
        n = min(baseline_n, len(detrended))
        baseline = np.nanmean(detrended[:n])

        # 3) Subtract baseline (align curves around 0)
        y_corrected = detrended - baseline

        g[value_col] = y_corrected
        g[channel_col] = g.name
        return g

    processed_df = df.groupby(channel_col, group_keys=False).apply(
        process_channel,
        include_groups=False
    )

    # --- NEW: shift everything back to realistic ppm ---
    corrected_global_min = processed_df[value_col].min()
    final_shift = raw_global_min - corrected_global_min
    processed_df[value_col] = processed_df[value_col] + final_shift

    processed_df = processed_df.drop(columns=['Time_s'])
    return processed_df

processed_df = remove_drift_and_baseline_and_shift_to_raw_min(
    raw_data,
    time_col='Timestamp',
    value_col='eCO2',
    channel_col='Channel',
    baseline_n=200
)

processed_df.to_csv("processed_" + filename, index=False)

