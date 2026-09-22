import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# -----------------------------
# CONFIGURE YOUR INPUT FILES
# -----------------------------
csv1 = Path(r"C:\Users\valer\Documents\TFG\ROS2_rUBot_mecanum_ws\src\my_robot_co2map\ens160_logs\sensor_log_20251219_113305.csv")
csv2 = Path(r"C:\Users\valer\Documents\TFG\ROS2_rUBot_mecanum_ws\src\my_robot_co2map\ens160_logs\sensor_log_20251219_125455.csv")
csv3 = Path(r"C:\Users\valer\Documents\TFG\ROS2_rUBot_mecanum_ws\src\my_robot_co2map\ens160_logs\sensor_log_20251219_132044.csv")

# -----------------------------
# FUNCTION: LOAD CSV + ADD ELAPSED TIME COLUMN
# -----------------------------
def load_with_elapsed(csv_path):
    df = pd.read_csv(csv_path)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="mixed")
    df["Elapsed_s"] = (df["Timestamp"] - df["Timestamp"].iloc[0]).dt.total_seconds()
    return df

# -----------------------------
# LOAD EACH CSV
# -----------------------------
df1 = load_with_elapsed(csv1)
df2 = load_with_elapsed(csv2)
df3 = load_with_elapsed(csv3)

# -----------------------------
# FILTER BY ELAPSED TIME
# -----------------------------
df1_f = df1.copy()                     # keep all of CSV1
df2_f = df2[df2["Elapsed_s"] <= 1200]  # keep first 1500s of CSV2
df3_f = df3.copy()                     # keep all of CSV3

# -----------------------------
# SHIFT ELAPSED TIME TO MAKE CONTINUOUS TIMELINE
# -----------------------------
# End of CSV1
end1 = df1_f["Elapsed_s"].max()

# Shift CSV2 so it starts immediately after CSV1
df2_f["Elapsed_s"] = df2_f["Elapsed_s"] - df2_f["Elapsed_s"].min() + end1

# End of CSV2
end2 = df2_f["Elapsed_s"].max()

# Shift CSV3 so it starts immediately after CSV2
df3_f["Elapsed_s"] = df3_f["Elapsed_s"] - df3_f["Elapsed_s"].min() + end2

# -----------------------------
# MERGE THE THREE FILTERED DATASETS
# -----------------------------
merged = pd.concat([df1_f, df2_f, df3_f], ignore_index=True)

print("Merged dataset shape:", merged.shape)
print(merged.head())

# -----------------------------
# SAVE RESULT
# -----------------------------
merged.to_csv("merged_filtered.csv", index=False)

# -----------------------------
# PLOT eCO2 vs TIME (BY CHANNEL)
# -----------------------------
plt.figure(figsize=(6, 3))

for ch in sorted(merged["Channel"].unique()):
    df_ch = merged[merged["Channel"] == ch]
    plt.plot(df_ch["Elapsed_s"], df_ch["eCO2"], linewidth=1.5, label=f"Channel {ch}")

plt.xlabel("Time (s)")
plt.ylabel("eCO₂ (ppm)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
