#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from ens160_interfaces.msg import SensorData
from sensor_msgs.msg import PointCloud2, PointField
import sensor_msgs_py.point_cloud2 as pc2
from geometry_msgs.msg import PointStamped
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException
from rclpy.time import Time
from std_msgs.msg import Header
from tf2_geometry_msgs import do_transform_point


class ECO2CloudNode(Node):
    def __init__(self):
        super().__init__('eco2_cloud')

        # TF buffer and listener
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Subscriber to the sensor data
        self.sub = self.create_subscription(
            SensorData,
            '/ens160_data',
            self.cb,
            10
        )

        # Publisher for the PointCloud2
        self.pub = self.create_publisher(PointCloud2, '/eco2_cloud', 10)

        # Store all past points to leave an unlimited trail
        self.points = []

        # Intensity mapping range
        self.intensity_min = 400.0
        self.intensity_max = 1500.0

        self.get_logger().info("ECO2CloudNode initialized with intensity range "
                               f"{self.intensity_min}-{self.intensity_max}")

    def cb(self, msg: SensorData):
        # Raw CO2 value from sensor
        eco2_raw = float(msg.sensor_readings[0])

        # Clip and normalize intensity to 0.0-1.0
        intensity = max(min(eco2_raw, self.intensity_max), self.intensity_min)
        intensity = (intensity - self.intensity_min) / (self.intensity_max - self.intensity_min)

        # Transform the point from 'base_link' (sensor frame) to 'map'
        point_in_sensor_frame = PointStamped()
        point_in_sensor_frame.header.stamp = self.get_clock().now().to_msg()
        point_in_sensor_frame.header.frame_id = 'base_link'
        point_in_sensor_frame.point.x = 0.0  # Sensor offset relative to base_link
        point_in_sensor_frame.point.y = 0.0
        point_in_sensor_frame.point.z = 0.0

        try:
            transform = self.tf_buffer.lookup_transform(
                'map', 'base_link', Time())
            point_in_map = do_transform_point(point_in_sensor_frame, transform)

            # Append the point with normalized intensity
            self.points.append((
                point_in_map.point.x,
                point_in_map.point.y,
                point_in_map.point.z,
                intensity
            ))

        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(f'TF lookup failed: {e}')
            return

        # Create PointCloud2 header
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'map'

        # Define fields for the PointCloud2
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1),
        ]

        # Create the PointCloud2 message
        cloud_msg = pc2.create_cloud(header, fields, self.points)

        # Publish the growing trail
        self.pub.publish(cloud_msg)


def main():
    rclpy.init()
    node = ECO2CloudNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
