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

# ✅ ตัวแปรสำหรับเก็บจำนวน Warning สูงสุด (ค่าเริ่มต้นคือ 2)
max_warnings = 2

# ✅ ฟังก์ชันสำหรับตั้งค่า Warning
def set_max_warnings():
    global max_warnings
    try:
        new_value = int(warning_var.get())
        if new_value >= 0:
            max_warnings = new_value
            speak_text(f"Maximum warnings set to {max_warnings}")
        else:
            speak_text("Please enter a value 0 or higher.")
    except ValueError:
        speak_text("Invalid input. Please enter a valid number.")


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
}

# ✅ Yo-Yo Intermittent Recovery Test Level 1
protocols_yoyo = {
    "Yo-Yo Intermittent Recovery Test Level 1": [
        {"level": 5, "shuttle": 1, "A-B": 7, "B-A": 7, "rest_time": 10},
        {"level": 8, "shuttle": 1, "A-B": 6.26, "B-A": 6.26, "rest_time": 10},
        {"level": 11, "shuttle": 2, "A-B": 5.53846, "B-A": 5.53846, "rest_time": 10},
        {"level": 12, "shuttle": 3, "A-B": 5.33333, "B-A": 5.33333, "rest_time": 10},
        {"level": 13, "shuttle": 4, "A-B": 5.14286, "B-A": 5.14286, "rest_time": 10},
        {"level": 14, "shuttle": 8, "A-B": 4.96552, "B-A": 4.96552, "rest_time": 10},
        {"level": 15, "shuttle": 8, "A-B": 4.8, "B-A": 4.8, "rest_time": 10},
        {"level": 16, "shuttle": 8, "A-B": 4.64516, "B-A": 4.64516, "rest_time": 10},
        {"level": 17, "shuttle": 8, "A-B": 4.5, "B-A": 4.5, "rest_time": 10},
        {"level": 18, "shuttle": 8, "A-B": 4.36364, "B-A": 4.36364, "rest_time": 10},
        {"level": 19, "shuttle": 8, "A-B": 4.23529, "B-A": 4.23529, "rest_time": 10},
        {"level": 20, "shuttle": 8, "A-B": 4.11429, "B-A": 4.11429, "rest_time": 10},
        {"level": 21, "shuttle": 8, "A-B": 4, "B-A": 4, "rest_time": 10},
        {"level": 22, "shuttle": 8, "A-B": 3.89189, "B-A": 3.89189, "rest_time": 10},
        {"level": 23, "shuttle": 8, "A-B": 3.78947, "B-A": 3.78947, "rest_time": 10},
    ]
}

# ✅ Protocol สำหรับ Yo-Yo Level 2 แยกจาก Level 1
protocols_yoyo2 = {
    "Yo-Yo Intermittent Recovery Test Level 2": [
        {"level": 11, "shuttle": 1, "A-B":  5.53846, "B-A":  5.53846, "rest_time": 10},
        {"level": 15, "shuttle": 1, "A-B": 4.8, "B-A": 4.8, "rest_time": 10},
        {"level": 17, "shuttle": 2, "A-B": 4.5, "B-A": 4.5, "rest_time": 10},
        {"level": 18, "shuttle": 3, "A-B": 4.36364, "B-A": 4.36364, "rest_time": 10},
        {"level": 19, "shuttle": 4, "A-B": 4.23529, "B-A": 4.23529, "rest_time": 10},
        {"level": 20, "shuttle": 8, "A-B": 4.11429, "B-A": 4.11429, "rest_time": 10},
        {"level": 21, "shuttle": 8, "A-B": 4, "B-A": 4, "rest_time": 10},
        {"level": 22, "shuttle": 8, "A-B": 3.89189, "B-A": 3.89189, "rest_time": 10},
        {"level": 23, "shuttle": 8, "A-B": 3.78947, "B-A": 3.78947, "rest_time": 10},
        {"level": 24, "shuttle": 8, "A-B": 3.69231, "B-A": 3.69231, "rest_time": 10},
        {"level": 25, "shuttle": 8, "A-B": 3.6, "B-A": 3.6, "rest_time": 10},
        {"level": 26, "shuttle": 8, "A-B": 3.51219, "B-A": 3.51219, "rest_time": 10},
        {"level": 27, "shuttle": 8, "A-B": 3.42857, "B-A": 3.42857, "rest_time": 10},
        {"level": 28, "shuttle": 8, "A-B": 3.34884, "B-A": 3.34884, "rest_time": 10},
        {"level": 29, "shuttle": 8, "A-B": 3.27273, "B-A": 3.27273, "rest_time": 10}
    ]
}


