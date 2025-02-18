import tkinter as tk
from tkinter import messagebox
import paho.mqtt.client as mqtt

# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("fitness_test/athlete_status_A")
    client.subscribe("fitness_test/athlete_status_B")

def on_message(client, userdata, msg):
    global athlete_status_A, athlete_status_B
    payload = msg.payload.decode()
    
    if msg.topic == "fitness_test/athlete_status_A":
        athlete_status_A = payload
        update_gui()
    elif msg.topic == "fitness_test/athlete_status_B":
        athlete_status_B = payload
        update_gui()

# MQTT Setup
broker_address = "192.168.100.189"  # Replace with the IP of your MQTT broker
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker_address, 1883, 60)

# GUI Setup
root = tk.Tk()
root.title("Multi-stage Fitness Test")

# Set initial values
athlete_status_A = "Not Passed"
athlete_status_B = "Not Passed"
test_running = False
current_stage = 1
time_per_stage = 60  # seconds for each stage, adjustable by user
time_left = time_per_stage

# Display current stage and time left
stage_label = tk.Label(root, text=f"Stage: {current_stage}", font=("Helvetica", 16))
stage_label.pack(pady=10)

time_label = tk.Label(root, text=f"Time Remaining: {time_left}s", font=("Helvetica", 16))
time_label.pack(pady=10)

status_label = tk.Label(root, text="Status: Waiting", font=("Helvetica", 16))
status_label.pack(pady=10)

athlete_a_label = tk.Label(root, text="Athlete at A: Not Passed", font=("Helvetica", 16))
athlete_a_label.pack(pady=10)

athlete_b_label = tk.Label(root, text="Athlete at B: Not Passed", font=("Helvetica", 16))
athlete_b_label.pack(pady=10)

# Functions
def start_test():
    global test_running, current_stage, time_left
    test_running = True
    current_stage = 1
    time_left = time_per_stage
    update_gui()
    start_stage()

def stop_test():
    global test_running
    test_running = False
    status_label.config(text="Status: Test Stopped")
    stage_label.config(text="Stage: -")
    time_label.config(text="Time Remaining: 0s")

def update_gui():
    stage_label.config(text=f"Stage: {current_stage}")
    time_label.config(text=f"Time Remaining: {time_left}s")
    athlete_a_label.config(text=f"Athlete at A: {athlete_status_A}")
    athlete_b_label.config(text=f"Athlete at B: {athlete_status_B}")

def start_stage():
    global current_stage, time_left, test_running
    if test_running:
        if time_left > 0:
            time_left -= 1
            update_gui()
            root.after(1000, start_stage)
        else:
            if athlete_status_A == "Not Passed" or athlete_status_B == "Not Passed":
                stop_test()
            else:
                current_stage += 1
                if current_stage > 10:  # Max stage limit
                    stop_test()
                    messagebox.showinfo("Test Complete", "The test has been completed successfully.")
                else:
                    time_left = time_per_stage
                    update_gui()
                    start_stage()

# Start and Stop Buttons
start_button = tk.Button(root, text="Start Test", font=("Helvetica", 16), command=start_test)
start_button.pack(pady=20)

stop_button = tk.Button(root, text="Stop Test", font=("Helvetica", 16), command=stop_test)
stop_button.pack(pady=10)

# Start MQTT Loop
client.loop_start()

root.mainloop()
