#   python3 /home/valeria/Desktop/ROS2_rUBot_mecanum_ws/src/my_robot_co2map/scripts/yaml_bounds.py

from PIL import Image
import yaml
from pathlib import Path

# --- Path to specific map YAML ---
yaml_path = Path("/home/valeria/Desktop/ROS2_rUBot_mecanum_ws/src/Navigation_Projects/my_robot_navigation2/map/passadis.yaml")

# Load map YAML
with open(yaml_path) as f:
    map_yaml = yaml.safe_load(f)

# Load image to get dimensions
# The image path in the YAML might be relative, so resolve it relative to the YAML folder
image_path = yaml_path.parent / map_yaml['image']
img = Image.open(image_path)
width, height = img.size

# Map metadata
res = map_yaml['resolution']
origin_x, origin_y, _ = map_yaml['origin']

# Compute map bounds in meters
x_min = origin_x
y_min = origin_y
x_max = origin_x + width * res
y_max = origin_y + height * res

print(f"Map bounds (meters): x=[{x_min}, {x_max}], y=[{y_min}, {y_max}]")
