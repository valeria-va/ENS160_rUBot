#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from ens160_interfaces.msg import SensorData
import transforms3d.euler as t3d_euler
import serial

class SensorPoseNode(Node):
    def __init__(self):
        super().__init__('sensor_pose_node_hw')

        # Robot pose
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_theta = 0.0

        # Publisher for custom message
        self.publisher_ = self.create_publisher(SensorData, 'ens160_data', 10)

        # Subscribe to odometry
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        # Open serial port
        serial_port_name = '/dev/ttyACM1'
        serial_baud = 9600
        try:
            self.ser = serial.Serial(serial_port_name, serial_baud, timeout=1)
            self.get_logger().info(f'Connected to sensor on {serial_port_name} at {serial_baud} baud')
        except Exception as e:
            self.get_logger().error(f'Cannot open serial port {serial_port_name}: {e}')
            raise

        # Timer to read sensor periodically
        self.create_timer(0.1, self.read_sensor)  # 10 Hz

    def odom_callback(self, msg: Odometry):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        quat_array = [q.w, q.x, q.y, q.z]
        try:
            _, _, yaw = t3d_euler.quat2euler(quat_array, axes='rzyx')
            self.robot_theta = yaw
        except Exception:
            self.robot_theta = 0.0

    def read_sensor(self):
        if self.ser.in_waiting:
            line = self.ser.readline()
            if line:
                decoded = line.decode('utf-8', errors='ignore').strip()
                parts = decoded.split(',')
                if len(parts) >= 9:
                    try:
                        msg = SensorData()
                        msg.pose_x = self.robot_x
                        msg.pose_y = self.robot_y
                        msg.pose_theta = self.robot_theta
                        msg.channels = [int(parts[1][2:])]  # e.g., "CH1" -> 1
                        msg.sensor_readings = [float(p.split('=')[1]) for p in parts[2:]]
                        self.publisher_.publish(msg)
                        self.get_logger().info(f'Published CH{msg.channels[0]}: {msg.sensor_readings}')
                    except Exception as e:
                        self.get_logger().error(f'Error parsing line: {decoded} | {e}')

def main(args=None):
    rclpy.init(args=args)
    node = SensorPoseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.ser.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
