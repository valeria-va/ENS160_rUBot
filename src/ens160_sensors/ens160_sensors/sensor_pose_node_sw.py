#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry # Robot's pose
from ens160_interfaces.msg import SensorData # Custom message format (from the sensors)
import transforms3d.euler as t3d_euler
import numpy as np

import random 

class SensorPoseNode(Node):
    """
    Subscribes to robot odometry to track pose and generates RANDOM sensor data.
    It fuses these two inputs and publishes the complete data set using the custom SensorData message.
    """
    def __init__(self):
        super().__init__('sensor_pose_node_sw')
        
        # --- Configuration Constants ---
        self.NUM_CHANNELS = 6
        self.KEYS_PER_CHANNEL = 7
        self.TOTAL_SENSOR_COUNT = self.NUM_CHANNELS * self.KEYS_PER_CHANNEL # 42 expected keys

        self.SENSOR_RANGES = {
            'eCO2': (400.0, 65000.0), # Equivalent CO2 in ppm
            'TVOC': (0.0, 6000.0), # Total Volatile Organic Compounds in ppb
            'AQI': (1.0, 5.0), # Air Quality Index (1=Excellent, 5=Poor)
            'R0': (30000, 100000), # Baseline resistance
            'R1': (1, 1),
            'R2': (15000, 200000),
            'R3': (1000, 150000),
        }

        self.EXPECTED_KEYS = list(self.SENSOR_RANGES.keys())
        self.get_logger().info('Running in DUMMY data mode. Serial connection bypassed.')
            
        # --- Robot State Variables ---
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_theta = 0.0
        
        # --- Odometry Subscriber ---
        self.odom_subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10)
        
        # --- Fused Data Publisher ---
        self.sensor_publisher = self.create_publisher(
            SensorData,
            'ens160_data', 
            10)
            
        # --- Timer to trigger data reading and publishing (1 Hz) ---
        self.sensor_timer = self.create_timer(1.0, self.publish_fused_data) 

        self.get_logger().info('Sensor-Pose Fusion Node started. Generating random sensor data.')

    def odom_callback(self, msg):
        """
        Extracts position (x, y) and yaw (theta) from incoming Odometry messages.
        
        FIX: Removed trailing commas that created tuples.
        """
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        
        # Convert orientation quaternion to Euler angles
        q = msg.pose.pose.orientation
        quat_array = np.array([q.w, q.x, q.y, q.z])
        roll, pitch, yaw = t3d_euler.quat2euler(quat_array, axes='rzyx')
        self.robot_theta = yaw

    def read_ens160_sensors(self):
        """
        Generates random sensor data for 6 channels and 7 keys per channel.
        
        Returns: A list of 42 floats (7 keys * 6 channels).
        """
        final_data = []
        
        # Generate data for 6 channels
        for _ in range(self.NUM_CHANNELS): 
            
            # Generate 7 values per channel
            for key in self.EXPECTED_KEYS:
                low, high = self.SENSOR_RANGES[key]
                
                # Generate a random float within the defined range
                random_value = random.uniform(low, high)
                final_data.append(random_value)
                
        # We guarantee a list of 42 floats (6 channels * 7 keys)
        return final_data

    
    def publish_fused_data(self):
        """
        Called by the timer, this function reads the random sensor data, fuses it 
        with the latest pose, and publishes the custom SensorData message.
        """
        # 1. Read the sensor data (random)
        sensor_values = self.read_ens160_sensors()
        
        # 2. Create and populate the custom message
        msg = SensorData()
        
        # Populate Pose Data (float64 fields from Odometry)
        msg.pose_x = self.robot_x
        msg.pose_y = self.robot_y
        msg.pose_theta = self.robot_theta
        
        # Populate Sensor Data Array (float32[42] field)
        msg.sensor_readings = [float(v) for v in sensor_values]

        # 3. Publish the message
        self.sensor_publisher.publish(msg)
        
        # 4. Log the action
        self.get_logger().info(
            f'Published RANDOM data (42 sensors) at pose (x={self.robot_x:.2f}, y={self.robot_y:.2f}, θ={self.robot_theta:.2f})'
        )
        
        # Prints eCO2, TVOC, and R3 from Channel 0 
        self.get_logger().info(
            f'Sensor 1: eCO2={sensor_values[0]:.0f} ppm | TVOC={sensor_values[1]:.0f} ppb | R3={sensor_values[6]:.0f} Ohm'
        )
        
def main(args=None):
    rclpy.init(args=args)
    
    sensor_pose_node = SensorPoseNode()
    
    try:
        rclpy.spin(sensor_pose_node)
    except KeyboardInterrupt:
        pass
    finally:
        sensor_pose_node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()