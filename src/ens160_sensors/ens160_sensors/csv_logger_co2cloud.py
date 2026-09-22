#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from ens160_interfaces.msg import SensorData
import csv
from datetime import datetime
import os
import math
from std_srvs.srv import Trigger
import tf2_ros
import geometry_msgs.msg

class CSVLoggerCO2Cloud(Node):
    def __init__(self):
        super().__init__('csv_logger_co2cloud')

        # --- Directory for logs ---
        self.log_dir = os.path.expanduser('~/ens160_logs')
        os.makedirs(self.log_dir, exist_ok=True)

        # --- CSV logging ---
        self.logging_enabled = False
        self.csv_path = None

        # --- Latest sensor data ---
        self.sensor_data = None

        # --- TF ---
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # --- Subscriptions ---
        self.sensor_sub = self.create_subscription(
            SensorData, 'ens160_data', self.sensor_callback, 10)

        # --- Services to start/stop logging ---
        self.start_srv = self.create_service(Trigger, 'start_csv_logging', self.start_logging)
        self.stop_srv = self.create_service(Trigger, 'stop_csv_logging', self.stop_logging)

        self.get_logger().info("CSVLogger node initialized. Call 'start_csv_logging' service to begin.")

    # -----------------------------
    # Sensor callback
    # -----------------------------
    def sensor_callback(self, msg):
        self.sensor_data = msg
        if self.logging_enabled:
            self.write_csv()

    # -----------------------------
    # Get robot pose in map frame
    # -----------------------------
    def get_map_pose(self):
        try:
            t = self.tf_buffer.lookup_transform(
                'map',            # target frame
                'base_link',      # source frame
                rclpy.time.Time()
            )
            x = t.transform.translation.x
            y = t.transform.translation.y
            q = t.transform.rotation
            yaw = math.atan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y*q.y + q.z*q.z))
            return x, y, yaw
        except (tf2_ros.LookupException, tf2_ros.ExtrapolationException, tf2_ros.ConnectivityException):
            self.get_logger().warn("TF lookup failed for map -> base_link")
            return None, None, None

    # -----------------------------
    # Write CSV
    # -----------------------------
    def write_csv(self):
        if self.sensor_data is None or self.csv_path is None:
            return

        x, y, yaw = self.get_map_pose()
        if x is None:
            return  # skip if TF not available

        timestamp = datetime.now().isoformat()

        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                self.sensor_data.channels[0] if self.sensor_data.channels else -1,
                x,          # Pose_X in map frame
                y,          # Pose_Y in map frame
                yaw,        # Pose_Theta in map frame
                *self.sensor_data.sensor_readings
            ])

    # -----------------------------
    # Start logging service
    # -----------------------------
    def start_logging(self, request, response):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.join(self.log_dir, f'sensor_log_{timestamp}.csv')
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Timestamp', 'Channel', 'Pose_X', 'Pose_Y', 'Pose_Theta',
                'eCO2', 'TVOC', 'AQI', 'R0', 'R1', 'R2', 'R3'
            ])
        self.logging_enabled = True
        response.success = True
        response.message = f"Logging started: {self.csv_path}"
        self.get_logger().info(response.message)
        return response

    # -----------------------------
    # Stop logging service
    # -----------------------------
    def stop_logging(self, request, response):
        self.logging_enabled = False
        response.success = True
        response.message = "Logging stopped."
        self.get_logger().info(response.message)
        return response

# -----------------------------
# Main
# -----------------------------
def main(args=None):
    rclpy.init(args=args)
    node = CSVLoggerCO2Cloud()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
