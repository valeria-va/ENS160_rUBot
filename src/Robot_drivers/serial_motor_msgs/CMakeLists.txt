cmake_minimum_required(VERSION 3.8)
project(serial_motor_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find required packages
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)  # if your messages use it

# Message files
set(msg_files
  "msg/MotorVels.msg"
  "msg/MotorCommands.msg"
  "msg/EncoderVals.msg"
  "msg/MecanumMotorVels.msg"
  "msg/MecanumEncoderVals.msg"
)

# Generate messages
rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  DEPENDENCIES std_msgs
)

# Export dependencies
ament_export_dependencies(rosidl_default_runtime)

# Package export
ament_package()

