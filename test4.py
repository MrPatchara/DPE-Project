import paho.mqtt.client as mqtt
import tkinter as tk
from tkinter import ttk
import time
import threading

# Updated Beep Test protocol
protocol = {
    1: (7, 9, 8.0),
    2: (8, 8, 9.0),
    3: (8, 7.58, 9.5),
    4: (9, 7.2, 10.0),
    5: (9, 6.86, 10.5),
    6: (10, 6.55, 11.0),
    7: (10, 6.26, 11.5),
    8: (11, 6, 12.0),
    9: (11, 5.76, 12.5),
    10: (11, 5.54, 13.0),
    11: (12, 5.33, 13.5),
    12: (12, 5.14, 14.0),
    13: (13, 4.97, 14.5),
    14: (13, 4.8, 15.0),
    15: (13, 4.65, 15.5),
    16: (14, 4.5, 16.0),
    17: (14, 4.36, 16.5),
    18: (15, 4.24, 17.0),
    19: (15, 4.11, 17.5),
    20: (16, 4, 18.0),
    21: (16, 3.89, 18.5),
}

current_level = 1
current_shuttle = 1
running = True
lock = threading.Lock()

# กำหนดตัวแปร global
selected_players = {f'Player {i}': False for i in range(1, 11)}
player_status = {f'Player {i}': "Waiting" for i in range(1, 11)}
passed_checkpoints = {f'Player {i}': {"A": False, "B": False} for i in range(1, 11)}

def start_protocol():
    global current_level, current_shuttle, running
    while running:
        if current_level in protocol:
            num_shuttles, time_per_shuttle, speed = protocol[current_level]
            if current_shuttle > num_shuttles:
                current_level += 1
                current_shuttle = 1
                continue
            
            time_left = time_per_shuttle
            
            while time_left > 0:
                update_timer_display(time_left, speed)
                time.sleep(1)
                time_left -= 1
            
            with lock:
                for player in selected_players:
                    if selected_players[player]:
                        if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                            player_status[player] = "Passed"
                        else:
                            player_status[player] = "Fails"
                
                update_table()
                threading.Thread(target=reset_shuttle, daemon=True).start()
        else:
            running = False

def reset_shuttle():
    global current_level, current_shuttle, passed_checkpoints, running
    with lock:
        current_shuttle += 1
        if current_level not in protocol or current_shuttle > protocol[current_level][0]:
            current_level += 1
            current_shuttle = 1
            if current_level not in protocol:
                running = False
                return  # หยุดการทำงานหากถึง Shuttle สุดท้าย
        
        for player in selected_players:
            passed_checkpoints[player] = {"A": False, "B": False}
            if selected_players[player]:
                player_status[player] = "Waiting"
        
        update_table()
        threading.Thread(target=start_protocol, daemon=True).start()

def update_timer_display(time_left, speed):
    timer_label.config(text=f"Level: {current_level} | Shuttle: {current_shuttle} | Time Left: {time_left}s | Speed: {speed} km/h")

def on_message(client, userdata, msg):
    sensor_data = msg.topic.split("/")[-1]
    status = msg.payload.decode()
    
    sensor_mapping = {
        "athlete_status_A": ("Player 1", "A"),
        "athlete_status_B": ("Player 1", "B"),
        "athlete_status_C": ("Player 2", "A"),
        "athlete_status_D": ("Player 2", "B"),
        "athlete_status_E": ("Player 3", "A"),
        "athlete_status_F": ("Player 3", "B"),
        "athlete_status_G": ("Player 4", "A"),
        "athlete_status_H": ("Player 4", "B"),
        "athlete_status_I": ("Player 5", "A"),
        "athlete_status_J": ("Player 5", "B"),
        "athlete_status_K": ("Player 6", "A"),
        "athlete_status_L": ("Player 6", "B"),
        "athlete_status_M": ("Player 7", "A"),
        "athlete_status_N": ("Player 7", "B"),
        "athlete_status_O": ("Player 8", "A"),
        "athlete_status_P": ("Player 8", "B"),
        "athlete_status_Q": ("Player 9", "A"),
        "athlete_status_R": ("Player 9", "B"),
        "athlete_status_S": ("Player 10", "A"),
        "athlete_status_T": ("Player 10", "B"),
    }
    
    if sensor_data in sensor_mapping:
        player, checkpoint = sensor_mapping[sensor_data]
        if selected_players[player]:
            passed_checkpoints[player][checkpoint] = True
            
            if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                player_status[player] = "Passed"
            
            update_table()

def update_table():
    tree.delete(*tree.get_children())  
    
    for player, status in player_status.items():
        if selected_players[player]:
            color = "green" if status == "Passed" else "red" if status == "Fails" else "white"
            tree.insert("", "end", values=(player, status), tags=(color,))
    
    tree.tag_configure("green", background="lightgreen")
    tree.tag_configure("red", background="lightcoral")

def start_test():
    global selected_players, running  
    running = True
    for player in selected_players:
        selected_players[player] = player_vars[player].get()
    update_table()
    threading.Thread(target=start_protocol, daemon=True).start()

root = tk.Tk()
root.title("Multi-Stage Fitness Test")

timer_label = tk.Label(root, text="", font=("Arial", 14))
timer_label.pack()

tree = ttk.Treeview(root, columns=("Player", "Status"), show="headings")
tree.heading("Player", text="Player")
tree.heading("Status", text="Status")
tree.pack()

player_vars = {f'Player {i}': tk.BooleanVar() for i in range(1, 11)}
for player, var in player_vars.items():
    chk = tk.Checkbutton(root, text=player, variable=var)
    chk.pack()

start_button = tk.Button(root, text="Start Test", command=start_test)
start_button.pack()

client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.100.189", 1883)
client.subscribe("fitness_test/#")
client.loop_start()

root.mainloop()