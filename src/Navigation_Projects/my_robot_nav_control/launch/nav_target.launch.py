from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_robot_nav_control',
            executable='nav_target_exec',
            name='nav_target_node',
            output='screen'
        )
    ])