# python3 /home/valeria/Desktop/ROS2_rUBot_mecanum_ws/src/my_robot_co2map/scripts/plot_waypoints.py 

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- CONFIGURATION ---
#csv_path = Path("/home/valeria/Desktop/ROS2_rUBot_mecanum_ws/src/my_robot_co2map/ens160_logs/sensor_log_20251218_165354.csv")
csv_path = Path(r"C:\Users\valer\Documents\TFG\ROS2_rUBot_mecanum_ws\src\my_robot_co2map\ens160_logs\sensor_log_20251217_142216.csv")

# Adjustable plotting parameters
point_size = 20       # Size of scatter points
plot_range = None      # Set to [[xmin, xmax], [ymin, ymax]] to zoom in, or None for auto

# --- 1. LOAD DATA ---
df = pd.read_csv(csv_path)

# --- 2. GROUP BY POSE AND AVERAGE SENSOR VALUES ---
# Average only eCO2 per pose (ignore other sensor channels for coloring)
grouped = df.groupby(['Pose_X', 'Pose_Y'])['eCO2'].mean().reset_index()

x_coords = grouped['Pose_Y'].to_numpy()  # Y-axis as horizontal
y_coords = grouped['Pose_X'].to_numpy()  # X-axis as vertical
co2_levels = grouped['eCO2'].to_numpy()  # Only eCO2 for color

# --- 3. PLOT ---
plt.figure(figsize=(10, 8))
scatter = plt.scatter(x_coords, y_coords,
                      c=co2_levels,
                      cmap='rainbow',
                      s=point_size,
                      alpha=0.8,
                      label='Trajectory Points')


# Colorbar
cbar = plt.colorbar(scatter)
cbar.set_label('Average eCO2 Level (PPM)', fontsize=12)

# Personalization
plt.title("Robot Trajectory Colored by Average eCO2")
plt.xlabel("Pose X (meters)", fontsize=12)
plt.ylabel("Pose Y (meters)", fontsize=12)
plt.grid(True, linestyle=':')
plt.axis('equal')

# Apply custom range if specified
if plot_range:
    plt.xlim(plot_range[0])
    plt.ylim(plot_range[1])

plt.show()