def set_protocol():
    """เลือกโปรโตคอลและอัปเดตการทำงาน"""
    global protocol, is_yo_yo_test, is_yo_yo_level_2

    selected = selected_protocol.get()

    if selected in protocols_beep:
        protocol = protocols_beep[selected]
        is_yo_yo_test = False
        is_yo_yo_level_2 = False
        speak_text(f"{selected} selected")

    elif selected in protocols_yoyo:
        protocol = protocols_yoyo[selected]
        is_yo_yo_test = True
        is_yo_yo_level_2 = False
        speak_text(f"{selected} selected")

    elif selected in protocols_yoyo2:
        protocol = protocols_yoyo2[selected]
        is_yo_yo_test = True
        is_yo_yo_level_2 = True
        speak_text(f"{selected} selected")

    # ✅ อัปเดตหัวตารางใหม่ตามโปรโตคอล
    update_table_header()
    reset_test()

    start_button["state"] = "normal"

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
        # ✅ แสดงผลเฉพาะ "Direction Done"
        root.after(0, timer_label.config(text=f"{direction} Done"))

        if direction == "A-B":
            # ✅ เล่นเสียง Beep หลังจาก A → B เสร็จ
            threading.Thread(target=play_beep, args=("shuttle",), daemon=True).start()

            # ✅ เริ่ม B → A หลังจากเสียง Beep
            root.after(1000, lambda: countdown_yo_yo(protocol[current_level]["B-A"], "B-A"))
        elif direction == "B-A":
            root.after(500, check_yo_yo_shuttle_completion)
        return

    # ✅ แสดงผลเฉพาะ "Direction" และ "Time Left"
    root.after(0, timer_label.config(text=f"{direction} | Time Left: {time_left:.1f}s"))

    # ✅ อัปเดตการนับถอยหลังทุก 100 ms
    root.after(100, lambda: countdown_yo_yo(time_left - 0.1, direction))

