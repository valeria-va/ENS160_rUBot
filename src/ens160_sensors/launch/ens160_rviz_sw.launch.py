from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import AnyLaunchDescriptionSource # Needed to include XML
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    
    # --- 1. ARGUMENTS  ---
    timer_period_arg = DeclareLaunchArgument(
        'timer_period', 
        default_value='1.0', 
        description='Sensor node timer period in seconds'
    )
    
    # --- 2. LOCATE AND INCLUDE GAZEBO BRINGUP (from the install folder) AND SLAM (from Navigation_Project) ---
    
    # Define the package that holds the bringup file
    bringup_package_name = 'my_robot_bringup' 

    # Define the package that holds the slam file
    slam_package_name = 'my_robot_cartographer'
    
    # Get the installed share directory path
    bringup_pkg_dir = get_package_share_directory(bringup_package_name)
    slam_pkg_dir = get_package_share_directory(slam_package_name)

    # Construct the full path to the XML launch file
    full_bringup_launch_path = os.path.join(
        bringup_pkg_dir, 
        'launch', 
        'my_robot_bringup_sw.launch.xml'
    )

    full_slam_launch_path = os.path.join(
        slam_pkg_dir, 
        'launch', 
        'cartographer.launch.py'
    )
    
    # Include the XML launch file
    full_bringup_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(full_bringup_launch_path),
        
        launch_arguments={
            'use_sim_time': 'true',
            'x0': '0.0',
            'y0': '0.0',
            'yaw0': '0.0',
            'robot': 'rubot/rubot_mecanum.urdf',
            'custom_world': 'square3m_walls.world',
        }.items()
    )

    full_slam_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(full_slam_launch_path),
        
        launch_arguments={
            'use_sim_time': 'true',
            'x0': '0.0',
            'y0': '0.0',
            'yaw0': '0.0',
            'robot': 'rubot/rubot_mecanum.urdf',
            'custom_world': 'square3m_walls.world',
        }.items()
    )

    # --- 3. LAUNCH THE ENS160 SENSOR NODE ---
    sensor_pose_node = Node(
        package="ens160_sensors",
        executable="ens160_sensors_sw_exec",
        name="sensor_pose_node_sw",
        output='screen',
        parameters=[
            {'timer_period': timer_period_arg.default_value},
            # CRITICAL: Always use sim time when running with Gazebo
            {'use_sim_time': True}, 
        ]
    )

    # --- 4. RETURN THE LAUNCH DESCRIPTION ---
    return LaunchDescription([
        timer_period_arg,
        
        full_bringup_launch,
        full_slam_launch,
        sensor_pose_node
    ])