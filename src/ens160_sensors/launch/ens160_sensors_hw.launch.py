from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    sensor_pose_node = Node(
        package="ens160_sensors",
        executable="ens160_sensors_hw_exec",
        name="sensor_pose_node_real",
      
        parameters=[
          
        {"serial_port": "/dev/ttyUSB1"},
        {"baud_rate": 9600},
        {"timer_period": 0.5} # Placeholder, publishes fused data at 2 Hz 
          
        ]
      
    )

    my_robot_control_node = Node(
        package="my_robot_control",
        executable="my_robot_control_exec",
        name="robot_control",
        parameters=[
            {"vx": 0.3},
            {"vy": 0.0},
            {"w": 0.0},
            {"td": 2.0}
        ]
    )

    ld.add_action(my_robot_control_node)
    ld.add_action(sensor_pose_node)
    
    return ld
