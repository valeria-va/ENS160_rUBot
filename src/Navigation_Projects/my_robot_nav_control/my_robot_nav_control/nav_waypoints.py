#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
import tf_transformations
import ast  # Import the ast module

class NavigationTask(Node):
    def __init__(self):
        super().__init__('nav_waypoints_node')
        self.navigator = BasicNavigator()

        # Declare the 'waypoints' parameter.  Important to declare parameters!
        self.declare_parameter('waypoints',
                             '[(2.0, -2.0, 1.57), (4.0, 0.8, 0.0), (8.0, 1.0, -1.57), (8.0, -0.5, 1.57), (5.0, 5.0, 3.14), (3.0, 4.0, 1.57), (4.0, 5.0, 0.0), (5.0, 3.0, -1.57), (4.0, 0.8, 3.14), (-4.0, 3.5, -1.57), (-4.0, 0.0, 1.57)]')  # Default value as a string

    def create_pose_stamped(self, position_x, position_y, orientation_z):
        q_x, q_y, q_z, q_w = tf_transformations.quaternion_from_euler(0.0, 0.0, orientation_z)
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = position_x
        pose.pose.position.y = position_y
        pose.pose.position.z = 0.0
        pose.pose.orientation.x = q_x
        pose.pose.orientation.y = q_y
        pose.pose.orientation.z = q_z
        pose.pose.orientation.w = q_w
        return pose

    def set_initial_pose(self, x, y, z_rotation):
        initial_pose = self.create_pose_stamped(x, y, z_rotation)
        self.navigator.setInitialPose(initial_pose)
        self.get_logger().info(f'Setted initial pose to: x={x}, y={y}, z_rotation={z_rotation}')

    def wait_for_nav2(self):
        self.navigator.waitUntilNav2Active()
        self.get_logger().info('Nav2 is active and ready for navigation.')

    def go_to_pose(self, x, y, z_rotation):
        goal_pose = self.create_pose_stamped(x, y, z_rotation)
        self.navigator.goToPose(goal_pose)
        self.get_logger().info(f'Going to pose: x={x}, y={y}, z_rotation={z_rotation}')
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            # self.get_logger().info(f'Feedback: {feedback}') # Uncomment for more detailed feedback
        result = self.navigator.getResult()
        self.get_logger().info(f'Navigation finished with result: {result}')
        return result

    def follow_waypoints(self, waypoints_list):
        waypoints = [self.create_pose_stamped(x, y, z) for x, y, z in waypoints_list]
        self.navigator.followWaypoints(waypoints)
        self.get_logger().info('Following waypoints.')
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            # self.get_logger().info(f'Feedback: {feedback}') # Uncomment for more detailed feedback
        result = self.navigator.getResult()
        self.get_logger().info(f'Waypoint following finished with result: {result}')
        return result

def main(args=None):
    rclpy.init(args=args)
    navigation_node = NavigationTask()

    # --- Set initial pose ---
    navigation_node.set_initial_pose(0.0, 0.0, 0.0)

    # --- Wait for Nav2 ---
    navigation_node.wait_for_nav2()

    # --- Get waypoints from parameter ---
    waypoints_string = navigation_node.get_parameter('waypoints').get_parameter_value().string_value
    navigation_node.get_logger().info(f'Received waypoints: {waypoints_string}')

    try:
        waypoints = ast.literal_eval(waypoints_string)  # Safely convert string to list of tuples
        if not isinstance(waypoints, list):
            raise ValueError("Waypoints parameter must be a list.")
        for waypoint in waypoints:
            if not isinstance(waypoint, tuple) or len(waypoint) != 3:
                raise ValueError("Each waypoint must be a tuple of (x, y, yaw).")
    except (ValueError, SyntaxError) as e:
        navigation_node.get_logger().error(f'Error parsing waypoints: {e}')
        #  Consider a more robust error handling strategy.  For example:
        #  rclpy.shutdown()
        #  return
        waypoints = [(1.5, 1.5, 1.57), (1.5, -0.7, 0.0), (2.7, 0.0, 1.57)] # Default.

    # --- Follow waypoints ---
    navigation_node.follow_waypoints(waypoints)

    print(navigation_node.navigator.getResult())

    # --- Shutdown ---
    navigation_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
