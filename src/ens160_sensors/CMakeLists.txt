cmake_minimum_required(VERSION 3.8)
project(ens160_sensors)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)


rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SensorData.msg"
  DEPENDENCIES builtin_interfaces std_msgs geometry_msgs
  PYTHON_DEPS ens160_sensors  
)

ament_export_interfaces(
  ${PROJECT_NAME}
  HAS_PREFIX_PATH
  DEPENDENCIES
  rosidl_default_generators
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()