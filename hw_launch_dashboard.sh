#!/bin/bash

WORKSPACE_DIR="$HOME/Desktop/ROS2_rUBot_mecanum_ws"
WEB_DIR="$WORKSPACE_DIR/web"

# Helper for launching new terminals
new_terminal() {
    gnome-terminal -- bash -c "$1; exec bash"
}

echo "1. Launching ENS160 Sensors..."
new_terminal "cd $WORKSPACE_DIR && source install/setup.bash && ros2 launch ens160_sensors ens160_rviz_hw.launch.py"

echo "2. Launching ROS Bridge..."
new_terminal "cd $WORKSPACE_DIR && source install/setup.bash && ros2 run rosbridge_server rosbridge_websocket --port 9090 --address 0.0.0.0 --ros-args -p default_call_service_timeout:=5.0 -p call_services_in_new_thread:=true -p send_action_goals_in_new_thread:=true"

echo "3. Starting HTTP server on port 8000..."
new_terminal "cd $WEB_DIR && python3 -m http.server 8000"

sleep 3

echo "4. Opening Firefox..."
new_terminal "firefox http://localhost:8000/"
