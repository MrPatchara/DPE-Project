import tkinter as tk
from tkinter import ttk, messagebox
import time, json, datetime
import paho.mqtt.client as mqtt
from tkinter import simpledialog, filedialog
from PIL import Image, ImageTk
import os

# ---------- CONFIG ----------
MQTT_TOPIC_START = "fitness_test/athlete_status_A"
MQTT_TOPIC_STOP = "fitness_test/athlete_status_B"
MQTT_BROKER_IP = "192.168.100.189"
RAST_RESULT_FILE = "rast_results.json"
ATHLETE_FILE = "athletes.json"
MAX_SPRINTS = 6

# ---------- GLOBALS ----------
mqtt_client = mqtt.Client()
sprint_times = []
start_time = None
selected_athlete = None
sensor_vars = {}
current_sprint = 0
recovery_time = 10  # seconds

# ---------- MQTT CALLBACK ----------
def on_message(client, userdata, msg):
    global start_time
    topic = msg.topic
    if topic == MQTT_TOPIC_START:
        start_sprint()
    elif topic == MQTT_TOPIC_STOP:
        stop_sprint()

def connect_mqtt():
    try:
        mqtt_client.on_message = on_message
        mqtt_client.connect(mqtt_ip.get(), 1883)
        mqtt_client.subscribe("fitness_test/#")
        mqtt_client.loop_start()
        messagebox.showinfo("MQTT", "Connected to broker")
    except Exception as e:
        messagebox.showerror("MQTT Error", str(e))

