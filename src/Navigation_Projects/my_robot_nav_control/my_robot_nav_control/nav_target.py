#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
import tf_transformations

class NavTarget(Node):
    def __init__(self):
        super().__init__('nav_target_node')
        self.navigator = BasicNavigator()

    def create_pose_stamped(self, position_x, position_y, rotation_z):
        q_x, q_y, q_z, q_w = tf_transformations.quaternion_from_euler(0.0, 0.0, rotation_z)
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.pose.position.x = position_x
        goal_pose.pose.position.y = position_y
        goal_pose.pose.position.z = 0.0
        goal_pose.pose.orientation.x = q_x
        goal_pose.pose.orientation.y = q_y
        goal_pose.pose.orientation.z = q_z
        goal_pose.pose.orientation.w = q_w
        return goal_pose

    def go_to_pose(self, pose):
        self.navigator.goToPose(pose)
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            self.get_logger().info(f'Current pose: {feedback}') # Use ROS logger
        result = self.navigator.getResult()
        self.get_logger().info(f'Navigation result: {result}') # Use ROS logger

    def follow_waypoints(self, waypoints):
        self.navigator.followWaypoints(waypoints)
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            self.get_logger().info(f'Current pose: {feedback}') # Use ROS logger
        result = self.navigator.getResult()
        self.get_logger().info(f'Waypoint following result: {result}') # Use ROS logger

def main(args=None):
    rclpy.init(args=args)
    nav_target_node = NavTarget()

    # --- Set initial pose ---
    # !!! Comment if the initial pose is already set !!!
    initial_pose = nav_target_node.create_pose_stamped(0.0, 0.0, 0.0)
    #nav_target_node.navigator.setInitialPose(initial_pose)

    # --- Wait for Nav2 ---
    nav_target_node.navigator.waitUntilNav2Active()

    # --- Create some Nav2 goal poses ---
    goal_pose1 = nav_target_node.create_pose_stamped(1.5, 1.5, 0.0)
    #goal_pose2 = nav_target_node.create_pose_stamped(2.0, 2.5, 3.14)
    #goal_pose3 = nav_target_node.create_pose_stamped(0.5, 1.0, 0.0)

    # --- Going to one pose ---
    nav_target_node.go_to_pose(goal_pose1)

    # --- Follow Waypoints ---
    # waypoints = [goal_pose1, goal_pose2, goal_pose3]
    # nav_target_node.follow_waypoints(waypoints)

    # --- Shutdown ROS2 communications ---
    nav_target_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()