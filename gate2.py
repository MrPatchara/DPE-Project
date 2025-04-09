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



def update_display_timer():
    if running:
        now = time.time()
        if selected_athlete and selected_athlete["id"] in start_times:
            elapsed = int(now - start_times[selected_athlete["id"]])
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            current_display_time.set(f"{h:02}:{m:02}:{s:02}")
    root.after(500, update_display_timer)

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

def on_message(client, userdata, msg):
    global start_times, selected_athlete, running
    if not running:
        return

    topic = msg.topic
    payload = msg.payload.decode()

    if not selected_athlete:
        return

    aid = selected_athlete["id"]

    if topic.endswith("athlete_status_A"):
        start_times[aid] = time.time()
        log("Start timing...")

    elif topic.endswith("athlete_status_B"):
        if aid in start_times:
            end_time = time.time()
            duration = end_time - start_times[aid]
            del start_times[aid]

            if aid not in results:
                results[aid] = []

            results[aid].append(duration)
            update_result_table()
            log(f"Time: {duration:.2f} seconds")

# ----------------------------
# ฟังก์ชัน GUI
# ----------------------------
def log(text):
    text_box.insert(tk.END, text + "\n")
    text_box.see(tk.END)

def connect_mqtt():
    broker_ip = mqtt_ip_entry.get()
    client.connect(broker_ip, 1883)
    threading.Thread(target=client.loop_forever, daemon=True).start()

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
        result_tree.insert("", "end", values=(i, f"{t:.2f} sec"))

def save_results():
    all_results = []
    for aid, times in results.items():
        athlete = athlete_dict.get(str(aid))
        if athlete:
            all_results.append({
                "athlete_id": aid,
                "first_name": athlete["first_name"],
                "last_name": athlete["last_name"],
                "sport": athlete.get("sport", ""),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "timings": times
            })

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump({"results": all_results}, f, indent=4)

    messagebox.showinfo("Saved", "Results saved successfully.")

def start_session():
    global running
    if not selected_athlete:
        messagebox.showwarning("Warning", "Please select an athlete first.")
        return
    running = True
    log("Session started. Waiting for sensor triggers...")

def reset_session():
    global running, start_times, results
    running = False
    start_times = {}
    results = {}
    update_result_table()
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
        times = ", ".join([f"{t:.2f}s" for t in r.get("timings", [])])
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

# ----------------------------
# GUI Layout
# ----------------------------
root = tk.Tk()
root.title("Timing Gate System")
root.geometry("900x750")

# เพิ่ม: ตัวแปรจับเวลาแบบ realtime
current_display_time = tk.StringVar(value="00:00:00")
# 🔻 ป้ายไฟแบบ 7-segment
segment_frame = tk.Frame(root, bg="black")
segment_frame.pack(pady=10)
segment_label = tk.Label(segment_frame, textvariable=current_display_time, font=("Courier", 48), fg="red", bg="black")
segment_label.pack()

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

setting_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=setting_menu)
setting_menu.add_command(label="Manage Athletes", command=manage_athletes)

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
tk.Button(control_frame, text="Start Session", command=start_session, bg="green", fg="white", font=("Arial", 12)).pack(side="left", padx=10)
tk.Button(control_frame, text="Reset Session", command=reset_session, bg="orange", fg="black", font=("Arial", 12)).pack(side="left", padx=10)
tk.Button(control_frame, text="Save Results", command=save_results, bg="blue", fg="white", font=("Arial", 12)).pack(side="left", padx=10)

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

result_tree = ttk.Treeview(result_frame, columns=("Round", "Time"), show="headings")
result_tree.heading("Round", text="Round")
result_tree.heading("Time", text="Time")
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