import paho.mqtt.client as mqtt
import tkinter as tk
from tkinter import ttk
import time
import threading

# Updated Beep Test protocol using a list of dictionaries
protocol = [
    {"level": 1, "shuttles": 7, "time_per_shuttle": 9},
    {"level": 2, "shuttles": 8, "time_per_shuttle": 8},
    {"level": 3, "shuttles": 8, "time_per_shuttle": 7.58},
    {"level": 4, "shuttles": 9, "time_per_shuttle": 7.2},
    {"level": 5, "shuttles": 9, "time_per_shuttle": 6.86},
    {"level": 6, "shuttles": 10, "time_per_shuttle": 6.55},
    {"level": 7, "shuttles": 10, "time_per_shuttle": 6.26},
    {"level": 8, "shuttles": 11, "time_per_shuttle": 6},
    {"level": 9, "shuttles": 11, "time_per_shuttle": 5.76},
    {"level": 10, "shuttles": 11, "time_per_shuttle": 5.54},
    {"level": 11, "shuttles": 12, "time_per_shuttle": 5.33},
    {"level": 12, "shuttles": 12, "time_per_shuttle": 5.14},
    {"level": 13, "shuttles": 13, "time_per_shuttle": 4.97},
    {"level": 14, "shuttles": 13, "time_per_shuttle": 4.8},
    {"level": 15, "shuttles": 13, "time_per_shuttle": 4.65},
    {"level": 16, "shuttles": 14, "time_per_shuttle": 4.5},
    {"level": 17, "shuttles": 14, "time_per_shuttle": 4.36},
    {"level": 18, "shuttles": 15, "time_per_shuttle": 4.24},
    {"level": 19, "shuttles": 15, "time_per_shuttle": 4.11},
    {"level": 20, "shuttles": 16, "time_per_shuttle": 4},
    {"level": 21, "shuttles": 16, "time_per_shuttle": 3.89},
]

current_level = 0
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
        if current_level < len(protocol):
            level_data = protocol[current_level]
            num_shuttles = level_data["shuttles"]
            time_per_shuttle = level_data["time_per_shuttle"]
            
            if current_shuttle > num_shuttles:
                current_level += 1
                current_shuttle = 1
                if current_level >= len(protocol):
                    running = False
                    return
                continue
            
            time_left = time_per_shuttle
            
            while time_left > 0:
                update_timer_display(time_left, level_data["level"])
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
    global current_shuttle, passed_checkpoints, running
    with lock:
        current_shuttle += 1
        if current_level >= len(protocol) or current_shuttle > protocol[current_level]["shuttles"]:
            current_level += 1
            current_shuttle = 1
            if current_level >= len(protocol):
                running = False
                return
        
        for player in selected_players:
            passed_checkpoints[player] = {"A": False, "B": False}
            if selected_players[player]:
                player_status[player] = "Waiting"
        
        update_table()
        threading.Thread(target=start_protocol, daemon=True).start()

def update_timer_display(time_left, level):
    timer_label.config(text=f"Level: {level} | Shuttle: {current_shuttle} | Time Left: {time_left}s")

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
