import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
import re
from PIL import Image, ImageTk
import os
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import csv
from pathlib import Path


class PlottingApp:
    def __init__(self, master, sensor_data_queue, hotplate_data_queue, channel_states, num_channels, tca_channels):
        self.master = master
        self.master.title("ENS160 Sensor Readings Graphs")
        self.master.geometry("1100x600")

        self.sensor_data_queue = sensor_data_queue
        self.hotplate_data_queue = hotplate_data_queue
        self.channel_states = channel_states
        self.num_channels = num_channels
        self.tca_channels = tca_channels # Store the channel map

        self.max_data_points = 180

        self.plot_data = {
            i: {'time': deque(maxlen=self.max_data_points),
                'eco2': deque(maxlen=self.max_data_points),
                'tvoc': deque(maxlen=self.max_data_points)}
            for i in range(self.num_channels)
        }

        self.hotplate_r3_plot_data = {
            i: {'time': deque(maxlen=self.max_data_points),
                'R3': deque(maxlen=self.max_data_points)}
            for i in range(self.num_channels)
        }

        self.start_time = time.time()
        self.create_plot_widgets()
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=1000, cache_frame_data=False)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_plot_widgets(self):
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, sharex=True, figsize=(10, 8))
        self.ax1.set_ylabel("eCO2 (ppm)")
        self.ax1.set_title("eCO2 Concentration")
        self.ax1.grid(True)
        self.lines_eco2 = {}

        self.ax2.set_ylabel("TVOC (ppb)")
        self.ax2.set_title("TVOC Concentration")
        self.ax2.grid(True)
        self.lines_tvoc = {}

        self.ax3.set_xlabel("Time (seconds)")
        self.ax3.set_ylabel("R3 Resistance")
        self.ax3.set_title("Hotplate R3 Resistance per Channel")
        self.ax3.grid(True)
        self.lines_hotplate_r3 = {}

        # Use tca_channels for the graph labels
        for i in range(self.num_channels):
            physical_channel = self.tca_channels[i]
            self.lines_eco2[i], = self.ax1.plot([], [], label=f'CH{physical_channel} eCO2')
            self.lines_tvoc[i], = self.ax2.plot([], [], label=f'CH{physical_channel} TVOC')
            self.lines_hotplate_r3[i], = self.ax3.plot([], [], label=f'CH{physical_channel} R3')

        self.ax1.legend(loc='upper left', bbox_to_anchor=(1,1))
        self.ax2.legend(loc='upper left', bbox_to_anchor=(1,1))
        self.ax3.legend(loc='upper left', bbox_to_anchor=(1,1))
        self.fig.tight_layout(rect=[0, 0, 0.97, 1])

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()

    def update_plot(self, frame):
        while self.sensor_data_queue:
            data_point = self.sensor_data_queue.popleft()
            logical_channel = data_point['channel'] # This is the index 0-5

            self.plot_data[logical_channel]['time'].append(data_point['timestamp_app'] - self.start_time)
            self.plot_data[logical_channel]['eco2'].append(data_point['eCO2'])
            self.plot_data[logical_channel]['tvoc'].append(data_point['TVOC'])

            if 'R3' in data_point:
                self.hotplate_r3_plot_data[logical_channel]['time'].append(data_point['timestamp_app'] - self.start_time)
                self.hotplate_r3_plot_data[logical_channel]['R3'].append(data_point['R3'])

        while self.hotplate_data_queue:
            self.hotplate_data_queue.popleft()

        max_x = 0
        min_x = 0
        has_data = False

        for i in range(self.num_channels):
            if self.channel_states[i] and self.plot_data[i]['time']:
                self.lines_eco2[i].set_data(list(self.plot_data[i]['time']), list(self.plot_data[i]['eco2']))
                self.lines_tvoc[i].set_data(list(self.plot_data[i]['time']), list(self.plot_data[i]['tvoc']))

                current_max_x = self.plot_data[i]['time'][-1]
                current_min_x = self.plot_data[i]['time'][0]
                if not has_data or current_max_x > max_x:
                    max_x = current_max_x
                if not has_data or current_min_x < min_x:
                    min_x = current_min_x
                has_data = True
            else:
                self.lines_eco2[i].set_data([], [])
                self.lines_tvoc[i].set_data([], [])

            if self.channel_states[i] and self.hotplate_r3_plot_data[i]['time']:
                self.lines_hotplate_r3[i].set_data(list(self.hotplate_r3_plot_data[i]['time']), list(self.hotplate_r3_plot_data[i]['R3']))
                current_max_x_r3 = self.hotplate_r3_plot_data[i]['time'][-1]
                if not has_data or current_max_x_r3 > max_x:
                    max_x = current_max_x_r3
                has_data = True
            else:
                self.lines_hotplate_r3[i].set_data([], [])

        if has_data:
            x_min = max(0, max_x - 120)
            self.ax1.set_xlim(x_min, max_x + 2)
            active_eco2_data = [val for i in range(self.num_channels) if self.channel_states[i] for val in self.plot_data[i]['eco2']]
            if active_eco2_data: self.ax1.set_ylim(min(active_eco2_data) * 0.95, max(active_eco2_data) * 1.05)
            else: self.ax1.set_ylim(300, 2000)

            active_tvoc_data = [val for i in range(self.num_channels) if self.channel_states[i] for val in self.plot_data[i]['tvoc']]
            if active_tvoc_data: self.ax2.set_ylim(min(active_tvoc_data) * 0.95, max(active_tvoc_data) * 1.05)
            else: self.ax2.set_ylim(0, 500)

            active_r3_data = [val for i in range(self.num_channels) if self.channel_states[i] for val in self.hotplate_r3_plot_data[i]['R3']]
            active_r3_data = [x for x in active_r3_data if not (isinstance(x, float) and x != x)]
            if active_r3_data: self.ax3.set_ylim(min(active_r3_data) * 0.95, max(active_r3_data) * 1.05)
            else: self.ax3.set_ylim(100, 10000)

        all_lines = list(self.lines_eco2.values()) + list(self.lines_tvoc.values()) + list(self.lines_hotplate_r3.values())
        return all_lines

    def on_closing(self):
        if self.ani: self.ani.event_source.stop()
        plt.close(self.fig)
        self.master.destroy()

class SerialPortApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitoring and Control of ENS160 Sensors, TCA9548A Multiplexer, and Arduino Nano 33 IOT")
        self.root.geometry("1100x600")

        self.serial_port_obj = None
        self.reading_thread = None
        self.reading_thread_active = False
        self.streaming_active = False

        self.sensor_data_for_plot = deque()
        self.hotplate_data_for_plot = deque()
        self._current_hotplate_read = {}

        self.num_channels = 6
        self.tca_channels = [0, 1, 2, 3, 4, 5] 
        self.channel_states = [False] * self.num_channels
        self.channel_indicator_labels = []

        self.red_square_photo = None
        self.green_square_photo = None
        self.channel_red_photos = []
        self.channel_green_photos = []
        self._load_images()
        self.plot_window = None
        self.csv_file = None
        self.csv_writer = None
        self.is_logging = False
        self.log_file_name = ""

        self.top_frame = ttk.Frame(root)
        self.top_frame.pack(pady=10, padx=10, fill="x")
        self.main_content_frame = ttk.Frame(root)
        self.main_content_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.left_panel = ttk.LabelFrame(self.main_content_frame, text="Control Center")
        self.left_panel.pack(side="left", fill="y", padx=5, pady=5)
        self.right_panel = ttk.LabelFrame(self.main_content_frame, text="Data Console")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        self.control_frame = ttk.LabelFrame(self.top_frame, text="Port Control")
        self.control_frame.pack(pady=5, padx=5, fill="x")

        ttk.Label(self.control_frame, text="Serial Port:").pack(side="left", padx=5)
        self.port_names = []
        self.selected_port_var = tk.StringVar()
        self.port_combobox = ttk.Combobox(self.control_frame, textvariable=self.selected_port_var, width=30, state="readonly")
        self.port_combobox.pack(side="left", padx=5)
        self.port_combobox.bind("<<ComboboxSelected>>", self.on_port_selected)

        self.refresh_button = ttk.Button(self.control_frame, text="Refresh Ports", command=self.refresh_ports)
        self.refresh_button.pack(side="left", padx=5)
        self.open_close_button = ttk.Button(self.control_frame, text="Open Port", command=self.toggle_port)
        self.open_close_button.pack(side="left", padx=5)
        self.open_close_button["state"] = "disabled"
        self.status_label = ttk.Label(self.control_frame, text="Status: No port selected.")
        self.status_label.pack(side="left", padx=10)
        self.multiplexer_viz_frame = ttk.LabelFrame(self.left_panel, text="Channel Selection")
        self.multiplexer_viz_frame.pack(pady=10, padx=5, fill="both", expand=True)
        self.plot_frame = ttk.LabelFrame(self.left_panel, text="Graphs")
        self.plot_frame.pack(pady=10, padx=5, fill="x")
        self.plot_button = ttk.Button(self.plot_frame, text="Show Graphs", command=self.open_plot_window)
        self.plot_button.pack(pady=10, padx=5, fill="x", expand=True)
        self.csv_logging_frame = ttk.LabelFrame(self.left_panel, text="CSV Logging")
        self.csv_logging_frame.pack(pady=10, padx=5, fill="x")
        self.csv_log_button = ttk.Button(self.csv_logging_frame, text="Start CSV Log", command=self.toggle_csv_logging)
        self.csv_log_button.pack(pady=5, padx=5, fill="x")
        self.csv_log_button["state"] = "disabled"
        self.channel_indicators_frame = ttk.Frame(self.multiplexer_viz_frame)
        self.channel_indicators_frame.pack(pady=5)

        for i in range(self.num_channels):
            channel_row = ttk.Frame(self.channel_indicators_frame)
            channel_row.pack(fill="x", pady=2)
            # Use tca_channels to display the correct physical channel in the UI
            ttk.Label(channel_row, text=f"CH{self.tca_channels[i]}:").pack(side="left", padx=5)
            indicator_button = ttk.Button(channel_row, image=self.red_square_photo, command=lambda ch=i: self.toggle_channel_button(ch))
            indicator_button.pack(side="left", padx=5)
            self.channel_indicator_labels.append(indicator_button)

        self.command_frame = ttk.LabelFrame(self.right_panel, text="Send Commands")
        self.command_frame.pack(side="bottom", pady=10, padx=10, fill="x")
        self.received_data_text = scrolledtext.ScrolledText(self.right_panel, wrap=tk.WORD, state="disabled", width=70, height=15)
        self.received_data_text.pack(pady=5, padx=5, fill="both", expand=True)
        self.input_area_frame = ttk.Frame(self.command_frame)
        self.input_area_frame.pack(side="left", padx=5, fill="x", expand=True)
        ttk.Label(self.input_area_frame, text="Command:").pack(side="left", padx=5)
        self.command_entry = ttk.Entry(self.input_area_frame)
        self.command_entry.pack(side="left", fill="x", expand=True)
        self.command_entry.bind("<Return>", self.send_command_from_entry)
        
        self.send_button = ttk.Button(self.command_frame, text="Send", command=self.send_command_from_entry)
        self.send_button.pack(side="right", padx=5)
        self.read_all_button = ttk.Button(self.command_frame, text="Read All Sensors", command=self.send_read_all_command)
        self.read_all_button.pack(side="right", padx=5)
        
        self._set_command_controls_state("disabled")
        self.refresh_ports()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _load_images(self):
        self.red_square_photo = tk.PhotoImage(width=30, height=30)
        self.red_square_photo.put("red", to=(0,0,30,30))
        self.green_square_photo = tk.PhotoImage(width=30, height=30)
        self.green_square_photo.put("green", to=(0,0,30,30))

    def _set_command_controls_state(self, state):
        self.command_entry["state"] = state
        self.send_button["state"] = state
        self.read_all_button["state"] = state
        self.csv_log_button["state"] = "normal" if state == "normal" else "disabled"

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_names = [port.device for port in ports]
        descriptions = [f"{port.device} - {port.description}" for port in ports]
        if not ports:
            descriptions.append("No serial ports found.")
            self.open_close_button["state"] = "disabled"
        else:
            self.selected_port_var.set(descriptions[0])
            self.selected_port_name = self.port_names[0]
            self.open_close_button["state"] = "normal"
        self.port_combobox['values'] = descriptions
        self.status_label.config(text="Status: Ports refreshed.")

    def on_port_selected(self, event):
        selected_index = self.port_combobox.current()
        if selected_index >= 0:
            self.selected_port_name = self.port_names[selected_index]
            self.status_label.config(text=f"Status: Port selected: {self.selected_port_name}")
            self.open_close_button["state"] = "normal"

    def toggle_port(self):
        if self.serial_port_obj is None or not self.serial_port_obj.is_open:
            try:
                self.serial_port_obj = serial.Serial(port=self.selected_port_name, baudrate=9600, timeout=0.1)
                time.sleep(2)
                self.status_label.config(text=f"Status: Port {self.selected_port_name} OPEN.")
                self.open_close_button.config(text="Close Port")
                self._set_command_controls_state("normal")
                self.append_to_text_area(f"--- Port {self.selected_port_name} OPEN ---\n")
                self.reading_thread_active = True
                self.reading_thread = threading.Thread(target=self._read_serial_data_thread, daemon=True)
                self.reading_thread.start()
                self.serial_port_obj.write(b"STATUS\n")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open {self.selected_port_name}:\n{e}")
        else:
            self.stop_csv_logging()
            self.reading_thread_active = False
            if self.reading_thread and self.reading_thread.is_alive(): self.reading_thread.join(timeout=1)
            self.serial_port_obj.close()
            self.status_label.config(text=f"Status: Port {self.selected_port_name} CLOSED.")
            self.open_close_button.config(text="Open Port")
            self._set_command_controls_state("disabled")
            self.append_to_text_area(f"--- Port {self.selected_port_name} CLOSED ---\n")
            self._update_channel_indicators(all_off=True)

    def _read_serial_data_thread(self):
        while self.reading_thread_active and self.serial_port_obj.is_open:
            try:
                if self.serial_port_obj.in_waiting > 0:
                    line = self.serial_port_obj.readline().decode('utf-8', errors='ignore').strip()
                    if line: self.root.after(0, self._process_incoming_line, line)
                time.sleep(0.01)
            except Exception as e:
                self.reading_thread_active = False
                break

    def _process_incoming_line(self, line):
        sensor_match = re.match(r'(\d+),CH(\d+),eCO2=(\d+),TVOC=(\d+),AQI=(\d+)(,R0=(\d+),R1=(\d+),R2=(\d+),R3=(\d+))?', line)
        status_match = re.match(r'STATUS: streaming=(ON|OFF), interval=(\d+) ms, inited_mask=0b([01]+)', line)

        if sensor_match:
            groups = sensor_match.groups()
            physical_channel = int(groups[1])
            try:
                logical_index = self.tca_channels.index(physical_channel)
            except ValueError:
                self.append_to_text_area(f"[WARNING] Received data from unknown channel {physical_channel}. Ignoring.\n")
                return

            data_point = {
                'timestamp_app': time.time(),
                'timestamp_arduino': int(groups[0]),
                'channel': logical_index, # <-- Use the logical index (0-5)
                'physical_channel': physical_channel, # Store physical channel for log
                'eCO2': int(groups[2]), 'TVOC': int(groups[3]), 'AQI': int(groups[4])
            }
            if groups[5]: # If there is resistance data
                data_point.update({'R0': int(groups[6]), 'R1': int(groups[7]), 'R2': int(groups[8]), 'R3': int(groups[9])})

            self.sensor_data_for_plot.append(data_point)
            self.append_to_text_area(f"[{time.strftime('%H:%M:%S')}] Data from CH{physical_channel} received.\n")
            if self.is_logging: self._write_to_csv(data_point)

        elif status_match:
            streaming_status, interval, init_mask_bin = status_match.groups()
            self.append_to_text_area(f"→ {line}\n")
            padded_mask = init_mask_bin.zfill(self.num_channels)
            for i in range(self.num_channels):
                self.channel_states[i] = (padded_mask[self.num_channels - 1 - i] == '1')
            self._update_channel_indicators()
            self.streaming_active = (streaming_status == "ON")
        else:
            self.append_to_text_area(f"→ {line}\n")

    def _update_channel_indicators(self, all_off=False):
        for i in range(self.num_channels):
            if all_off or not self.channel_states[i]:
                self.channel_indicator_labels[i].config(image=self.red_square_photo)
            else:
                self.channel_indicator_labels[i].config(image=self.green_square_photo)

    def toggle_channel_button(self, channel_num):
        if not self.serial_port_obj or not self.serial_port_obj.is_open:
            messagebox.showwarning("Port Closed", "Please open the serial port first.")
            return

        temp_channel_states = list(self.channel_states)
        temp_channel_states[channel_num] = not temp_channel_states[channel_num]
        active_channels = [str(i) for i, state in enumerate(temp_channel_states) if state]

        if not active_channels: command_to_send = "CLEAR_CHANNELS"
        elif len(active_channels) == self.num_channels: command_to_send = "ALL_CHANNELS"
        else: command_to_send = f"SET_CHANNELS {','.join(active_channels)}"
        self.send_command_to_arduino(command_to_send)

    def append_to_text_area(self, text):
        self.received_data_text.config(state="normal")
        self.received_data_text.insert(tk.END, text)
        self.received_data_text.see(tk.END)
        self.received_data_text.config(state="disabled")

    def send_command_to_arduino(self, command):
        if self.serial_port_obj and self.serial_port_obj.is_open:
            cmd_upper = command.upper()
            self.append_to_text_area(f"<< Sending: {cmd_upper}\n")
            self.serial_port_obj.write((cmd_upper + '\n').encode())
        else:
            messagebox.showerror("Send Error", "The serial port is not open.")

    def send_command_from_entry(self, event=None):
        command = self.command_entry.get().strip()
        if command:
            self.send_command_to_arduino(command)
            self.command_entry.delete(0, tk.END)
            
    def send_read_all_command(self):
        self.send_command_to_arduino("READ_ALL")

    def open_plot_window(self):
        if self.plot_window is None or not self.plot_window.winfo_exists():
            self.plot_window = tk.Toplevel(self.root)
            self.plot_app = PlottingApp(self.plot_window, self.sensor_data_for_plot, self.hotplate_data_for_plot, self.channel_states, self.num_channels, self.tca_channels)
        else:
            self.plot_window.lift()

    def toggle_csv_logging(self):
        if not self.is_logging:
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                self.log_file_name = f"sensor_data_{timestamp}.csv"

                # create folder in the specified path
                log_dir = Path.home() / 'Documents' / 'sensor_logs'
                log_dir.mkdir(parents=True, exist_ok=True)

                full_path = log_dir / self.log_file_name
                
                # Open file and create writer
                self.csv_file = open(full_path, 'w', newline='')
                self.csv_writer = csv.writer(self.csv_file)

                header = [
                    "Timestamp", "Arduino_MS", "Channel", 
                    "eCO2", "TVOC", "AQI", 
                    "R0", "R1", "R2", "R3"
                ]
                self.csv_writer.writerow(header)
                
                self.csv_file.flush() 

                self.is_logging = True
                self.csv_log_button.config(text="Stop CSV Log")

                # inform user of full path
                self.append_to_text_area(f"\n--- CSV logging started in '{full_path}' ---\n")

            except (IOError, OSError) as e:
                messagebox.showerror("File Error", f"Could not create CSV file: {e}")
                if self.csv_file:
                    self.csv_file.close()
                self.csv_file = None
                self.csv_writer = None
                self.is_logging = False
                self.csv_log_button.config(text="Start CSV Log")
        
        else:
            self.stop_csv_logging()

    def _write_to_csv(self, data_point):
        if self.csv_writer:
            readable_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data_point.get('timestamp_app', 0)))
            row = [
                readable_timestamp,
                data_point.get('timestamp_arduino', ''),
                data_point.get('physical_channel', ''), # Store physical channel in the CSV
                data_point.get('eCO2', ''), data_point.get('TVOC', ''), data_point.get('AQI', ''),
                data_point.get('R0', ''), data_point.get('R1', ''), data_point.get('R2', ''), data_point.get('R3', '')
            ]
            self.csv_writer.writerow(row)
            self.csv_file.flush()

    def stop_csv_logging(self):
        if self.is_logging:
            if self.csv_file: self.csv_file.close()
            self.is_logging = False
            self.csv_log_button.config(text="Start CSV Log")
            self.append_to_text_area(f"--- CSV logging stopped. File saved as '{self.log_file_name}' ---\n")

    def on_closing(self):
        self.stop_csv_logging()
        if self.serial_port_obj and self.serial_port_obj.is_open: self.toggle_port()
        if self.plot_window and self.plot_window.winfo_exists(): self.plot_app.on_closing()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialPortApp(root)
    root.mainloop()