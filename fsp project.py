pip install paho-mqtt
import time
import json
import random
import paho.mqtt.client as mqtt

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 8000  # HiveMQ WebSocket port
POLE_ID = "Pole_001"
TOPIC_PUBLISH_DATA = f"smartcity/streetlights/{POLE_ID}/data"
TOPIC_SUBSCRIBE_CONTROL = f"smartcity/streetlights/{POLE_ID}/control"

pole_state = {
    "manual_override": False,
    "lamp_status": "OFF",
    "brightness": 0
}

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe(TOPIC_SUBSCRIBE_CONTROL)

def on_message(client, userdata, msg):
    global pole_state
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        if payload.get("command") == "FORCE_ON":
            pole_state.update({"manual_override": True, "lamp_status": "ON", "brightness": 100})
        elif payload.get("command") == "FORCE_OFF":
            pole_state.update({"manual_override": True, "lamp_status": "OFF", "brightness": 0})
        elif payload.get("command") == "AUTO":
            pole_state["manual_override"] = False
    except Exception:
        pass

def read_ldr_sensor():
    return random.randint(0, 1023)

def calculate_adaptive_lighting(ldr_value):
    if ldr_value > 800:
        return "OFF", 0
    elif ldr_value < 300:
        return "ON", 100
    else:
        return "ON", int(((800 - ldr_value) / 500) * 100)

def main():
    # Use VERSION2 and transport="websockets" for Google Colab compatibility
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, POLE_ID, transport="websockets")
    client.on_connect = on_connect
    client.on_message = on_message

    # Increased timeout slightly for websocket handshake
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    try:
        while True:
            ldr_value = read_ldr_sensor()

            if not pole_state["manual_override"]:
                status, brightness = calculate_adaptive_lighting(ldr_value)
                pole_state.update({"lamp_status": status, "brightness": brightness})

            sensor_data = {
                "pole_id": POLE_ID,
                "ldr_value": ldr_value,
                "lamp_status": pole_state["lamp_status"],
                "brightness_percentage": pole_state["brightness"],
                "mode": "MANUAL" if pole_state["manual_override"] else "AUTO",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            client.publish(TOPIC_PUBLISH_DATA, json.dumps(sensor_data))
            print(f"[{time.strftime('%H:%M:%S')}] LDR: {ldr_value} | Mode: {sensor_data['mode']} | Lamp: {pole_state['lamp_status']} at {pole_state['brightness']}%")

            time.sleep(0.5)

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()

    import paho.mqtt.client as mqtt
import json

# Command options: "FORCE_ON", "FORCE_OFF", "AUTO"
command_payload = json.dumps({"command": "FORCE_ON"})
mqtt.Client().publish("smartcity/streetlights/Pole_001/control", command_payload, hostname="broker.hivemq.com")
print("Command sent to pole!")