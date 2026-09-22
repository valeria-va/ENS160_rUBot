#!/usr/bin/env python3

import time
import math
import rclpy
import serial
from threading import Lock
from rclpy.node import Node
from typing import List, Optional

# Imports de missatges de ROS2
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped
from sensor_msgs.msg import JointState
from serial_motor_msgs.msg import MecanumMotorVels, MecanumEncoderVals
from std_msgs.msg import Bool

# Imports per a la gestió de nodes i TFs
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from tf2_ros import TransformBroadcaster


class MecanumMotorDriver(Node):
    """Node de ROS2 per controlar i monitoritzar un robot amb tracció Mecanum."""

    def __init__(self, args) -> None:
        """Inicialitza el node amb comunicació serial, paràmetres i publicadors/subscriptors."""
        super().__init__("rubot_nano_driver_mecanum")

        self._logger = self.get_logger()

        # --- Paràmetres ---
        # Gestió robusta de 'use_sim_time' per evitar errors de doble declaració.
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', False)
        self.use_sim_time = self.get_parameter("use_sim_time").get_parameter_value().bool_value
        
        if self.use_sim_time:
            self.get_logger().info("Utilitzant temps de simulació.")

        # Declaració de la resta de paràmetres amb valors per defecte.
        self.declare_parameter("encoder_cpr", 1320) #1320
        self.encoder_cpr = self.get_parameter("encoder_cpr").value
        
        self.declare_parameter("loop_rate", 30)
        self.loop_rate = self.get_parameter("loop_rate").value
        
        self.declare_parameter("serial_port", "/dev/ttyACM0")
        self.serial_port: str = self.get_parameter("serial_port").value
        
        self.declare_parameter("baud_rate", 57600)
        self.baud_rate: int = self.get_parameter("baud_rate").value

        self.declare_parameter("serial_debug", False)
        self.debug_serial_cmds: bool = self.get_parameter("serial_debug").value

        self.declare_parameter("wheel_diameter", 0.080)
        self.wheel_diameter = self.get_parameter("wheel_diameter").value
        self.wheel_radius = self.wheel_diameter / 2

        self.declare_parameter("robot_length", 0.22)
        self.robot_length = self.get_parameter("robot_length").value

        self.declare_parameter("robot_width", 0.165)
        self.robot_width = self.get_parameter("robot_width").value

        self.L_diag_factor = (self.robot_width / 2) + (self.robot_length / 2)
        if self.L_diag_factor == 0:
            self._logger.error("Els paràmetres de longitud/amplada del robot no poden ser zero!")
            raise ValueError("Paràmetres cinemàtics incorrectes.")

        # --- Publicadors, Subscriptors i Callbacks ---
        self.callback_group = ReentrantCallbackGroup()
        self._sub_cmd_vel = self.create_subscription(Twist, "cmd_vel", self.cmd_vel_callback, 10, callback_group=self.callback_group)
        self.odom_pub_ = self.create_publisher(Odometry, "odom", 10)
        self.tf_broadcaster_ = TransformBroadcaster(self)
        self.joint_states_pub_ = self.create_publisher(JointState, 'joint_states', 10)
        
        # Publicadors opcionals per a depuració
        self.motor_vels_pub_ = self.create_publisher(MecanumMotorVels, "motor_vels", 10)
        self.encoder_pub_ = self.create_publisher(MecanumEncoderVals, "encoder_vals", 10)

        #Subscriber
        self._sub_reset_odom = self.create_subscription(Bool, "reset_odom", self.reset_odom_callback, 10, callback_group=self.callback_group)
        
        # Bucle principal del node
        self.create_timer(1.0 / self.loop_rate, self._timer_callback, callback_group=self.callback_group)
        
        # --- Inicialització de variables ---
        self.last_enc_read_time = self.get_clock().now()
        self.last_fl_enc, self.last_fr_enc, self.last_bl_enc, self.last_br_enc = 0, 0, 0, 0
        self.m_fl_spd, self.m_fr_spd, self.m_bl_spd, self.m_br_spd = 0.0, 0.0, 0.0, 0.0
        self.mutex = Lock()
        self.x, self.y, self.theta = 0.0, 0.0, 0.0
        self.last_time = self.get_clock().now()

        # --- Connexió Serial ---
        try:
            self._logger.info(f"Connectant al port {self.serial_port} a {self.baud_rate}.")
            self.conn = serial.Serial(self.serial_port, self.baud_rate, timeout=1.0)
            self._logger.info(f"Connectat a {self.conn.name}")
        except serial.SerialException as e:
            self._logger.error(f"No s'ha pogut connectar a {self.serial_port}: {e}")
            raise

    def _timer_callback(self) -> None:
        """Callback del temporitzador per llegir encoders i publicar dades."""
        self.check_encoders()
        self.publish_odometry()

    def cmd_vel_callback(self, msg: Twist) -> None:
        """Converteix comandes de velocitat a velocitats de roda i les envia."""
        vx, vy, omega_z = msg.linear.x, msg.linear.y, msg.angular.z
        
        if self.wheel_radius == 0 or self.L_diag_factor == 0:
            return

        fl_rad_s = (vx - vy - self.L_diag_factor * omega_z) / self.wheel_radius
        fr_rad_s = (vx + vy + self.L_diag_factor * omega_z) / self.wheel_radius
        bl_rad_s = (vx + vy - self.L_diag_factor * omega_z) / self.wheel_radius
        br_rad_s = (vx - vy + self.L_diag_factor * omega_z) / self.wheel_radius

        scaler = (self.encoder_cpr / (2 * math.pi)) / self.loop_rate
        fl_ct = fl_rad_s * scaler
        fr_ct = fr_rad_s * scaler
        bl_ct = bl_rad_s * scaler
        br_ct = br_rad_s * scaler

        if all(math.isfinite(c) for c in [fl_ct, fr_ct, bl_ct, br_ct]):
            self.send_feedback_motor_command(fl_ct, fr_ct, bl_ct, br_ct)

    def check_encoders(self) -> None:
        """Llegeix els encoders, calcula velocitats i publica /joint_states."""
        resp = self.send_encoder_read_command()
        if resp:
            current_time = self.get_clock().now()
            dt = (current_time - self.last_enc_read_time).nanoseconds / 1e9
            self.last_enc_read_time = current_time
            if dt == 0: return

            fl_diff, fr_diff, bl_diff, br_diff = resp[0] - self.last_fl_enc, resp[1] - self.last_fr_enc, resp[2] - self.last_bl_enc, resp[3] - self.last_br_enc
            self.last_fl_enc, self.last_fr_enc, self.last_bl_enc, self.last_br_enc = resp[0], resp[1], resp[2], resp[3]

            rads_per_ct = 2 * math.pi / self.encoder_cpr
            self.m_fl_spd = fl_diff * rads_per_ct / dt
            self.m_fr_spd = fr_diff * rads_per_ct / dt
            self.m_bl_spd = bl_diff * rads_per_ct / dt
            self.m_br_spd = br_diff * rads_per_ct / dt
            
            # Publica l'estat de les articulacions
            self.publish_joint_states()

    def publish_joint_states(self) -> None:
        """Publica l'estat actual de les articulacions de les rodes."""
        js_msg = JointState()
        js_msg.header.stamp = self.get_clock().now().to_msg()
        # AQUESTS NOMS HAN DE COINCIDIR AMB ELS DEL TEU FITXER URDF
        js_msg.name = [
            'upper_left_wheel_joint', 'upper_right_wheel_joint',
            'lower_left_wheel_joint', 'lower_right_wheel_joint'
        ]
        
        rads_per_ct = 2 * math.pi / self.encoder_cpr
        js_msg.position = [
            self.last_fl_enc * rads_per_ct,
            self.last_fr_enc * rads_per_ct,
            self.last_bl_enc * rads_per_ct,
            self.last_br_enc * rads_per_ct
        ]
        js_msg.velocity = [self.m_fl_spd, self.m_fr_spd, self.m_bl_spd, self.m_br_spd]
        self.joint_states_pub_.publish(js_msg)

    def publish_odometry(self) -> None:
        """Calcula i publica l'odometria i la transformada TF corresponent."""
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time
        if dt == 0: return

        # Cinemàtica directa per calcular la velocitat del robot
        vx = (self.m_fl_spd + self.m_fr_spd + self.m_bl_spd + self.m_br_spd) * self.wheel_radius / 4.0
        vy = (-self.m_fl_spd + self.m_fr_spd + self.m_bl_spd - self.m_br_spd) * self.wheel_radius / 4.0
        vth = (-self.m_fl_spd + self.m_fr_spd - self.m_bl_spd + self.m_br_spd) * self.wheel_radius / (4.0 * self.L_diag_factor)
        
        # Integració de la posició
        delta_x = (vx * math.cos(self.theta) - vy * math.sin(self.theta)) * dt
        delta_y = (vx * math.sin(self.theta) + vy * math.cos(self.theta)) * dt
        delta_th = vth * dt
        self.x += delta_x
        self.y += delta_y
        self.theta += delta_th
        
        quat = self.euler_to_quaternion(0, 0, self.theta)
        
        # Publicació de la transformada odom -> base_footprint
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_footprint"
        t.transform.translation.x, t.transform.translation.y = self.x, self.y
        t.transform.rotation.x, t.transform.rotation.y, t.transform.rotation.z, t.transform.rotation.w = quat
        self.tf_broadcaster_.sendTransform(t)

        # Publicació del missatge d'odometria
        odom_msg = Odometry()
        odom_msg.header.stamp = t.header.stamp
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_footprint"
        odom_msg.pose.pose.position.x, odom_msg.pose.pose.position.y = self.x, self.y
        odom_msg.pose.pose.orientation.x, odom_msg.pose.pose.orientation.y, odom_msg.pose.pose.orientation.z, odom_msg.pose.pose.orientation.w = quat
        odom_msg.twist.twist.linear.x, odom_msg.twist.twist.linear.y = vx, vy
        odom_msg.twist.twist.angular.z = vth
        self.odom_pub_.publish(odom_msg)

    def reset_odom_callback(self, msg: Bool) -> None:
        """Reinicia els encoders i l'odometria si rep True pel topic /reset_odom."""

        if msg.data:
            self._logger.info("Reiniciant odometria i encoders.")
            self.send_command("r")
            self.x, self.y, self.theta = 0.0, 0.0, 0.0
            self.last_fl_enc = self.last_fr_enc = self.last_bl_enc = self.last_br_enc = 0

    def euler_to_quaternion(self, roll: float, pitch: float, yaw: float) -> tuple:
        cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
        cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
        cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
        return (
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy
        )

    def send_command(self, cmd_string: str) -> Optional[str]:
        with self.mutex:
            try:
                self.conn.write((cmd_string + "\r").encode("utf-8"))
                response = self.conn.readline().decode("utf-8").strip()
                return response
            except Exception as e:
                self._logger.error(f"Error a send_command: {e}")
                return None
    
    def send_feedback_motor_command(self, fl, fr, bl, br) -> None:
        self.send_command(f"m {int(fl)} {int(fr)} {int(bl)} {int(br)}")
        
    def send_encoder_read_command(self) -> Optional[List[int]]:
        resp = self.send_command("e")
        if resp:
            try:
                return [int(val) for val in resp.split()]
            except (ValueError, IndexError):
                self._logger.warning(f"No s'ha pogut analitzar la resposta de l'encoder: '{resp}'")
        return None
        
    def close_conn(self) -> None:
        if hasattr(self, 'conn') and self.conn.is_open:
            self.conn.close()
            self._logger.info("Connexió serial tancada.")

def main(args: Optional[List[str]] = None) -> None:
    rclpy.init(args=args)
    motor_driver = None
    try:
        motor_driver = MecanumMotorDriver(args)
        executor = MultiThreadedExecutor(num_threads=2)
        executor.add_node(motor_driver)
        try:
            executor.spin()
        finally:
            executor.shutdown()
            if motor_driver: motor_driver.destroy_node()
    except (ValueError, serial.SerialException, KeyboardInterrupt):
        if motor_driver: motor_driver.get_logger().info("Node finalitzant.")
    finally:
        if motor_driver: motor_driver.close_conn()
        rclpy.shutdown()

if __name__ == "__main__":
    main()