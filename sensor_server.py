# This Python script runs on your MacBook Pro. It acts as a TCP server,
# receiving live sensor data from the Wear OS app and visualizing it
# in real-time using a more robust Matplotlib approach.

import socket
import threading
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
import time
from queue import Queue
import math

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 9090       # Must match the port in the Kotlin code

# --- Global Data Storage and Communication ---
# A thread-safe queue to pass received data from the network thread to the main thread
data_queue = Queue()

# A dictionary to store the history of sensor data for plotting
live_sensor_data = {}

# Maximum number of data points to display on the plots
MAX_POINTS = 100

def handle_client(conn, addr):
    """Handles a single client connection, receiving data and putting it in the queue."""
    print(f"Connected by {addr}")
    # Initialize a buffer for this client to handle fragmented messages
    buffer = ""
    try:
        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    print(f"Connection with {addr} closed by client.")
                    break
                
                # Append received data to the buffer and process line by line
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        # print(f"Received data from {addr}: {line}") # Optional: can be noisy
                        data_queue.put(line)

    except ConnectionResetError:
        print(f"Client {addr} disconnected unexpectedly.")
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        print(f"Connection from {addr} closed.")

def server_thread():
    """Sets up and runs the TCP server to listen for clients."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            try:
                conn, addr = s.accept()
                client_handler = threading.Thread(target=handle_client, args=(conn, addr))
                client_handler.daemon = True
                client_handler.start()
            except Exception as e:
                print(f"Error accepting connection: {e}")
                time.sleep(1)

def parse_data(line):
    """Parses a single line of data and updates the global data structure."""
    try:
        parts = line.strip().split(',')
        sensor_name = parts[0]
        values = [float(v) for v in parts[2:]]
        timestamp_ms = int(parts[1])
        timestamp_s = timestamp_ms / 1000.0  # Convert ms to seconds

        if sensor_name not in live_sensor_data:
            num_values = len(values)
            live_sensor_data[sensor_name] = {
                'values': [[] for _ in range(num_values)],
                'timestamps': []
            }
        
        # Append new values and a timestamp
        for i, val in enumerate(values):
            live_sensor_data[sensor_name]['values'][i].append(val)
        live_sensor_data[sensor_name]['timestamps'].append(timestamp_s)

        # Limit the size of the data lists to MAX_POINTS
        for i in range(len(values)):
            if len(live_sensor_data[sensor_name]['values'][i]) > MAX_POINTS:
                live_sensor_data[sensor_name]['values'][i].pop(0)
        if len(live_sensor_data[sensor_name]['timestamps']) > MAX_POINTS:
            live_sensor_data[sensor_name]['timestamps'].pop(0)
    
    except (ValueError, IndexError) as e:
        print(f"Error parsing line: '{line}'. Exception: {e}")

def main_plot_loop():
    """The main loop for plotting data in real-time."""
    plt.ion() # Turn on interactive mode
    fig, axes = None, None
    num_sensors_prev = 0

    while True:
        # Process all data currently in the queue
        while not data_queue.empty():
            line = data_queue.get()
            parse_data(line)

        num_sensors_current = len(live_sensor_data)

        # If the number of sensors has changed, re-create the subplots
        if num_sensors_current != num_sensors_prev:
            if fig:
                plt.close(fig) # Close the old figure
            
            if num_sensors_current == 0:
                fig = plt.figure(figsize=(15, 12))
                axes = [fig.add_subplot(1, 1, 1)]
                fig.suptitle('Waiting for Sensor Data...', fontsize=16)
            else:
                rows = math.ceil(math.sqrt(num_sensors_current))
                cols = math.ceil(num_sensors_current / rows)
                fig, axes = plt.subplots(rows, cols, figsize=(15, 12), sharex=False) # sharex=False is safer
                if num_sensors_current == 1:
                    axes = [axes] # Make it a list for consistent iteration
                else:
                    axes = axes.flatten()
                fig.suptitle('Live Wear OS Sensor Data', fontsize=16)

            num_sensors_prev = num_sensors_current

        # Update the plots only if there is data
        if num_sensors_current > 0:
            for i, (sensor_name, data) in enumerate(live_sensor_data.items()):
                # Check if we are trying to access an axis that doesn't exist (can happen during resize)
                if i >= len(axes):
                    continue
                    
                ax = axes[i]
                ax.clear()

                timestamps = data['timestamps']
                # We need at least two points to draw a line
                if len(timestamps) < 2:
                    ax.set_title(sensor_name.replace("_", " ") + " (Waiting for more data...)")
                    continue

                # --- FIX: Create relative timestamps for plotting ---
                first_timestamp = timestamps[0]
                relative_timestamps = [t - first_timestamp for t in timestamps]
                # --- END FIX ---

                for j in range(len(data['values'])):
                    # Ensure value list is not empty for this axis
                    if data['values'][j]:
                        ax.plot(relative_timestamps, data['values'][j], label=f'Axis {j+1}')

                ax.set_title(sensor_name.replace("_", " "))
                ax.set_xlabel("Time Elapsed in Window (s)") # FIX: Updated X-axis label
                ax.set_ylabel("Value")
                ax.legend()
                
                # Set X-limits based on the relative time
                if relative_timestamps:
                    ax.set_xlim(0, relative_timestamps[-1])

                all_vals = [v for axis_data in data['values'] for v in axis_data]
                if all_vals:
                    min_val = min(all_vals)
                    max_val = max(all_vals)
                    padding = (max_val - min_val) * 0.1
                    if padding == 0: padding = 1
                    ax.set_ylim(min_val - padding, max_val + padding)
            
            # Hide any unused subplots
            for j in range(num_sensors_current, len(axes)):
                axes[j].set_visible(False)
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle
            plt.draw()
            plt.pause(0.01) # Small pause to allow GUI updates
        else:
            plt.pause(1) # Wait longer if no data is coming in


if __name__ == '__main__':
    # Start the server thread
    server = threading.Thread(target=server_thread, daemon=True)
    server.start()
    
    # Run the main plotting loop
    try:
        main_plot_loop()
    except KeyboardInterrupt:
        print("\nPlotting stopped by user.")