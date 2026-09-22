#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from ens160_interfaces.msg import SensorData
import csv
from datetime import datetime
import os
import math
from std_srvs.srv import Trigger  # Simple start/stop logging service

class CSVLogger(Node):
    def __init__(self):
        super().__init__('csv_logger')

        # --- Directory for logs ---
        self.log_dir = os.path.expanduser('~/ens160_logs')
        os.makedirs(self.log_dir, exist_ok=True)

        # --- CSV logging ---
        self.logging_enabled = False
        self.csv_path = None  # will be set when logging starts

        # --- Latest sensor & odom ---
        self.sensor_data = None
        self.odom_data = None

        # --- Subscriptions ---
        self.sensor_sub = self.create_subscription(
            SensorData, 'ens160_data', self.sensor_callback, 10)
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10)

        # --- Services to start/stop logging ---
        self.start_srv = self.create_service(Trigger, 'start_csv_logging', self.start_logging)
        self.stop_srv = self.create_service(Trigger, 'stop_csv_logging', self.stop_logging)

        self.get_logger().info("CSVLogger node initialized. Call 'start_csv_logging' service to begin.")

    # -----------------------------
    # Sensor callback
    # -----------------------------
    def sensor_callback(self, msg):
        self.sensor_data = msg  # store the full SensorData message
        if self.logging_enabled:
            self.write_csv()

    # -----------------------------
    # Odometry callback
    # -----------------------------
    def odom_callback(self, msg):
        p = msg.pose.pose.position
        o = msg.pose.pose.orientation
        # Correct yaw from quaternion
        yaw = math.atan2(2*(o.w*o.z + o.x*o.y), 1 - 2*(o.y*o.y + o.z*o.z))
        self.odom_data = (p.x, p.y, yaw)

    # -----------------------------
    # Write CSV
    # -----------------------------
    def write_csv(self):
        if self.sensor_data is None or self.odom_data is None or self.csv_path is None:
            return

        timestamp = datetime.now().isoformat()
        x, y, yaw = self.odom_data

        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                self.sensor_data.channels[0] if self.sensor_data.channels else -1,
                self.sensor_data.pose_x,
                self.sensor_data.pose_y,
                self.sensor_data.pose_theta,
                *self.sensor_data.sensor_readings
            ])

    # -----------------------------
    # Start logging service
    # -----------------------------
    def start_logging(self, request, response):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.join(self.log_dir, f'sensor_log_{timestamp}.csv')
        # Write header
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
    node = CSVLogger()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