# ---------- ATHLETE DATABASE ----------
def load_athletes():
    if not os.path.exists(ATHLETE_FILE): return []
    with open(ATHLETE_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("athletes", [])

def save_athletes(athletes):
    with open(ATHLETE_FILE, "w", encoding="utf-8") as f:
        json.dump({"athletes": athletes}, f, indent=4)

def select_athlete():
    global selected_athlete
    athletes = load_athletes()
    if not athletes:
        messagebox.showwarning("No athletes", "Please add an athlete first.")
        return
    win = tk.Toplevel(root)
    win.title("Select Athlete")
    listbox = tk.Listbox(win, font=("Arial", 12))
    listbox.pack(fill="both", expand=True, padx=10, pady=10)
    for athlete in athletes:
        listbox.insert(tk.END, f"{athlete['first_name']} {athlete['last_name']}")

    def confirm():
        index = listbox.curselection()
        if not index: return
        selected_athlete = athletes[index[0]]
        selected_label.config(text=f"Selected: {selected_athlete['first_name']} {selected_athlete['last_name']}")
        win.destroy()

    tk.Button(win, text="Select", command=confirm).pack(pady=10)

def manage_athletes():
    athletes = load_athletes()
    def save():
        save_athletes(athletes)
        refresh()

    def refresh():
        listbox.delete(0, tk.END)
        for a in athletes:
            listbox.insert(tk.END, f"{a['first_name']} {a['last_name']}")

    def add():
        first = simpledialog.askstring("First Name", "Enter first name")
        last = simpledialog.askstring("Last Name", "Enter last name")
        if first and last:
            id_ = str(max([int(a['id']) for a in athletes], default=0) + 1)
            athletes.append({"id": id_, "first_name": first, "last_name": last})
            save()

    def delete():
        idx = listbox.curselection()
        if not idx: return
        del athletes[idx[0]]
        save()

    win = tk.Toplevel(root)
    win.title("Manage Athletes")
    listbox = tk.Listbox(win, font=("Arial", 12))
    listbox.pack(fill="both", expand=True, padx=10, pady=10)
    btn_frame = tk.Frame(win)
    btn_frame.pack()
    tk.Button(btn_frame, text="Add", command=add).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Delete", command=delete).pack(side="left", padx=5)
    refresh()

def sensor_setting():
    win = tk.Toplevel(root)
    win.title("Sensor Settings")
    tk.Label(win, text="Select exactly 2 sensors:", font=("Arial", 12)).pack(pady=5)
    sensor_frame = tk.Frame(win)
    sensor_frame.pack()

    def validate():
        selected = [k for k, v in sensor_vars.items() if v.get()]
        if len(selected) != 2:
            messagebox.showerror("Error", "Please select exactly 2 sensors.")
        else:
            messagebox.showinfo("OK", f"Selected Sensors: {', '.join(selected)}")
            win.destroy()

    for i in range(10):
        code = chr(65 + i)  # A, B, C...
        sensor_vars[code] = tk.BooleanVar()
        tk.Checkbutton(sensor_frame, text=f"Sensor {code}", variable=sensor_vars[code]).grid(row=i//5, column=i%5, sticky="w", padx=10)

    tk.Button(win, text="Confirm", command=validate).pack(pady=10)

# ---------- RAST FUNCTIONS ----------
def run_full_rast_test():
    global current_sprint, start_time

    if current_sprint >= MAX_SPRINTS:
        return  # หยุดทันทีถ้าครบ 6 รอบแล้ว

    current_sprint += 1
    timer_label.config(text=f"SPRINT {current_sprint}", fg="red")
    start_time = time.time()
    update_timer()

    def finish_sprint():
        global start_time
        if start_time:
            elapsed = time.time() - start_time
            sprint_times.append(elapsed)
            update_listbox()
            start_time = None

            if current_sprint < MAX_SPRINTS:
                start_recovery_timer(recovery_time)
            else:
                timer_label.config(text="Test Complete!", fg="green")
                messagebox.showinfo("RAST", "All 6 sprints completed.\nPlease save or reset the result.")

    root.after(6000, finish_sprint)  # จำกัดเวลาสูงสุดของการวิ่งในแต่ละรอบ


def start_recovery_timer(seconds):
    if seconds > 0:
        timer_label.config(text=f"Recovery: {seconds} s", fg="blue")
        root.after(1000, lambda: start_recovery_timer(seconds - 1))
    else:
        timer_label.config(text="GO!", fg="green")
        root.after(1000, run_full_rast_test)

def start_full_test():
    global current_sprint, sprint_times
    current_sprint = 0
    sprint_times = []
    update_listbox()
    run_full_rast_test()

def start_sprint():
    global start_time
    if len(sprint_times) >= MAX_SPRINTS:
        return
    start_time = time.time()
    update_timer()

def stop_sprint():
    global start_time
    if start_time:
        elapsed = time.time() - start_time
        sprint_times.append(elapsed)
        start_time = None
        update_listbox()
        if len(sprint_times) == MAX_SPRINTS:
            messagebox.showinfo("RAST", "All 6 sprints completed.")

def update_timer():
    if start_time:
        elapsed = time.time() - start_time
        timer_label.config(text=f"{elapsed:.4f}")
        root.after(10, update_timer)
    else:
        timer_label.config(text="0.0000")

def update_listbox():
    listbox.delete(0, tk.END)
    for i, t in enumerate(sprint_times, 1):
        listbox.insert(tk.END, f"Sprint {i}: {t:.4f} sec")

def reset():
    global sprint_times, start_time
    sprint_times = []
    start_time = None
    update_listbox()
    timer_label.config(text="0.0000")

def save_result():
    if not selected_athlete:
        messagebox.showerror("Error", "Please select an athlete.")
        return
    if len(sprint_times) < MAX_SPRINTS:
        messagebox.showerror("Error", "Not enough sprints.")
        return

    distance = 35
    weight = float(selected_athlete.get("weight", 70))
    powers = [(weight * distance ** 2) / (t ** 3) for t in sprint_times]
    peak = max(powers)
    avg = sum(powers) / len(powers)
    fatigue = (peak - min(powers)) / peak * 100

    result = {
        "athlete_id": selected_athlete["id"],
        "first_name": selected_athlete["first_name"],
        "last_name": selected_athlete["last_name"],
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "test_type": "RAST test",
        "sprint_times": sprint_times,
        "peak_power": round(peak, 2),
        "average_power": round(avg, 2),
        "fatigue_index": round(fatigue, 2)
    }

    try:
        with open(RAST_RESULT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = {"results": []}

    data["results"].append(result)

    with open(RAST_RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    messagebox.showinfo("Saved", "RAST result saved.")
    reset()

def set_distance():
    def confirm():
        try:
            val = float(entry.get())
            if val > 0:
                distance_var.set(val)
                messagebox.showinfo("Distance Set", f"Distance set to {val:.2f} meters.")
                win.destroy()
            else:
                messagebox.showerror("Invalid", "Distance must be positive.")
        except:
            messagebox.showerror("Invalid", "Please enter a valid number.")

    win = tk.Toplevel(root)
    win.title("Set Distance")
    tk.Label(win, text="Enter Sprint Distance (meters):", font=FONT).pack(pady=10)
    entry = tk.Entry(win, font=FONT)
    entry.insert(0, str(distance_var.get()))
    entry.pack(pady=5)
    tk.Button(win, text="Confirm", font=FONT, command=confirm).pack(pady=10)
def view_rast_results():
    try:
        with open(RAST_RESULT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            results = data.get("results", [])
    except:
        messagebox.showerror("Error", "Failed to load RAST results.")
        return

    # จัดเรียงตามวันที่ (ล่าสุดก่อน)
    results.sort(key=lambda r: r["date"], reverse=True)

    win = tk.Toplevel(root)
    win.title("RAST Test History")
    win.geometry("800x400")

    tree = ttk.Treeview(win, columns=("Date", "Name", "Peak", "Fatigue"), show="headings")
    tree.heading("Date", text="Date")
    tree.heading("Name", text="Name")
    tree.heading("Peak", text="Peak Power (W)")
    tree.heading("Fatigue", text="Fatigue Index")

    tree.column("Date", width=150)
    tree.column("Name", width=200)
    tree.column("Peak", width=150)
    tree.column("Fatigue", width=150)

    for i, r in enumerate(results):
        name = f"{r['first_name']} {r['last_name']}"
        tree.insert("", "end", iid=i, values=(r["date"], name, r["peak_power"], r["fatigue_index"]))

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def view_selected():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Please select a result to view.")
            return
        view_result_detail(results[int(selected)])

    def delete_selected():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Please select a result to delete.")
            return
        confirm = messagebox.askyesno("Delete", "Are you sure to delete this result?")
        if confirm:
            del results[int(selected)]
            with open(RAST_RESULT_FILE, "w", encoding="utf-8") as f:
                json.dump({"results": results}, f, indent=4)
            tree.delete(selected)
            messagebox.showinfo("Deleted", "Result deleted successfully.")

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="View Selected", command=view_selected, width=15).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Delete Selected", command=delete_selected, width=15).pack(side="left", padx=10)
    
def view_result_detail(result):
    win = tk.Toplevel(root)
    win.title("Result Detail")
    win.geometry("600x600")

    name = f"{result['first_name']} {result['last_name']}"
    date = result['date']
    weight = float(result.get("weight", 70))
    distance = float(result.get("distance", 35))
    times = result["sprint_times"]

    powers = [(weight * distance ** 2) / (t ** 3) for t in times]
    peak = max(powers)
    relative = peak / weight
    avg = sum(powers) / len(powers)
    fatigue = (peak - min(powers)) / sum(times)

    summary = f"Name: {name}\nDate: {date}\nWeight: {weight:.1f} kg\nDistance: {distance:.1f} m\n\n"
    summary += "Sprint Times & Power:\n"
    for i, (t, p) in enumerate(zip(times, powers), 1):
        summary += f"  [{i}] {t:.2f} s → {p:.2f} W\n"

    summary += f"\nPeak Power       : {peak:.2f} W"
    summary += f"\nRelative Peak    : {relative:.2f} W/kg"
    summary += f"\nAverage Power    : {avg:.2f} W"
    summary += f"\nFatigue Index    : {fatigue:.4f}"

    tk.Label(win, text="RAST Test Result", font=("Arial", 16, "bold")).pack(pady=10)
    text = tk.Text(win, font=("Courier New", 12), width=60, height=25)
    text.pack(padx=10, pady=10)
    text.insert("1.0", summary)
    text.config(state="disabled")

# ---------- GUI SETUP ----------
root = tk.Tk()
root.title("RAST Test")
root.state("zoomed")  # ✅ เต็มหน้าจอ

FONT = ("Arial", 16)
BIG_FONT = ("DS-Digital", 80)

mqtt_ip = tk.StringVar(value=MQTT_BROKER_IP)
distance_var = tk.DoubleVar(value=35.0)

# ---------- Menu Bar ----------
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

setting_menu = tk.Menu(menu_bar, tearoff=0)
setting_menu.add_command(label="Manage Athletes", command=manage_athletes)
setting_menu.add_command(label="Sensor Settings", command=sensor_setting)
setting_menu.add_command(label="Set Distance", command=set_distance)

menu_bar.add_cascade(label="Settings", menu=setting_menu)
result_menu = tk.Menu(menu_bar, tearoff=0)
result_menu.add_command(label="View RAST Results", command=view_rast_results)
menu_bar.add_cascade(label="Result", menu=result_menu)

# ---------- Title ----------
title_label = tk.Label(root, text="Running Based Anaerobic Sprint Test (RAST)", font=("Arial", 20, "bold"))
title_label.pack(pady=(20, 10))

# ---------- Timer Display ----------
timer_label = tk.Label(root, text="0.0000", font=BIG_FONT, fg="red")
timer_label.pack(pady=40)

# ---------- Athlete Selection ----------
selected_label = tk.Label(root, text="Selected Athlete: None", font=FONT)
selected_label.pack(pady=10)

tk.Button(root, text="Select Athlete", command=select_athlete, font=FONT, width=20).pack(pady=5)

# ---------- MQTT Connection ----------
mqtt_frame = tk.Frame(root, pady=10)
mqtt_frame.pack()
tk.Label(mqtt_frame, text="MQTT Broker IP:", font=FONT).pack(side="left", padx=10)
tk.Entry(mqtt_frame, textvariable=mqtt_ip, font=FONT, width=25).pack(side="left", padx=10)
tk.Button(mqtt_frame, text="Connect", command=connect_mqtt, font=FONT).pack(side="left", padx=10)

# ---------- Sprint Result Listbox ----------
listbox = tk.Listbox(root, font=FONT, height=8, width=40, justify="center")
listbox.pack(pady=30)

# ---------- Control Buttons ----------
btn_frame = tk.Frame(root, pady=20)
btn_frame.pack()

tk.Button(btn_frame, text="Start Test", command=start_full_test, bg="orange", font=FONT, width=14).pack(side="left", padx=20)
tk.Button(btn_frame, text="Reset", command=reset, bg="red", fg="white", font=FONT, width=14).pack(side="left", padx=20)
tk.Button(btn_frame, text="Save Result", command=save_result, bg="green", fg="white", font=FONT, width=14).pack(side="left", padx=20)

root.mainloop()

