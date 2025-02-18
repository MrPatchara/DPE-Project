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
from tkinter import simpledialog

# ✅ สร้าง dictionary เก็บชื่อของ Player
player_names = {f'Player {i}': f'Player {i}' for i in range(1, 11)}


def change_player_name(player, chk_button):
    """ เปลี่ยนชื่อ Player และอัปเดต Checkbox """
    new_name = simpledialog.askstring("Change Player Name", f"Enter new name for {player}:")
    if new_name:
        player_names[player] = new_name  # ✅ อัปเดตชื่อใน dictionary
        chk_button.config(text=new_name)  # ✅ อัปเดตชื่อที่ Checkbox
        root.after(0, update_table)  # ✅ อัปเดต GUI

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


# ✅ โปรโตคอลที่สามารถเลือกได้
# ✅ Standard Beep Test
protocols_beep = {
    "Standard Beep Test": [
        {"level": 1, "shuttles": 7, "time_per_shuttle": 9},
        {"level": 2, "shuttles": 8, "time_per_shuttle": 8},
        {"level": 3, "shuttles": 8, "time_per_shuttle": 7.58},
    ]
}

# ✅ Yo-Yo Intermittent Recovery Test Level 1
protocols_yoyo = {
    "Yo-Yo Intermittent Recovery Test Level 1": [
        {"level": 5, "shuttle": 1, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 8, "shuttle": 1, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 11, "shuttle": 2, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 12, "shuttle": 3, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 13, "shuttle": 4, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 14, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 15, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 16, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 17, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 18, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 19, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 20, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 21, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 22, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
        {"level": 23, "shuttle": 8, "A-B": 5, "B-A": 5, "rest_time": 10},
    ]
}


def set_protocol():
    """เปลี่ยนโปรโตคอลและเปิดปุ่ม Start Test"""
    global protocol, is_yo_yo_test

    selected = selected_protocol.get()

    if selected in protocols_beep:
        protocol = protocols_beep[selected]
        is_yo_yo_test = False
    elif selected in protocols_yoyo:
        protocol = protocols_yoyo[selected]
        is_yo_yo_test = True

    speak_text(f"Protocol set to {selected}")
    start_button["state"] = "normal"  # ✅ เปิดปุ่ม Start Test

def speak_yo_yo(level, shuttle, is_recovery=False, is_change=False):
    """พูด Speed Level และ Recovery ตามลำดับที่ถูกต้อง"""
    if is_recovery:
        speak_text("Recovery")
    elif is_change:
        speak_text(f"change to speed LEVEL: {level} , {shuttle}")
    else:
        speak_text(f"speed LEVEL: {level} , {shuttle}")


def start_yo_yo_test():
    """เริ่ม Yo-Yo Test"""
    global current_level, current_shuttle, running
    
    if not running:
        return

    if current_level >= len(protocol):
        running = False
        return

    level_data = protocol[current_level]
    num_shuttles = level_data["shuttle"]

    if current_shuttle > num_shuttles:
        current_level += 1
        current_shuttle = 1
        if current_level >= len(protocol):
            running = False
            return

    # ✅ พูด Speed Level ก่อนเริ่ม A → B (พูดครั้งเดียว)
    if current_shuttle == 1:
        if current_level == 0:
            speak_yo_yo(level_data["level"], current_shuttle)
        else:
            speak_yo_yo(level_data["level"], current_shuttle, is_change=True)
    
    countdown_yo_yo(level_data["A-B"], "A-B")


def countdown_yo_yo(time_left, direction):
    """นับเวลาถอยหลังสำหรับ Shuttle A → B หรือ B → A"""
    global running
    if not running:
        return

    if time_left <= 0:
        root.after(0, timer_label.config(text=f"Level {current_level + 1} | Shuttle {current_shuttle} | {direction} Done"))

        if direction == "A-B":
            # ✅ เล่นเสียง Beep หลังจาก A → B เสร็จ
            threading.Thread(target=play_beep, args=("shuttle",), daemon=True).start()
            
            # ✅ เริ่ม B → A
            root.after(1000, lambda: countdown_yo_yo(protocol[current_level]["B-A"], "B-A"))
        elif direction == "B-A":
            root.after(500, check_yo_yo_shuttle_completion)
        return
    
    root.after(0, timer_label.config(text=f"Level {current_level + 1} | Shuttle {current_shuttle} | {direction} | Time Left: {time_left:.1f}s"))
    root.after(100, lambda: countdown_yo_yo(time_left - 0.1, direction))  


def check_yo_yo_shuttle_completion():
    """ตรวจสอบ Shuttle Completion สำหรับ Yo-Yo Test"""
    global running
    with lock:
        for player in selected_players:
            if player_status[player] == "Disqualified":
                continue

            if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                if checkpoint_time[player]["A"] > checkpoint_time[player]["B"]:
                    player_status[player] = "Passed"
            else:
                warning_count[player] += 1
                if warning_count[player] >= 2:
                    player_status[player] = "Disqualified"
                else:
                    player_status[player] = "Warning"

    root.after(0, update_table)
    root.after(500, rest_before_next_yo_yo_shuttle)  


def rest_before_next_yo_yo_shuttle():
    """พัก 10 วินาทีก่อนเริ่ม Shuttle ใหม่"""
    global current_shuttle, current_level, running
    with lock:
        if not running:
            return

        level_data = protocol[current_level]
        rest_time = level_data["rest_time"]

        # ✅ พูด "Recovery" ก่อนพัก
        speak_yo_yo(level_data["level"], current_shuttle, is_recovery=True)

        def beep_and_speak():
            pygame.mixer.music.load("beep.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

        threading.Thread(target=beep_and_speak, daemon=True).start()
        root.after(rest_time * 1000, reset_yo_yo_shuttle)  



def reset_yo_yo_shuttle():
    """รีเซ็ต Shuttle และเริ่ม Shuttle ใหม่"""
    global current_shuttle, current_level, running
    with lock:
        if not running:
            return

        level_up = current_shuttle >= protocol[current_level]["shuttle"]

        if level_up:
            current_level += 1
            current_shuttle = 1
        else:
            current_shuttle += 1

        if current_level >= len(protocol):
            running = False
            return

        for player in selected_players:
            if player_status[player] not in ["Disqualified"]:
                passed_checkpoints[player] = {"A": False, "B": False}
                player_status[player] = "Waiting"

        root.after(0, update_table)
    
    root.after(1000, start_yo_yo_test)  # ✅ เริ่ม Shuttle ใหม่


def start_beep_test():
    """เริ่ม Beep Test"""
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

    countdown(time_per_shuttle)


def check_beep_shuttle_completion():
    """ตรวจสอบ Shuttle Completion สำหรับ Beep Test (A → B)"""
    global running
    with lock:
        for player in selected_players:
            if player_status[player] == "Disqualified":
                continue

            if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                player_status[player] = "Passed"
            else:
                warning_count[player] += 1
                if warning_count[player] >= 2:
                    player_status[player] = "Disqualified"
                else:
                    player_status[player] = "Warning"

    root.after(0, update_table)
    root.after(500, reset_beep_shuttle)  # ✅ รีเซ็ต Shuttle ใหม่

def reset_beep_shuttle():
    """รีเซ็ต Shuttle และเริ่ม Shuttle ใหม่"""
    global current_shuttle, current_level, running
    with lock:
        if not running:
            return

        level_up = current_shuttle >= protocol[current_level]["shuttles"]

        if level_up:
            current_level += 1
            current_shuttle = 1
        else:
            current_shuttle += 1

        if current_level >= len(protocol):
            running = False
            return

        def beep_and_speak():
            pygame.mixer.music.load("beep.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            speak_text(f"Level {current_level + 1} - Shuttle {current_shuttle}")

        threading.Thread(target=beep_and_speak, daemon=True).start()

        for player in selected_players:
            if player_status[player] not in ["Disqualified"]:
                passed_checkpoints[player] = {"A": False, "B": False}
                player_status[player] = "Waiting"

        root.after(0, update_table)

    root.after(1000, start_beep_test)  # ✅ เริ่ม Shuttle ถัดไปทันที


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

    # ✅ เล่นเสียง Beep และเริ่มนับเวลาพร้อมกัน
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

        # ✅ เล่นเสียง Beep ก่อนพูด (ตัด Beep ที่ซ้ำหลังพูดออก)
        def beep_and_speak():
            if level_up:
                pygame.mixer.music.load("double_beep.mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():  # ✅ รอเสียง Beep จบก่อนพูด
                    time.sleep(0.1)
                speak_text(f"Level {current_level + 1}")  # ✅ พูด Level ใหม่
            else:
                pygame.mixer.music.load("beep.mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():  # ✅ รอเสียง Beep จบก่อนพูด
                    time.sleep(0.1)
                speak_text(f"Level {current_level + 1} - Shuttle {current_shuttle}")  # ✅ พูด Shuttle (ไม่มี Beep ซ้ำ)

        threading.Thread(target=beep_and_speak, daemon=True).start()

        # ✅ รีเซ็ตเฉพาะคนที่ยังไม่ Disqualified
        for player in selected_players:
            if player_status[player] not in ["Disqualified"]:
                passed_checkpoints[player] = {"A": False, "B": False}
                player_status[player] = "Waiting"

        root.after(0, update_table)

    # ✅ เริ่ม Shuttle ถัดไปทันที ไม่ต้องดีเลย์
    root.after(1000, start_protocol)

def on_message(client, userdata, msg):
    """รับข้อมูลจาก MQTT"""
    sensor_data = msg.topic.split("/")[-1]

    sensor_mapping = {}
    for i in range(10):
        player = f"Player {i+1}"
        sensor_mapping[f"athlete_status_{chr(65 + i * 2)}"] = (player, "A")  
        sensor_mapping[f"athlete_status_{chr(66 + i * 2)}"] = (player, "B")  

    if sensor_data in sensor_mapping:
        player, checkpoint = sensor_mapping[sensor_data]
        if selected_players[player]:
            with lock:
                passed_checkpoints[player][checkpoint] = True
                checkpoint_time[player][checkpoint] = time.time()

                if is_yo_yo_test:
                    if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                        if checkpoint_time[player]["A"] > checkpoint_time[player]["B"]:
                            player_status[player] = "Passed"
                else:
                    if passed_checkpoints[player]["A"] and passed_checkpoints[player]["B"]:
                        player_status[player] = "Passed"

            root.after(0, update_table)



# ✅ สร้าง dictionary เก็บผลลัพธ์สุดท้ายของแต่ละ Player
player_results = {f'Player {i}': "" for i in range(1, 11)}

def update_table():
    """Efficiently update the Treeview instead of redrawing everything"""
    for child in tree.get_children():
        tree.delete(child)  # ❌ Clears everything each time (Inefficient)

    for player, status in player_status.items():
        if selected_players[player]:
            color = (
                "green" if status == "Passed" else 
                "orange" if status == "Warning" else 
                "red" if status in ["Disqualified", "Fails"] else "white"
            )

            if status in ["Fails", "Disqualified"] and not player_results[player]:
                player_results[player] = f"Level {current_level + 1} - Shuttle {current_shuttle}"

            display_name = f"{player_names[player]} ({warning_count[player]} warnings)" if warning_count[player] > 0 else player_names[player]
            result_text = player_results[player] if player_results[player] else "-"

            tree.insert("", "end", values=(display_name, status, result_text), tags=(color,))
    
    tree.tag_configure("green", background="lightgreen")
    tree.tag_configure("orange", background="yellow")
    tree.tag_configure("red", background="lightcoral")


def start_test():
    """เริ่มต้นการทดสอบตามโปรโตคอลที่เลือก"""
    global running
    running = True
    start_button.config(state="disabled")
    reset_button.config(state="normal")
    
    play_beep("shuttle")
    time.sleep(1)

    speak_text("Starting the test")

    for player in selected_players:
        selected_players[player] = player_vars[player].get()
    
    root.after(0, update_table)
    
    # ✅ แยกเป็นสองฟังก์ชันอิสระ
    if is_yo_yo_test:
        threading.Thread(target=start_yo_yo_test, daemon=True).start()
    else:
        threading.Thread(target=start_beep_test, daemon=True).start()


def reset_test():
    """ รีเซ็ตสถานะทั้งหมดให้พร้อมเริ่มใหม่ """
    global running, current_level, current_shuttle
    running = False
    current_level = 0
    current_shuttle = 1

    # ✅ เปิดปุ่ม Start Test ให้กดได้อีกครั้ง
    start_button["state"] = "normal"

    # ✅ รีเซ็ตข้อมูลผู้เล่นทั้งหมด
    with lock:
        for player in selected_players:
            player_status[player] = "Waiting"
            warning_count[player] = 0
            passed_checkpoints[player] = {"A": False, "B": False}
            player_results[player] = ""  # ✅ ล้างค่าผลลัพธ์เดิม

    root.after(0, update_table)
    root.after(0, timer_label.config(text="Ready to Start"))
    speak_text("Test reset complete")




root = tk.Tk()
root.title("Multi-Stage Fitness Test")

timer_label = tk.Label(root, text="", font=("Arial", 14))
timer_label.pack()

# ✅ เพิ่มคอลัมน์ใหม่ใน Treeview
tree = ttk.Treeview(root, columns=("Player", "Status", "Result"), show="headings")
tree.heading("Player", text="Player")
tree.heading("Status", text="Status")
tree.heading("Result", text="Result")  # ✅ เพิ่มคอลัมน์ Result
tree.pack()


player_vars = {f'Player {i}': tk.BooleanVar() for i in range(1, 11)}

for player, var in player_vars.items():
    frame = tk.Frame(root)  # ✅ ใช้ Frame เพื่อจัด layout
    frame.pack(anchor="w")  # ✅ จัดให้อยู่ชิดซ้าย

    # ✅ Checkbox สำหรับเลือก Player
    chk = tk.Checkbutton(frame, text=player_names[player], variable=var)
    chk.pack(side="left")

    # ✅ ปุ่ม Rename Player อยู่ข้าง Checkbox
    rename_btn = tk.Button(frame, text="Rename", command=lambda p=player, c=chk: change_player_name(p, c))
    rename_btn.pack(side="left", padx=5)

# ✅ ตัวแปรเก็บโปรโตคอลที่เลือก
selected_protocol = tk.StringVar()
selected_protocol.set("Standard Beep Test")  # ค่าเริ่มต้น

# ✅ สร้างตัวเลือกจากทั้งสองโปรโตคอล
all_protocols = {**protocols_beep, **protocols_yoyo}  # รวมทั้ง Beep และ Yo-Yo Test

# ✅ อัปเดต Dropdown Menu
protocol_menu = tk.OptionMenu(root, selected_protocol, *all_protocols.keys())
protocol_menu.pack()


# ✅ ปุ่มใช้เลือกโปรโตคอล (ต้องกดก่อนถึงจะเริ่มได้)
set_protocol_button = tk.Button(root, text="Set Protocol", command=set_protocol)
set_protocol_button.pack()


# ✅ ปุ่มเริ่มการทดสอบ (ตอนเริ่มต้นปิดไว้)
start_button = tk.Button(root, text="Start Test", command=start_test, state="disabled")
start_button.pack()


reset_button = tk.Button(root, text="Reset Test", command=reset_test)
reset_button.pack()


client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.100.189", 1883)
client.subscribe("fitness_test/#")
client.loop_start()

root.mainloop()
