import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import time
import threading
import paho.mqtt.client as mqtt
import os
from datetime import datetime
from PIL import Image, ImageTk

# ----------------------------
# ตั้งค่าเริ่มต้น
# ----------------------------
BROKER_DEFAULT_IP = "192.168.100.189"
RESULT_FILE = "timing_gate_results.json"
ATHLETE_FILE = "athletes.json"

start_times = {}  # athlete_id -> start timestamp
results = {}       # athlete_id -> list of timings
selected_athlete = None
athlete_dict = {}
running = False

active_sensors = {chr(65 + i): True for i in range(10)}  # A–J

allow_next_round = False  # ✅ กำหนดว่าอนุญาตจับเวลารอบใหม่หรือยัง



def update_display_timer():
    if running:
        now = time.time()
        if selected_athlete and selected_athlete["id"] in start_times:
            elapsed = now - start_times[selected_athlete["id"]]
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            milliseconds = int((elapsed % 1) * 100)  # 2 หลักมิลลิวินาที
            current_display_time.set(f"{minutes:02}:{seconds:02}:{milliseconds:02}")
    root.after(50, update_display_timer)  # อัปเดตถี่ขึ้น (20 FPS)

# ----------------------------
# โหลดรายชื่อนักกีฬา
# ----------------------------
def load_athletes():
    global athlete_dict
    if not os.path.exists(ATHLETE_FILE):
        return []
    with open(ATHLETE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f).get("athletes", [])
        athlete_dict = {a["id"]: a for a in data}
        return data

def save_athletes(athletes):
    with open(ATHLETE_FILE, "w", encoding="utf-8") as f:
        json.dump({"athletes": athletes}, f, indent=4)

# ----------------------------
# ฟังก์ชัน MQTT
# ----------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log("Connected to MQTT Broker")
        client.subscribe("fitness_test/#")
    else:
        log(f"Failed to connect with code {rc}")

player_splits = {}
player_sensors = {}
start_times = {}

def on_message(client, userdata, msg):
    global selected_athlete, running, allow_next_round
    if not running or not selected_athlete:
        return

    topic = msg.topic
    sensor_key = topic.split("_")[-1]

    if not allow_next_round:
        log(f"Ignored sensor {sensor_key} — waiting for 'Next Round'")
        return

    if not active_sensors.get(sensor_key, False):
        return

    aid = selected_athlete["id"]
    active_sequence = [k for k, v in active_sensors.items() if v]
    total_selected = len(active_sequence)

    if total_selected == 1:
        # ✅ โหมด 1 เซ็นเซอร์ (ไป-กลับ)
        if aid not in start_times:
            start_times[aid] = time.time()
            log(f"Single-sensor: Start timing at {sensor_key}")
        else:
            duration = time.time() - start_times[aid]
            del start_times[aid]

            if aid not in results:
                results[aid] = []
            results[aid].append(duration)
            update_result_table()
            log(f"Single-sensor: Stop timing at {sensor_key} → Time: {duration:.6f}s")

            allow_next_round = False  # ✅ ห้ามจับต่อจนกว่าจะกด Next

    elif total_selected == 2:
        # ✅ โหมด 2 เซ็นเซอร์ (เข้าอันไหนก่อนก็ได้ ออกอีกตัว)
        if aid not in player_sensors:
            player_sensors[aid] = []

        if len(player_sensors[aid]) == 0:
            player_sensors[aid].append(sensor_key)
            start_times[aid] = time.time()
            log(f"Dual-sensor: Start timing at {sensor_key}")
        elif len(player_sensors[aid]) == 1 and sensor_key != player_sensors[aid][0]:
            duration = time.time() - start_times[aid]
            if aid not in results:
                results[aid] = []
            results[aid].append(duration)
            update_result_table()
            log(f"Dual-sensor: Stop timing at {sensor_key} → Time: {duration:.6f}s")

            # reset
            player_sensors[aid] = []
            del start_times[aid]
            allow_next_round = False  # ✅ ห้ามจับต่อจนกว่าจะกด Next

    else:
        # ✅ โหมด Split Timing (> 2 sensors)
        if aid not in player_splits:
            player_splits[aid] = []
            player_sensors[aid] = set()

        if sensor_key in player_sensors[aid]:
            log(f"Split: Sensor {sensor_key} already triggered – ignoring")
            return

        now = time.time()
        player_splits[aid].append((sensor_key, now))
        player_sensors[aid].add(sensor_key)
        log(f"Split: Sensor {sensor_key} triggered at {now:.2f}")

        if len(player_splits[aid]) == 1:
            start_times[aid] = now  # สำหรับแสดงเวลา

        if len(player_splits[aid]) == total_selected:
            timestamps = [t[1] for t in sorted(player_splits[aid], key=lambda x: x[1])]
            total_time = timestamps[-1] - timestamps[0]
            split_durations = [round(timestamps[i+1] - timestamps[i], 2) for i in range(len(timestamps)-1)]

            if aid not in results:
                results[aid] = []

            results[aid].append(total_time)
            update_result_table()
            log(f"Split: Finished. Total: {total_time:.2f}s | Splits: {split_durations}")

            # reset
            del start_times[aid]
            player_splits[aid] = []
            player_sensors[aid] = set()
            allow_next_round = False  # ✅ ห้ามจับต่อจนกว่าจะกด Next


