#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import numpy as np 

class WallFollowerHolonomic(Node): 

    def __init__(self):
        super().__init__('wall_follower_holonomic_node')
        
        # --- Parameter Declarations ---
        self.declare_parameter('distance_laser', 0.5)     # Wall distance (d)
        self.declare_parameter('forward_speed', 0.3)      # Speed for linear.x
        self.declare_parameter('rotation_speed', 0.3)
        self.declare_parameter('time_to_stop', 10.0)     

        self.declare_parameter("max_strafe_speed", 0.5)   # Max speed for linear.y
        self.declare_parameter("strafe_factor", 1.5)      # Proportional Gain (Kp)
        
        self.d = self.get_parameter('distance_laser').value
        self.vx = self.get_parameter('forward_speed').value # Base forward speed
        self.vy_max = self.get_parameter("max_strafe_speed").value 
        self.kp_strafe = self.get_parameter("strafe_factor").value
        self.wz = self.get_parameter('rotation_speed').value
        self.time_to_stop = self.get_parameter('time_to_stop').value

        self.is_scan_ranges_length_correction_factor_calculated = False
        self.scan_ranges_length_correction_factor = 2

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(LaserScan, '/scan', self.clbk_laser, 10)
        
        self.regions = None

        self.timer_period = 0.04  # seconds
        self.timer = self.create_timer(self.timer_period, self.take_action)

        self.start_time = self.get_clock().now().seconds_nanoseconds()[0]
        self._shutting_down = False 

        self.get_logger().info("Holonomic Wall Follower Node Initialized")
        
    def clbk_laser(self, msg):
        if self._shutting_down: 
            return
        
        if not self.is_scan_ranges_length_correction_factor_calculated:
            self.scan_ranges_length_correction_factor = len(msg.ranges) / 360
            self.is_scan_ranges_length_correction_factor_calculated = True

        bright_min = int(30 * self.scan_ranges_length_correction_factor)
        bright_max = int(90 * self.scan_ranges_length_correction_factor)
        right_min = int(90 * self.scan_ranges_length_correction_factor)
        right_max = int(120 * self.scan_ranges_length_correction_factor)
        fright_min = int(120 * self.scan_ranges_length_correction_factor)
        fright_max = int(170 * self.scan_ranges_length_correction_factor)
        front_min = int(175 * self.scan_ranges_length_correction_factor)
        front_max = int(185 * self.scan_ranges_length_correction_factor)
        left_min = int(190 * self.scan_ranges_length_correction_factor)
        left_max = int(240 * self.scan_ranges_length_correction_factor)

        self.regions = {
            'bright': min(min(msg.ranges[bright_min:bright_max]), 3),
            'right': min(min(msg.ranges[right_min:right_max]), 3),
            'fright': min(min(msg.ranges[fright_min:fright_max]), 3),
            'front': min(min(msg.ranges[front_min:front_max]), 3),
            'left': min(min(msg.ranges[left_min:left_max]), 3),
        }

    def calculate_strafe_speed(self, current_distance):
        """Calculates strafe speed (linear.y) using P-control (Kp=strafe_factor)"""
        # Error: Positive = too far, Negative = too close.
        # We want positive linear.y (strafe left) if too close (negative error).
        error = self.d - current_distance 
        
        linear_y = self.kp_strafe * error
        
        # Clamp linear_y to the maximum strafe speed
        return np.clip(linear_y, -self.vy_max, self.vy_max)


    def take_action(self):
        if self._shutting_down: 
            return
        elapsed_time = self.get_clock().now().seconds_nanoseconds()[0] - self.start_time

        if self.regions is None:
            return

        msg = Twist()
        linear_x = 0.0 
        linear_y = 0.0 # Use linear_y for strafing
        angular_z = 0.0

        state_description = ''
        
        right_dist = self.regions['right']
        fright_dist = self.regions['fright']
        front_dist = self.regions['front']
        left_dist = self.regions['left']

        # --- HOLONOMIC MOVEMENT LOGIC ---

        if left_dist < self.d * 1:
            state_description = 'Case 0 - Pinned Left: Escape Right'
            linear_x = 0.0          
            linear_y = -self.vy_max # Force maximum strafe RIGHT (negative Y)
            angular_z = 0.0 
            
        if front_dist < self.d * 1.5 or fright_dist < self.d:
            # Case 1: Obstacle Directly Ahead - Stop Forward, Strafe Left
            state_description = 'Case 1 - Front Obstacle: Strafe Left'
            linear_x = 0.0         
            linear_y = self.vy_max # Strafe left (positive Y)
            angular_z = self.wz / 2.0 # Slight left rotation

        elif right_dist < 3.0 * self.d: 
            # Case 2: Wall in Range  (right side)
            state_description = 'Case 2 - Wall Following'
            
            # Forward motion (keep moving along the wall)
            linear_x = self.vx
            
            # Strafe motion
            linear_y = self.calculate_strafe_speed(right_dist)
            
            # Rotation: Minimal, only for alignment
            angular_z = 0.1 

        else:
            # Case 3: Searching for Wall - Move Forward and Turn Right
            state_description = 'Case 3 - Searching/Corner: Turn Right'
            linear_x = self.vx / 2.0 
            linear_y = -self.vy_max / 2.0 # Strafe right slightly to close distance
            angular_z = -self.wz 


        self.get_logger().info(f"{state_description} -> (vx:{linear_x:.2f}, vy:{linear_y:.2f}, wz:{angular_z:.2f})")
        msg.linear.x = linear_x # Publish forward speed
        msg.linear.y = linear_y # Publish strafe speed (HOLONOMIC)
        msg.angular.z = angular_z
        self.publisher.publish(msg)

        if elapsed_time >= self.time_to_stop:
            self.stop()
            self.timer.cancel()
            self.get_logger().info(f"Robot stopped")
            rclpy.try_shutdown()

    def stop(self):
        self._shutting_down = True
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.linear.y = 0.0
        stop_msg.angular.z = 0.0
        self.publisher.publish(stop_msg)
        rclpy.spin_once(self, timeout_sec=0.1)

def main(args=None):
    rclpy.init(args=args)
    wall_follower = WallFollowerHolonomic()

    try:
        rclpy.spin(wall_follower)
    except KeyboardInterrupt:
        pass
    finally:
        wall_follower.destroy_node()

if __name__ == '__main__':
    main()