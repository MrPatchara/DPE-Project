import paho.mqtt.client as mqtt
import tkinter as tk
from tkinter import ttk
import time
import threading
import pyttsx3
import platform
import os
import pygame
import queue

# ตั้งค่าเสียงพูด
engine = pyttsx3.init()
engine.setProperty("rate", 150)  # ปรับความเร็วเสียงพูด
speech_queue = queue.Queue()

def speech_worker():
    """ รันคิวข้อความที่ต้องพูด เพื่อป้องกัน run loop already started """
    while True:
        text = speech_queue.get()
        engine.say(text)
        engine.runAndWait()
        speech_queue.task_done()

# เริ่ม thread สำหรับพูด
speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

def speak_text(text):
    """ ใส่ข้อความเข้า queue เพื่อป้องกันการเรียกซ้อนกันของ pyttsx3 """
    speech_queue.put(text)

# ตั้งค่า pygame สำหรับเล่นไฟล์เสียง
pygame.mixer.init()

def play_beep(beep_type="shuttle"):
    """ เล่นเสียง Beep จากไฟล์ """
    if beep_type == "shuttle":
        pygame.mixer.music.load("beep.mp3")
    elif beep_type == "level":
        pygame.mixer.music.load("double_beep.mp3")
    
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # รอให้เสียงเล่นจบก่อน
        time.sleep(0.1)


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
warning_count = {f'Player {i}': 0 for i in range(1, 11)}


selected_players = {f'Player {i}': False for i in range(1, 11)}
player_status = {f'Player {i}': "Waiting" for i in range(1, 11)}
passed_checkpoints = {f'Player {i}': {"A": False, "B": False} for i in range(1, 11)}
checkpoint_time = {f'Player {i}': {"A": None, "B": None} for i in range(1, 11)}

def start_protocol():
    """ เริ่มโปรโตคอลและควบคุมการทำงานของ Shuttle Test """
    global current_level, current_shuttle, running
    if not running:
        return

    if current_level >= len(protocol):
        running = False
        return

    level_data = protocol[current_level]
    num_shuttles = level_data["shuttles"]
    time_per_shuttle = level_data["time_per_shuttle"]

    if current_shuttle > num_shuttles:
        current_level += 1
        current_shuttle = 1
        if current_level >= len(protocol):
            running = False
            return

    # ✅ เริ่มนับเวลาถอยหลังแบบสมูท
    countdown(time_per_shuttle)

def countdown(time_left):
    """ นับเวลาถอยหลังแบบสมูท """
    global running
    if not running:
        return

    if time_left <= 0:
        root.after(0, timer_label.config(text=f"Level: {current_level + 1} | Shuttle: {current_shuttle} | Time Left: 0.0s"))
        root.after(500, check_shuttle_completion)  # ✅ รอ 0.5 วินาทีก่อนตรวจสอบ Shuttle
        return
    
    # ✅ อัปเดต GUI ทุก 100ms
    root.after(0, timer_label.config(text=f"Level: {current_level + 1} | Shuttle: {current_shuttle} | Time Left: {time_left:.1f}s"))
    
    # ✅ เรียก countdown ใหม่ทุก 100ms
    root.after(100, lambda: countdown(time_left - 0.1))

def check_shuttle_completion():
    """ ตรวจสอบว่านักกีฬาผ่านเซ็นเซอร์ครบหรือไม่ เมื่อหมดเวลา """
    global running
    with lock:
        for player in selected_players:
            if player_status[player] == "Disqualified":
                continue  # ข้ามผู้ที่ถูกตัดออกแล้ว

            if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                player_status[player] = "Passed"
            else:
                warning_count[player] += 1
                if warning_count[player] >= 2:
                    player_status[player] = "Disqualified"  # หยุดการทดสอบของผู้เล่น
                else:
                    player_status[player] = "Warning"  # ให้ Warning

    root.after(0, update_table)
    root.after(500, reset_shuttle)  # ✅ รอ 0.5 วินาทีแล้วเริ่ม Shuttle ใหม่