def check_yo_yo_shuttle_completion():
    """ตรวจสอบ Shuttle Completion สำหรับ Yo-Yo Test"""
    global running
    with lock:
        for player in selected_players:
            if player_status[player] == "Disqualified":
                continue  # ข้ามผู้เล่นที่ถูกตัดสิทธิ์แล้ว

            passed_A = passed_checkpoints[player]["A"]
            passed_B = passed_checkpoints[player]["B"]
            time_A = checkpoint_time[player]["A"]
            time_B = checkpoint_time[player]["B"]

            # ✅ เงื่อนไข 1: ผ่าน A → B → A สำเร็จ (เวลา A > เวลา B)
            if passed_A and passed_B and time_A > time_B:
                player_status[player] = "Passed"
            else:
                # ✅ เงื่อนไข 2: ตรวจสอบการตั้งค่า Warning
                if max_warnings == 0:
                    # ✅ ถ้า Warning = 0 → Disqualify ทันที
                    player_status[player] = "Disqualified"
                else:
                    # ✅ เพิ่มจำนวน Warning และตรวจสอบว่าถึงขีดจำกัดหรือยัง
                    warning_count[player] += 1
                    if warning_count[player] >= max_warnings:
                        player_status[player] = "Disqualified"
                    else:
                        player_status[player] = "Warning"

            # ✅ รีเซ็ตค่าการตรวจสอบสำหรับ Shuttle ถัดไป
            passed_checkpoints[player] = {"A": False, "B": False}

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

        def beep_and_speak():
            pygame.mixer.music.load("beep.mp3")
            pygame.mixer.music.play()
            

        threading.Thread(target=beep_and_speak, daemon=True).start()

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
    """ตรวจสอบ Shuttle Completion สำหรับ Beep Test"""
    global running
    with lock:
        for player in selected_players:
            if player_status[player] == "Disqualified":
                continue  # ✅ ข้ามผู้เล่นที่ถูก Disqualified แล้ว

            passed_A = passed_checkpoints[player]["A"]
            passed_B = passed_checkpoints[player]["B"]

            # ✅ เงื่อนไข 1: ถ้าผ่านทั้ง A และ B ถือว่าสำเร็จ
            if passed_A and passed_B:
                if player_status[player] != "Disqualified":
                    player_status[player] = "Passed"
                # ❌ ไม่รีเซ็ต Warning เพื่อให้สะสมได้

            else:
                # ✅ เงื่อนไข 2: ถ้าไม่ผ่าน ให้ตรวจสอบค่าของ max_warnings
                if max_warnings == 0:
                    # ✅ ถ้า max_warnings = 0 → Disqualified ทันที
                    player_status[player] = "Disqualified"
                else:
                    # ✅ เพิ่มจำนวน Warning
                    warning_count[player] += 1

                    # ✅ ตรวจสอบว่าจำนวน Warning ถึง max_warnings หรือยัง
                    if warning_count[player] >= max_warnings:
                        player_status[player] = "Disqualified"
                    else:
                        player_status[player] = "Warning"

            # ✅ รีเซ็ตค่าการตรวจสอบสำหรับ Shuttle ถัดไป
            passed_checkpoints[player] = {"A": False, "B": False}

    root.after(0, update_table)  # ✅ อัปเดต GUI
    root.after(500, reset_beep_shuttle)  # ✅ ไปยัง Shuttle ถัดไป



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
    """ตรวจสอบ Shuttle Completion สำหรับ Beep Test"""
    global running
    with lock:
        for player in selected_players:
            if player_status[player] == "Disqualified":
                continue  # ✅ ข้ามผู้เล่นที่ถูก Disqualified แล้ว

            passed_A = passed_checkpoints[player]["A"]
            passed_B = passed_checkpoints[player]["B"]

            # ✅ เงื่อนไข 1: ถ้าผ่านทั้ง A และ B ถือว่าสำเร็จ
            if passed_A and passed_B:
                if player_status[player] != "Disqualified":
                    player_status[player] = "Passed"
                # ❌ ไม่รีเซ็ต Warning เพื่อให้สะสมได้

            else:
                # ✅ เงื่อนไข 2: ถ้าไม่ผ่าน ให้ตรวจสอบค่าของ max_warnings
                if max_warnings == 0:
                    # ✅ ถ้า max_warnings = 0 → Disqualified ทันที
                    player_status[player] = "Disqualified"
                else:
                    # ✅ เพิ่มจำนวน Warning
                    warning_count[player] += 1

                    # ✅ ตรวจสอบว่าจำนวน Warning ถึง max_warnings หรือยัง
                    if warning_count[player] >= max_warnings:
                        player_status[player] = "Disqualified"
                    else:
                        player_status[player] = "Warning"

            # ✅ รีเซ็ตค่าการตรวจสอบสำหรับ Shuttle ถัดไป
            passed_checkpoints[player] = {"A": False, "B": False}

    root.after(0, update_table)  # ✅ อัปเดต GUI
    root.after(500, reset_beep_shuttle)  # ✅ ไปยัง Shuttle ถัดไป


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


# ✅ แยกเก็บผลลัพธ์สำหรับ Beep Test และ Yo-Yo Test
player_results_beep = {f'Player {i}': "" for i in range(1, 11)}
player_results_yoyo = {f'Player {i}': "" for i in range(1, 11)}

