import paho.mqtt.client as mqtt

def on_message(client, userdata, message):
    data = message.payload.decode()
    if data == "PASS_A":
        print("✅ นักกีฬาผ่านจุด A")
    elif data == "PASS_B":
        print("✅ นักกีฬาผ่านจุด B")

client = mqtt.Client()
client.connect("192.168.100.189", 1883)  # ใช้ IP ของคอมพิวเตอร์
client.subscribe("test/sensorA")
client.subscribe("test/sensorB")
client.on_message = on_message

print("📡 MQTT Subscriber Running...")
client.loop_forever()
