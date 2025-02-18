import time
import paho.mqtt.client as mqtt
from tkinter import Tk, Label, StringVar

# กำหนดข้อมูล MQTT
mqtt_broker = "192.168.100.189"
mqtt_port = 1883
mqtt_topic_A = "fitness_test/athlete_status_A"
mqtt_topic_B = "fitness_test/athlete_status_B"

# ตั้งเวลาสำหรับแต่ละ Level (เวลาวิ่งจาก A ไป B และ B ไป A)
level_times = {
    1: 9,  # Level 1 มีเวลา 9 วินาที
    2: 8,  # Level 2 มีเวลา 8 วินาที
    3: 7,  # Level 3 มีเวลา 7 วินาที
    # เพิ่มเวลาสำหรับแต่ละ Level ตามต้องการ
}

current_level = 1
current_shuttle = 1

# สถานะการทดสอบ
athlete_status_A = False
athlete_status_B = False
test_running = False  # ตัวแปรเพื่อเช็คว่าการทดสอบกำลังดำเนินอยู่

# MQTT client setup
client = mqtt.Client()

# GUI setup
root = Tk()
root.title("Multi-stage Fitness Test")

level_label = Label(root, text=f"Level {current_level}", font=("Arial", 24))
level_label.pack(pady=20)

shuttle_label = Label(root, text=f"Shuttle {current_shuttle}", font=("Arial", 20))
shuttle_label.pack(pady=10)

status_var = StringVar()
status_var.set("Starting Test...")

status_label = Label(root, textvariable=status_var, font=("Arial", 16))
status_label.pack(pady=20)

time_var = StringVar()
time_var.set("Time Left: 0")

time_label = Label(root, textvariable=time_var, font=("Arial", 16))
time_label.pack(pady=10)

def on_message(client, userdata, msg):
    global athlete_status_A, athlete_status_B

    message = msg.payload.decode()
    print(f"Received message: {message} from topic: {msg.topic}")
    
    # ถ้านักกีฬาแค่ผ่าน A
    if msg.topic == mqtt_topic_A and message == "Passed":
        athlete_status_A = True
        print(f"Athlete passed A, status: {athlete_status_A}")

    # ถ้านักกีฬาแค่ผ่าน B
    if msg.topic == mqtt_topic_B and message == "Passed":
        athlete_status_B = True
        print(f"Athlete passed B, status: {athlete_status_B}")

def start_timer(level_time):
    global athlete_status_A, athlete_status_B, test_running
    
    # เริ่มเวลา
    start_time = time.time()
    time_left = level_time
    total_elapsed_time = 0

    while time_left > 0:
        # แสดงเวลาที่เหลือ
        elapsed_time = time.time() - start_time + total_elapsed_time
        time_left = level_time - int(elapsed_time)
        time_var.set(f"Time Left: {time_left}s")
        root.update()

        # ถ้าเวลาหมดหรือไม่ผ่านจุดใดจุดหนึ่งให้หยุดการทดสอบ
        if elapsed_time >= level_time:
            if not athlete_status_A or not athlete_status_B:
                stop_test()  # หยุดการทดสอบ
                break
            else:
                print(f"Level {current_level} Shuttle {current_shuttle} completed")
                break  # เริ่ม shuttle ถัดไป
        time.sleep(0.1)

    # หากเวลาหมด ตรวจสอบการผ่านจุด A และ B
    if elapsed_time >= level_time:
        if athlete_status_A and athlete_status_B:
            print(f"Athlete passed shuttle {current_shuttle} of Level {current_level}")
            status_var.set(f"Passed shuttle {current_shuttle} of Level {current_level}")
            # รีเซ็ตสถานะการผ่านจุด
            athlete_status_A = False
            athlete_status_B = False
            # เปลี่ยน shuttle หรือ level ถัดไป
            change_shuttle_or_level()
        else:
            # แจ้งเตือนเมื่อไม่ทันเวลา
            status_var.set(f"Failed to pass in time!")
            stop_test()  # หยุดการทดสอบ

def change_shuttle_or_level():
    global current_level, current_shuttle

    # เปลี่ยน shuttle ตามเวลาหมด
    if current_shuttle == 3:  # ตัวอย่างจำนวน Shuttle ต่อ Level
        current_shuttle = 1
        current_level += 1
        level_label.config(text=f"Level {current_level}")
        shuttle_label.config(text=f"Shuttle {current_shuttle}")
    else:
        current_shuttle += 1
        shuttle_label.config(text=f"Shuttle {current_shuttle}")
    
    # รีเซ็ตเวลาใหม่
    reset_timer_for_next_shuttle()

def reset_timer_for_next_shuttle():
    # รีเซ็ตเวลาหมายถึงการเริ่มต้นนับเวลาสำหรับ shuttle ใหม่
    level_time = level_times.get(current_level, 9)  # ค่าเริ่มต้น 9 วินาทีหากไม่พบ Level
    start_timer(level_time)  # เริ่มการนับถอยหลังเวลาใหม่

def stop_test():
    global test_running
    # หยุดการทดสอบ
    test_running = False
    status_var.set("Test Stopped")
    print("Test Stopped")
    client.disconnect()

def start_test():
    global test_running
    if not test_running:
        test_running = True
        # เริ่มทดสอบ
        print(f"Starting Level {current_level} Shuttle {current_shuttle}")
        status_var.set(f"Running Level {current_level} Shuttle {current_shuttle}")

        # รับเวลาที่กำหนดสำหรับ Level นั้นๆ
        level_time = level_times.get(current_level, 9)  # ค่าเริ่มต้น 9 วินาทีหากไม่พบ Level
        start_timer(level_time)

# เชื่อมต่อกับ MQTT Broker
def connect_mqtt():
    client.on_message = on_message
    client.connect(mqtt_broker, mqtt_port, 60)
    client.subscribe(mqtt_topic_A)
    client.subscribe(mqtt_topic_B)
    client.loop_start()

# เริ่มต้นการเชื่อมต่อ MQTT และเปิด GUI
connect_mqtt()

# เริ่มทดสอบโดยอัตโนมัติ
start_test()

root.mainloop()