def update_table():
    """อัปเดตตารางผลลัพธ์แยกกันสำหรับ Beep Test และ Yo-Yo Test"""
    tree.delete(*tree.get_children())  # ✅ ลบข้อมูลเก่าทั้งหมด

    for player, status in player_status.items():
        if selected_players[player]:
            # ✅ ตั้งค่าสีตามสถานะของผู้เล่น
            color = (
                "green" if status == "Passed" else 
                "orange" if status == "Warning" else 
                "red" if status in ["Disqualified", "Fails"] else "white"
            )

            # ✅ แสดงจำนวน Warnings ที่สะสมได้
            display_name = f"{player_names[player]} ({warning_count[player]} warnings)" if warning_count[player] > 0 else player_names[player]

            # ✅ แยกการแสดงผลระหว่าง Beep Test และ Yo-Yo Test
            if is_yo_yo_test:
                level_data = protocol[current_level] if current_level < len(protocol) else {}

                if status in ["Fails", "Disqualified"] and not player_results_yoyo[player]:
                    player_results_yoyo[player] = f"Level {level_data.get('level', '-')}, Shuttle {current_shuttle}"

                result_text = player_results_yoyo[player] if player_results_yoyo[player] else "-"

                tree.insert("", "end", values=(
                    display_name,
                    status,
                    level_data.get("level", "-"),
                    current_shuttle,
                    result_text
                ), tags=(color,))
            else:
                # ✅ สำหรับ Beep Test
                level_data = protocol[current_level] if current_level < len(protocol) else {}

                if status in ["Fails", "Disqualified"] and not player_results_beep[player]:
                    player_results_beep[player] = f"Level {level_data.get('level', '-')}, Shuttle {current_shuttle}"

                result_text = player_results_beep[player] if player_results_beep[player] else "-"

                tree.insert("", "end", values=(
                    display_name,
                    status,
                    level_data.get("level", "-"),
                    current_shuttle,
                    result_text
                ), tags=(color,))

    # ✅ การตั้งค่าสีของแถวตามสถานะ
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
    """รีเซ็ตสถานะทั้งหมดให้พร้อมเริ่มใหม่"""
    global running, current_level, current_shuttle
    running = False
    current_level = 0
    current_shuttle = 1

    start_button["state"] = "normal"

    with lock:
        for player in selected_players:
            player_status[player] = "Waiting"
            warning_count[player] = 0  # ✅ รีเซ็ตจำนวน Warning
            passed_checkpoints[player] = {"A": False, "B": False}
            checkpoint_time[player] = {"A": None, "B": None}
            player_results_beep[player] = ""
            player_results_yoyo[player] = ""
            start_button["state"] = "disabled"

    root.after(0, update_table)
    root.after(0, timer_label.config(text="Ready to Start"))


def update_table_header():
    """อัปเดตหัวตารางสำหรับ Beep Test และ Yo-Yo Test"""
    tree.delete(*tree.get_children())  # ลบข้อมูลเก่า

    if is_yo_yo_test:
        # ✅ หัวตารางสำหรับ Yo-Yo Test
        tree["columns"] = ("Player", "Status", "Level", "Shuttle", "Result")
        tree.heading("Player", text="Player")
        tree.heading("Status", text="Status")
        tree.heading("Level", text="Level")
        tree.heading("Shuttle", text="Shuttle")
        tree.heading("Result", text="Yo-Yo Result")
    else:
        # ✅ หัวตารางสำหรับ Beep Test
        tree["columns"] = ("Player", "Status", "Level", "Shuttle", "Result")
        tree.heading("Player", text="Player")
        tree.heading("Status", text="Status")
        tree.heading("Level", text="Level")
        tree.heading("Shuttle", text="Shuttle")
        tree.heading("Result", text="Beep Test Result")

    tree.pack()



# ✅ สร้างหน้าต่างหลัก
root = tk.Tk()
root.title("Multi-Stage Fitness Test")
root.geometry("800x600")  # ✅ กำหนดขนาดหน้าต่าง

# ✅ ตั้งค่าฟอนต์หลัก
FONT_LARGE = ("Arial", 14, "bold")
FONT_MEDIUM = ("Arial", 12)
FONT_SMALL = ("Arial", 10)

# ✅ ส่วนแสดงเวลา
timer_frame = tk.Frame(root, pady=10)
timer_frame.pack(fill="x")

timer_label = tk.Label(timer_frame, text="Waiting to start...", font=FONT_LARGE, fg="blue")
timer_label.pack()

