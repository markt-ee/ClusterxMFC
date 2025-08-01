import paho.mqtt.client as mqtt
import json
import time
import random  # Just for simulating sensor data


# MQTT broker settings
broker = "192.168.0.156"  # or IP address like "192.168.1.100"
port = 1883
topic = "tele/esp32/SENSOR"

# Create a client instance
client = mqtt.Client()

# Connect to the broker
client.connect(broker, port)
client.loop_start()  # Start a background network thread

try:
    while True:
        # Simulate sensor data
        sensor_data = {
            "device_id": "soil-node-01",
            "voltage": round(random.uniform(0.7, 0.9), 2),
            "current": round(random.uniform(0.004, 0.006), 4),
            "timestamp": time.time()
        }

        # Convert to JSON
        payload = json.dumps(sensor_data)

        # Publish the message
        result = client.publish(topic, payload)

        # Print confirmation
        status = result[0]
        if status == 0:
            print(f"✅ Sent: {payload}")
        else:
            print(f"❌ Failed to send message")

        # Wait for 10 seconds
        time.sleep(10)

except KeyboardInterrupt:
    print("⛔ Stopped by user")

finally:
    client.loop_stop()
    client.disconnect()