# ----------------------------
# ฟังก์ชัน GUI
# ----------------------------
def log(text):
    text_box.insert(tk.END, text + "\n")
    text_box.see(tk.END)

def connect_mqtt():
    global mqtt_connected
    broker_ip = mqtt_ip_entry.get()
    client.connect(broker_ip, 1883)
    threading.Thread(target=client.loop_forever, daemon=True).start()
    mqtt_connected = True
    if not session_started:
        start_button.config(state="normal")


def select_athlete():
    def confirm():
        nonlocal selected
        index = selected.curselection()
        if index:
            aid = str(athletes[index[0]]["id"])
            set_selected_athlete(aid)
            win.destroy()

    athletes = load_athletes()
    win = tk.Toplevel(root)
    win.title("Select Athlete")
    selected = tk.Listbox(win, font=("Arial", 12))
    for a in athletes:
        selected.insert(tk.END, f"{a['first_name']} {a['last_name']} ({a['sport']})")
    selected.pack(fill="both", expand=True)
    tk.Button(win, text="Select", command=confirm).pack(pady=5)

def set_selected_athlete(aid):
    global selected_athlete
    selected_athlete = athlete_dict.get(str(aid))
    if selected_athlete:
        athlete_label.config(text=f"Selected: {selected_athlete['first_name']} {selected_athlete['last_name']}")
        update_result_table()

def update_result_table():
    for row in result_tree.get_children():
        result_tree.delete(row)

    if not selected_athlete:
        return

    aid = selected_athlete["id"]
    rounds = results.get(aid, [])
    for i, t in enumerate(rounds, 1):
        result_tree.insert("", "end", values=(i, f"{t:.6f} sec"))

def save_results():
    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_results = data.get("results", [])
    except:
        all_results = []

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for aid, times in results.items():
        athlete = athlete_dict.get(str(aid))
        if athlete and times:
            result_entry = {
                "athlete_id": aid,
                "first_name": athlete["first_name"],
                "last_name": athlete["last_name"],
                "sport": athlete.get("sport", ""),
                "date": now,
                "timings": times  # ✅ รวมทั้งหมดของ session นี้
            }
            all_results.append(result_entry)

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump({"results": all_results}, f, indent=4)

    messagebox.showinfo("Saved", "Results saved successfully.")


def start_session():
    global running, session_started, allow_next_round
    if not selected_athlete:
        messagebox.showwarning("Warning", "Please select an athlete first.")
        return
    if not mqtt_connected:
        messagebox.showwarning("MQTT", "Please connect to MQTT first.")
        return

    running = True
    session_started = True
    allow_next_round = True  # ✅ เริ่มรอบแรกได้
    start_button.config(state="disabled")
    save_button.config(state="normal")
    next_button.config(state="normal")
    log("Session started. Waiting for sensor triggers...")


def reset_session():
    global running, start_times, results, session_started, allow_next_round
    running = False
    session_started = False
    allow_next_round = False
    start_times = {}
    results = {}
    update_result_table()
    current_display_time.set("00:00:00")
    start_button.config(state="normal" if mqtt_connected else "disabled")
    save_button.config(state="disabled")
    next_button.config(state="disabled")
    log("Session reset. Please press 'Start Session' again.")