# ✅ สร้าง Treeview สำหรับแสดงผลลัพธ์
tree_frame = tk.Frame(root, padx=10, pady=10)
tree_frame.pack(fill="both", expand=True)

tree = ttk.Treeview(tree_frame, columns=("Player", "Status", "Result"), show="headings", height=10)
tree.heading("Player", text="Player")
tree.heading("Status", text="Status")
tree.heading("Result", text="Result")
tree.column("Player", width=150)
tree.column("Status", width=100)
tree.column("Result", width=200)

# ✅ แถบเลื่อนแนวตั้ง
tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=tree_scroll.set)
tree_scroll.pack(side="right", fill="y")

tree.pack(fill="both", expand=True)

# ✅ ส่วนเลือก Player
player_frame = tk.LabelFrame(root, text="Select Players", padx=10, pady=10)
player_frame.pack(fill="x", padx=10, pady=5)

player_vars = {f'Player {i}': tk.BooleanVar() for i in range(1, 11)}

for i, (player, var) in enumerate(player_vars.items()):
    frame = tk.Frame(player_frame)
    frame.grid(row=i//5, column=i%5, padx=5, pady=5)

    # ✅ Checkbox สำหรับเลือก Player
    chk = tk.Checkbutton(frame, text=player, variable=var, font=FONT_SMALL)
    chk.pack(side="left")

    # ✅ ปุ่ม Rename Player อยู่ข้าง Checkbox
    rename_btn = tk.Button(frame, text="Rename", font=FONT_SMALL, command=lambda p=player, c=chk: change_player_name(p, c))
    rename_btn.pack(side="left", padx=5)

# ✅ ส่วนเลือกโปรโตคอล
protocol_frame = tk.LabelFrame(root, text="Test Protocol", padx=10, pady=10)
protocol_frame.pack(fill="x", padx=10, pady=5)

selected_protocol = tk.StringVar()
selected_protocol.set("Standard Beep Test")  # ค่าเริ่มต้น

all_protocols = {**protocols_beep, **protocols_yoyo, **protocols_yoyo2}  # รวมทั้ง Beep และ Yo-Yo Test
protocol_menu = ttk.Combobox(protocol_frame, textvariable=selected_protocol, values=list(all_protocols.keys()), state="readonly", font=FONT_MEDIUM)
protocol_menu.pack(side="left", padx=5)

set_protocol_button = tk.Button(protocol_frame, text="Set Protocol", font=FONT_MEDIUM, command=set_protocol)
set_protocol_button.pack(side="left", padx=10)

# ✅ ส่วนควบคุมการทดสอบ
control_frame = tk.Frame(root, pady=10)
control_frame.pack(fill="x")

start_button = tk.Button(control_frame, text="Start Test", font=FONT_MEDIUM, command=start_test, state="disabled", width=12, bg="green", fg="white")
start_button.pack(side="left", padx=10)

reset_button = tk.Button(control_frame, text="Reset Test", font=FONT_MEDIUM, command=reset_test, width=12, bg="red", fg="white")
reset_button.pack(side="left", padx=10)

# ✅ ส่วนตั้งค่า Warning
warning_frame = tk.LabelFrame(root, text="Settings", padx=10, pady=10)
warning_frame.pack(fill="x", padx=10, pady=5)

warning_label = tk.Label(warning_frame, text="Max Warnings (0 = Instant Disqualify):", font=FONT_MEDIUM)
warning_label.pack(side="left")

warning_var = tk.IntVar(value=max_warnings)
warning_entry = tk.Entry(warning_frame, textvariable=warning_var, width=5, font=FONT_MEDIUM)
warning_entry.pack(side="left", padx=5)

set_warning_button = tk.Button(warning_frame, text="Set Warnings", font=FONT_MEDIUM, command=set_max_warnings)
set_warning_button.pack(side="left", padx=5)

# ✅ ตั้งค่า MQTT
client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.100.189", 1883)
client.subscribe("fitness_test/#")
client.loop_start()

# ✅ เริ่ม GUI
root.mainloop()