from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    # --- 1. ARGUMENTS ---
    timer_period_arg = DeclareLaunchArgument(
        'timer_period',
        default_value='1.0',
        description='Sensor node timer period in seconds'
    )

    # --- 2. ROBOT DESCRIPTION (URDF) ---
    bringup_package_name = 'my_robot_description'
    bringup_pkg_dir = get_package_share_directory(bringup_package_name)
    robot_urdf_path = os.path.join(bringup_pkg_dir, 'urdf','rubot', 'hw_rubot_mecanum.urdf')

    # --- 3. SENSOR NODE ---
    sensor_pose_node = Node(
        package="ens160_sensors",
        executable="ens160_sensors_hw_exec",  
        name="sensor_pose_node_real",
        output='screen',
        parameters=[
            {'timer_period': timer_period_arg.default_value},
            {'use_sim_time': False},  # real robot does NOT use simulation time
            {'serial_port': ''},
            {'baud_rate': 9600},
        ]
    )

    # --- 4. ROBOT STATE / DESCRIPTION NODE ---
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': open(robot_urdf_path).read()}]
    )

    # --- 5. RETURN LAUNCH DESCRIPTION ---
    return LaunchDescription([
        timer_period_arg,
        sensor_pose_node,
        robot_state_publisher_node
    ])
