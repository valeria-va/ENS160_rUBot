#!/usr/bin/env python3
"""Inverted Distance Weighted Interpolation CO2 Map Plotter"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import yaml

# -----------------------------
# CONFIGURATION
# -----------------------------
csv_path = Path(r"C:\Users\valer\Documents\TFG\ROS2_rUBot_mecanum_ws\src\my_robot_co2map\ens160_logs\processed_sensor_data_passadis1.csv")
yaml_path = Path(r"C:\Users\valer\Documents\TFG\ROS2_rUBot_mecanum_ws\src\Navigation_Projects\my_robot_navigation2\map\passadis.yaml")

square_size = 0.3  # meters per grid square
eco2_min, eco2_max = 400, 1200  # clamp CO2 values
max_path_gap = 0.3  # meters, don't connect points farther than this

# Set to None to average all channels, or to an integer channel index
channel_to_plot = 0     # e.g. 5 for channel 5, or None for average

# -----------------------------
# LOAD SENSOR DATA
# -----------------------------
df = pd.read_csv(csv_path)

if channel_to_plot is None:
    # Group by Pose_X and Pose_Y, average eCO2 across all channels for that position
    grouped = df.groupby(['Pose_X', 'Pose_Y'])['eCO2'].mean().reset_index()
    title_suffix = "average over all channels"
else:
    # Filter by channel and do not average over channels
    df_ch = df[df['Channel'] == channel_to_plot].copy()
    grouped = df_ch.groupby(['Pose_X', 'Pose_Y'])['eCO2'].mean().reset_index()
    title_suffix = f"Channel {channel_to_plot}"

x_data = grouped['Pose_X'].to_numpy()
y_data = grouped['Pose_Y'].to_numpy()
co2_data = grouped['eCO2'].clip(eco2_min, eco2_max).to_numpy()

# -----------------------------
# LOAD MAP YAML
# -----------------------------
with open(yaml_path) as f:
    map_yaml = yaml.safe_load(f)

image_path = Path(map_yaml['image'])
if not image_path.is_absolute():
    image_path = yaml_path.parent / image_path

img = Image.open(image_path)
img = img.transpose(Image.FLIP_TOP_BOTTOM)
width_px, height_px = img.size
res = map_yaml['resolution']
origin_x, origin_y, _ = map_yaml['origin']

x_min = origin_x
y_min = origin_y
x_max = origin_x + width_px * res
y_max = origin_y + height_px * res

print(f"Map bounds (meters): x=[{x_min}, {x_max}], y=[{y_min}, {y_max}]")

# -----------------------------
# CREATE GRID COVERING FULL MAP
# -----------------------------
x_bins = np.arange(x_min, x_max, square_size)
y_bins = np.arange(y_min, y_max, square_size)

xx, yy = np.meshgrid(x_bins + square_size/2, y_bins + square_size/2)
grid_shape = xx.shape
co2_grid = np.zeros(grid_shape)

# -----------------------------
# COMPUTE WEIGHTED CO2 USING INVERSE DISTANCE SQUARED
# -----------------------------
grid_points = np.column_stack([xx.ravel(), yy.ravel()])
sensor_points = np.column_stack([x_data, y_data])

for i, gp in enumerate(grid_points):
    dists = np.linalg.norm(sensor_points - gp, axis=1)
    weights = 1 / (dists**2 + 1e-6)
    co2_grid.ravel()[i] = np.sum(weights * co2_data) / np.sum(weights)

# -----------------------------
# PLOT MAP
# -----------------------------
fig = plt.figure(figsize=(13, 13), constrained_layout=True)
plt.subplots_adjust(left=0.04, right=0.96, top=0.96, bottom=0.04)

extent = [x_min, x_max, y_min, y_max]

# Background map
plt.imshow(np.array(img), origin='lower', extent=extent, cmap='gray', alpha=0.3)

# CO2 heatmap
im = plt.imshow(
    co2_grid,
    origin='lower',
    extent=extent,
    cmap='jet',
    interpolation='nearest',
    alpha=0.7,
    vmin=eco2_min,
    vmax=eco2_max,
    aspect='equal'
)

# Colorbar
cbar = plt.colorbar(im, fraction=0.03)  # 0.03 if rajoles and 0.02 if passadis
cbar.set_label('eCO₂ (ppm)')


plt.title(f"eCO₂ Map ({title_suffix})")
plt.xlabel("X (meters)")
plt.ylabel("Y (meters)")
plt.grid(False)

plt.show()