def manage_athletes():
    athletes = load_athletes()

    def refresh():
        for row in table.get_children():
            table.delete(row)
        for i, a in enumerate(athletes):
            table.insert("", "end", values=(a["id"], a["first_name"], a["last_name"], a.get("sport", "")))

    def add():
        edit_athlete()
        refresh()

    def edit():
        sel = table.focus()
        if sel:
            index = int(table.index(sel))
            edit_athlete(athletes[index])
            refresh()

    def delete():
        sel = table.focus()
        if sel:
            index = int(table.index(sel))
            del athletes[index]
            save_athletes(athletes)
            refresh()

    def edit_athlete(data=None):
        athlete = {} if data is None else data.copy()
        win = tk.Toplevel()
        win.title("Athlete Form")
        fields = ["first_name", "last_name", "age", "gender", "sport"]
        entries = {}
        for i, f in enumerate(fields):
            tk.Label(win, text=f).grid(row=i, column=0)
            var = tk.StringVar(value=athlete.get(f, ""))
            tk.Entry(win, textvariable=var).grid(row=i, column=1)
            entries[f] = var
        def save():
            for f in fields:
                athlete[f] = entries[f].get()
            if not athlete.get("id"):
                athlete["id"] = str(len(athletes) + 1)
                athletes.append(athlete)
            else:
                for i, a in enumerate(athletes):
                    if a["id"] == athlete["id"]:
                        athletes[i] = athlete
            save_athletes(athletes)
            win.destroy()
        tk.Button(win, text="Save", command=save).grid(row=len(fields), columnspan=2)

    win = tk.Toplevel()
    win.title("Manage Athletes")
    table = ttk.Treeview(win, columns=("ID", "First Name", "Last Name", "Sport"), show="headings")
    for col in table["columns"]:
        table.heading(col, text=col)
    table.pack(fill="both", expand=True)
    btn_frame = tk.Frame(win)
    btn_frame.pack()
    tk.Button(btn_frame, text="Add", command=add).pack(side="left")
    tk.Button(btn_frame, text="Edit", command=edit).pack(side="left")
    tk.Button(btn_frame, text="Delete", command=delete).pack(side="left")
    refresh()

def view_history():
    if not os.path.exists(RESULT_FILE):
        messagebox.showinfo("No Data", "No test results found.")
        return
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f).get("results", [])

    win = tk.Toplevel()
    win.title("Test History")
    tree = ttk.Treeview(win, columns=("Name", "Date", "Times"), show="headings")
    tree.heading("Name", text="Name")
    tree.heading("Date", text="Date")
    tree.heading("Times", text="Timings")
    tree.pack(fill="both", expand=True)

    for i, r in enumerate(data):
        name = f"{r['first_name']} {r['last_name']}"
        date = r['date']
        times = ", ".join([f"{t:.6f}s" for t in r.get("timings", [])])
        tree.insert("", "end", iid=str(i), values=(name, date, times))

    def delete_selected():
        selected = tree.focus()
        if not selected:
            return
        confirm = messagebox.askyesno("Delete", "Are you sure to delete this result?")
        if confirm:
            del data[int(selected)]
            with open(RESULT_FILE, "w", encoding="utf-8") as f:
                json.dump({"results": data}, f, indent=4)
            tree.delete(selected)

    tk.Button(win, text="Delete Selected", command=delete_selected, bg="red", fg="white").pack(pady=5)


