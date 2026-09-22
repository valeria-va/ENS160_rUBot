
#   python3 /home/valeria/Desktop/ROS2_rUBot_mecanum_ws/src/my_robot_co2map/scripts/live_plotter.py

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from ens160_interfaces.msg import SensorData
import matplotlib.pyplot as plt
import time
from collections import defaultdict, deque

MAX_SECONDS = 1800   # rolling window (5 minutes)
NUM_CHANNELS = 6    # adjust if needed

class CO2LivePlot(Node):
    def __init__(self):
        super().__init__('co2_live_plot')

        self.start_time = time.time()

        self.time_buf = defaultdict(lambda: deque())
        self.val_buf = defaultdict(lambda: deque())

        self.create_subscription(
            SensorData,
            'ens160_data',
            self.cb,
            10
        )

        # --- matplotlib setup ---
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        self.lines = {}

        for ch in range(NUM_CHANNELS):
            line, = self.ax.plot([], [], label=f'CH{ch}')
            self.lines[ch] = line

        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("eCO₂ (ppm)")
        self.ax.set_title("Live ENS160 eCO₂")
        self.ax.legend(loc='upper left')
        self.ax.grid(True)

        self.timer = self.create_timer(0.2, self.update_plot)

    def cb(self, msg: SensorData):
        now = time.time() - self.start_time

        for ch, val in zip(msg.channels, msg.sensor_readings):
            self.time_buf[ch].append(now)
            self.val_buf[ch].append(val)

            while self.time_buf[ch] and self.time_buf[ch][0] < now - MAX_SECONDS:
                self.time_buf[ch].popleft()
                self.val_buf[ch].popleft()

    def update_plot(self):
        for ch, line in self.lines.items():
            if ch in self.time_buf:
                line.set_data(self.time_buf[ch], self.val_buf[ch])

        self.ax.relim()
        self.ax.autoscale_view()
        plt.pause(0.001)

def main(args=None):
    rclpy.init(args=args)
    node = CO2LivePlot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
