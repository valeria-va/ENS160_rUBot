from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='False'),
        DeclareLaunchArgument('robot_name', default_value='rUBot_mecanum'),
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyACM0'),
        DeclareLaunchArgument('baud_rate', default_value='57600'),
        DeclareLaunchArgument('loop_rate', default_value='30'),
        DeclareLaunchArgument('encoder_cpr', default_value='1320'),

        Node(
            package='my_robot_driver',
            executable='rubot_nano_driver_diff_exec',
            name='rubot_nano_driver_diff',
            output='screen',
            parameters=[{
                'robot_name': LaunchConfiguration('robot_name'),
                'serial_port': LaunchConfiguration('serial_port'),
                'baud_rate': LaunchConfiguration('baud_rate'),
                'loop_rate': LaunchConfiguration('loop_rate'),
                'encoder_cpr': LaunchConfiguration('encoder_cpr'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }]
        )
    ])