def show_sensor_options():
    win = tk.Toplevel()
    win.title("Select Active Sensors")
    vars = {}

    def save_settings():
        for k in vars:
            active_sensors[k] = vars[k].get()
        win.destroy()

    for i, key in enumerate(active_sensors.keys()):
        vars[key] = tk.BooleanVar(value=active_sensors[key])
        cb = tk.Checkbutton(win, text=f"Sensor {key}", variable=vars[key])
        cb.grid(row=i//5, column=i%5, padx=10, pady=5)

    tk.Button(win, text="Save", command=save_settings).grid(row=3, columnspan=5, pady=10)

def allow_next_timing():
    global allow_next_round
    allow_next_round = True
    log("Ready for next round.")

# ----------------------------
# GUI Layout
# ----------------------------
root = tk.Tk()
root.title("Timing Gate System")
root.geometry("900x750")

# เพิ่มไว้หลัง root = tk.Tk()
mqtt_connected = False
session_started = False


# เพิ่ม: ตัวแปรจับเวลาแบบ realtime
current_display_time = tk.StringVar(value="00:00:00")
# 🔻 ป้ายไฟแบบ 7-segment
segment_frame = tk.Frame(root, bg="black")
segment_frame.pack(pady=10)
segment_label = tk.Label(
    segment_frame,
    textvariable=current_display_time,
    font=("Courier New", 56, "bold"),  # หรือใช้ฟอนต์ nixie ถ้ามี
    fg="#ff6600",        # สีส้มอำพันคล้าย nixie
    bg="black",
    padx=30,
    pady=20,
    bd=4,
    relief="sunken",     # มีขอบให้เหมือนกรอบหลอด
    highlightthickness=2,
    highlightbackground="#330000"
)

segment_label.pack()

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

setting_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=setting_menu)
setting_menu.add_command(label="Manage Athletes", command=manage_athletes)
setting_menu.add_command(label="Sensor Options", command=show_sensor_options)


result_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Results", menu=result_menu)
result_menu.add_command(label="View History", command=view_history)

# MQTT + Athlete
mqtt_frame = tk.LabelFrame(root, text="MQTT Broker")
mqtt_frame.pack(fill="x", padx=10, pady=5)

mqtt_ip_entry = tk.Entry(mqtt_frame)
mqtt_ip_entry.insert(0, BROKER_DEFAULT_IP)
mqtt_ip_entry.pack(side="left", padx=5)
tk.Button(mqtt_frame, text="Connect", command=connect_mqtt).pack(side="left", padx=10)

athlete_frame = tk.Frame(root)
athlete_frame.pack(fill="x", pady=5)
athlete_label = tk.Label(athlete_frame, text="Selected: None", font=("Arial", 12))
athlete_label.pack(side="left", padx=10)
tk.Button(athlete_frame, text="Select Athlete", command=select_athlete).pack(side="left")

control_frame = tk.Frame(root)
control_frame.pack(pady=5)
start_button = tk.Button(control_frame, text="Start Session", command=start_session, bg="green", fg="white", font=("Arial", 12), state="disabled")
start_button.pack(side="left", padx=10)

reset_button = tk.Button(control_frame, text="Reset Session", command=reset_session, bg="orange", fg="black", font=("Arial", 12))
reset_button.pack(side="left", padx=10)

next_button = tk.Button(control_frame, text="Next Round", command=allow_next_timing, bg="purple", fg="white", font=("Arial", 12), state="disabled")
next_button.pack(side="left", padx=10)

save_button = tk.Button(control_frame, text="Save Results", command=save_results, bg="blue", fg="white", font=("Arial", 12), state="disabled")
save_button.pack(side="left", padx=10)


# 🔻 แบ่งซ้ายขวา Timing Results และ Log
main_content_frame = tk.Frame(root)
main_content_frame.pack(fill="both", expand=True, padx=10, pady=10)

left_frame = tk.Frame(main_content_frame)
left_frame.pack(side="left", fill="both", expand=True)

right_frame = tk.Frame(main_content_frame, width=300)
right_frame.pack(side="right", fill="y")

# ✅ Timing Results
result_frame = tk.LabelFrame(left_frame, text="Timing Results")
result_frame.pack(fill="both", expand=True)

result_tree = ttk.Treeview(result_frame, columns=("Round", "Time"), show="headings", height=10)

result_tree.heading("Round", text="Round", anchor="center")
result_tree.heading("Time", text="Time", anchor="center")

result_tree.column("Round", anchor="center", width=100)
result_tree.column("Time", anchor="center", width=200)

result_tree.pack(fill="both", expand=True)

# ✅ Log Box
log_label = tk.Label(right_frame, text="Log")
log_label.pack()
text_box = tk.Text(right_frame, height=30, width=40)
text_box.pack(fill="y", expand=True, padx=5)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
update_display_timer()
root.mainloop()