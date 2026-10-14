# rUBot eCO₂ Indoor Mapping

![eCO2 Sensing Mobile Robot](src/my_robot_co2map/img/ENS160_rUBot.png)

ROS 2 Humble project for indoor eCO₂ mapping using **rUBot**, a mobile mecanum-wheeled robot equipped with an array of ENS160 gas sensors. The system combines SLAM, robot localization and gas sensing to record spatially associated measurements, visualize eCO₂ levels in RViz, and generate offline concentration maps.

![Corridor eCO₂ mapping results](src/my_robot_co2map/img/Corridor_results.png)

## Features

- Indoor mapping and navigation using SLAM and Nav2.
- Acquisition of eCO₂, TVOC, AQI and sensor resistance readings.
- Real-time eCO₂ point-cloud visualization in RViz.
- CSV logging for stationary experiments and mobile gas mapping.
- Offline eCO₂ heatmap generation using spatial interpolation.

## Requirements

- ROS 2 Humble and Ubuntu 22.04.
- rUBot hardware and ENS160 sensors for physical experiments.
- The required workspace packages and dependencies.

## How to Use

### 1. Connect to the robot

The Raspberry Pi is accessed remotely via SSH. The robot and the PC used to run ROS 2 commands should be connected to the same local WLAN, with ROS 2 network discovery configured between them.

```bash
ssh <username>@<robot_ip>
```

Replace the placeholders with the Raspberry Pi's username and IP address.

### 2. Build the workspace

After cloning the repository and obtaining its dependencies, build the workspace on the computer where the packages will run:

```bash
cd ~/ROS2_rUBot_mecanum_ws

source /opt/ros/humble/setup.bash

rosdep install --from-paths src --ignore-src -r -y

colcon build --symlink-install

source install/setup.bash
```

In each new terminal, source the workspace before running ROS 2 commands.

### 3. Bring up the robot and generate a SLAM map

When the robot is powered on, the Raspberry Pi automatically starts `my_robot_bringup_co2cloud_hw.launch.py`. This bringup starts the configured hardware drivers, `robot_state_publisher`, ENS160 acquisition and the eCO₂ cloud node.

Start Cartographer separately, using the launch file provided in `my_robot_cartographer`. The hardware bringup must already be running, so do not start duplicate hardware drivers.

Drive the robot through the environment while monitoring the map in RViz. Once the map is complete, save it:

```bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/ROS2_rUBot_mecanum_ws/src/my_robot_navigation2/map/desired_map_name
```

This generates a YAML file and its corresponding map image. Keep both files together and ensure the YAML references the correct image.

**This mapping step is only necessary when creating or updating the map.**

### 4. Launch localization using the saved map

Stop Cartographer once the map has been saved. Keep the robot hardware running and launch the Nav2 configuration with the saved map:

```bash
ros2 launch my_robot_navigation2 navigation2_robot.launch.py \
  use_sim_time:=false \
  map_file:=desired_map_name.yaml \
  params_file:=rubot_real_lidar.yaml
```

The map must be installed in the package's configured `map` directory. If a new map was generated in the source directory, rebuild the package so that the installed copy is updated.

### 5. Record and visualize eCO₂ measurements

The `sensor_pose_node_hw` node reads ENS160 measurements and publishes sensor readings with odometry-derived pose information on `/ens160_data`.

The `eco2_cloud` node uses TF2 to place measurements in the global `map` frame and publishes `/eco2_cloud` for live visualization.

In RViz, add a **PointCloud2** display, select `/eco2_cloud`, set the Fixed Frame to `map`, and adjust the point size and colour settings.

To record measurements, enable CSV logging using the `csv_logger_enabled` argument in the hardware bringup, or run the standalone logger if the bringup logger is not already handling the experiment:

```bash
ros2 run ens160_sensors csv_logger_co2cloud
```
**Stopping CSV data acquisition:** To stop the CSV logger and finish the current data acquisition session, press `Ctrl+C` in the terminal where the logger is running.

### 6. Generate the offline heatmap

Transfer the recorded CSV file to the external computer if necessary. Use the plotting scripts in `src/my_robot_co2map/scripts/`, providing the CSV and corresponding map YAML paths.

Offline analysis does not require the robot or ROS 2 network to be running.

## Main Nodes and Topics

| Node | Function |
|---|---|
| `sensor_pose_node_hw` | Reads ENS160 measurements and publishes sensor data with odometry-derived pose information. |
| `eco2_cloud` | Uses TF2 to place measurements in the `map` frame and publishes the point cloud. |
| `csv_logger` | Records sensor measurements without robot pose information. |
| `csv_logger_co2cloud` | Records sensor measurements with robot pose information for spatial mapping. |

