#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiManager.h>  // ✅ ใช้ WiFi Manager ให้ผู้ใช้เลือก WiFi และใส่ MQTT Broker
#include <ArduinoJson.h>  // ✅ ใช้ JSON เพื่อรับค่าจาก Web Portal

WiFiClient espClient;
PubSubClient client(espClient);

// ✅ ค่าเริ่มต้นของ MQTT Broker (สามารถเปลี่ยนได้ผ่าน Web Portal)
String mqtt_server = "192.168.100.189";  

const int irSensorD = 2;  // ✅ เซ็นเซอร์ IR
const int buzzerPin = 13;    // กำหนดขา Buzzer (เปลี่ยนตามที่คุณต่อจริง)

// ✅ ฟังก์ชันเชื่อมต่อ MQTT
void connectMQTT() {
    client.setServer(mqtt_server.c_str(), 1883);
    while (!client.connected()) {
        Serial.print("Connecting to MQTT Broker: ");
        Serial.println(mqtt_server);
        if (client.connect("ESP32_D_Client")) {
            Serial.println("Connected to MQTT Broker!");
        } else {
            delay(2000);
        }
    }
}

// ✅ ฟังก์ชันแสดง Web Portal สำหรับให้ผู้ใช้เลือก WiFi และใส่ MQTT Broker
void setupWiFiAndMQTT() {
    WiFiManager wifiManager;

    // ✅ ตั้งให้เปิด Web Portal ทุกครั้งที่รีสตาร์ท
    wifiManager.resetSettings(); 

    // ✅ เพิ่มฟิลด์สำหรับให้ใส่ MQTT Broker
    WiFiManagerParameter mqtt_param("mqtt", "MQTT Broker IP", mqtt_server.c_str(), 40);
    wifiManager.addParameter(&mqtt_param);

    if (!wifiManager.startConfigPortal("ESP32-Setup #4D")) {
        Serial.println("Failed to connect. Restarting...");
        ESP.restart();
    }

    // ✅ อัปเดตค่า MQTT Broker ที่ผู้ใช้กรอก
    mqtt_server = mqtt_param.getValue();
    Serial.println("MQTT Server Set To: " + mqtt_server);
}

void setup() {
    Serial.begin(115200);

    setupWiFiAndMQTT();

    Serial.println("Connected to WiFi!");

    connectMQTT();
    
    pinMode(irSensorD, INPUT_PULLUP);  // ✅ ป้องกัน floating
    pinMode(buzzerPin, OUTPUT);
    digitalWrite(buzzerPin, HIGH);     // ✅ ปิดเสียงเริ่มต้น
}

void loop() {
    if (!client.connected()) {
        connectMQTT();
    }
    client.loop();

    int irState = digitalRead(irSensorD);
    Serial.println(irState);  // ✅ เช็กค่าจริง

    if (irState == LOW) {
        digitalWrite(buzzerPin, LOW);  // เปิดเสียง
        client.publish("fitness_test/athlete_status_D", "Passed");
    } else {
        digitalWrite(buzzerPin, HIGH); // ปิดเสียง
    }

    delay(100);
}