def reset_shuttle():
    """ รีเซ็ต Shuttle และเริ่ม Shuttle ใหม่ """
    global current_shuttle, current_level, running
    with lock:
        if not running:
            return

        # เช็คว่ากำลังเปลี่ยน Level หรือไม่
        level_up = current_shuttle >= protocol[current_level]["shuttles"]

        if level_up:
            current_level += 1
            current_shuttle = 1
        else:
            current_shuttle += 1

        if current_level >= len(protocol):
            running = False
            return

        # ✅ เล่นเสียง Beep ก่อนประกาศ
        if level_up:
            play_beep("level")  # Double Beep เมื่อเปลี่ยน Level
            time.sleep(2)  # รอให้เสียง Beep จบก่อนพูด
            speak_text(f"Level {current_level + 1}")  # พูด Level ใหม่
        else:
            play_beep("shuttle")  # Single Beep เมื่อเปลี่ยน Shuttle
            time.sleep(1)  # รอให้เสียง Beep จบก่อนพูด
        
        speak_text(f"Level {current_level + 1} - Shuttle {current_shuttle}")  # ✅ พูด Shuttle ถูกต้อง

        # ✅ รีเซ็ตเฉพาะคนที่ยังไม่ Disqualified
        for player in selected_players:
            if player_status[player] not in ["Disqualified"]:  # ถ้า Disqualified แล้วไม่ต้องรีเซ็ต
                passed_checkpoints[player] = {"A": False, "B": False}
                player_status[player] = "Waiting"  # กลับไปเริ่มต้นใหม่

        root.after(0, update_table)

    # ✅ เริ่ม Shuttle ถัดไป
    root.after(1000, start_protocol)


def on_message(client, userdata, msg):
    """ รับข้อมูลจาก MQTT และบันทึกเวลาผ่านเซ็นเซอร์ """
    sensor_data = msg.topic.split("/")[-1]
    sensor_mapping = {f"athlete_status_{chr(65 + i)}": (f"Player {i//2+1}", "A" if i % 2 == 0 else "B") for i in range(20)}
    
    if sensor_data in sensor_mapping:
        player, checkpoint = sensor_mapping[sensor_data]
        if selected_players[player]:
            with lock:
                # ✅ บันทึกเวลาที่นักกีฬาผ่านเซ็นเซอร์
                passed_checkpoints[player][checkpoint] = True
                checkpoint_time[player][checkpoint] = time.time()

                # ✅ ถ้าผ่านทั้ง A และ B ให้เปลี่ยนเป็น "Passed"
                if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                    player_status[player] = "Passed"

            root.after(0, update_table)


def update_table():
    tree.delete(*tree.get_children())
    for player, status in player_status.items():
        if selected_players[player]:
            color = (
                "green" if status == "Passed" else 
                "orange" if status == "Warning" else 
                "red" if status == "Disqualified" else "white"
            )
            display_name = f"{player} ({warning_count[player]} warnings)" if warning_count[player] > 0 else player
            tree.insert("", "end", values=(display_name, status), tags=(color,))
    tree.tag_configure("green", background="lightgreen")
    tree.tag_configure("orange", background="yellow")
    tree.tag_configure("red", background="lightcoral")


def start_test():
    global running
    running = True
    
    # ✅ เล่นเสียง Beep ก่อนเริ่ม (เริ่มด้วย Shuttle 1)
    play_beep("shuttle")
    
    # ✅ รอเสียง Beep จบก่อนแล้วค่อยพูด
    time.sleep(1)
    
    # ✅ ประกาศเริ่มต้น
    speak_text("Starting the test. Level 1 - Shuttle 1")

    for player in selected_players:
        selected_players[player] = player_vars[player].get()
    
    root.after(0, update_table)
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
