import json
import time
import hashlib
import paho.mqtt.client as mqtt



topic = "/sensor_data"
# Connect to the broker
client = mqtt.Client()
client.connect("192.168.2.5", 1883, 60) #this is the IP of this PC, why do we have to set it?
#client.connect("localhost", 1883, 60)
client.loop_start()

time.sleep(1)



def generate_dummy_data():
    # Simulated sensor reading
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "voltage": 0.55,
        "current": 0.0015
    }
    
    # Add checksum (SHA256 of JSON string before adding checksum)
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    checksum = hashlib.sha256(raw_json.encode()).hexdigest()
    payload["checksum"] = checksum
    return json.dumps(payload)

# Periodically publish dummy data
try:
    while True:
        message = generate_dummy_data()
        print("Publishing:", message)
        client.publish(topic, message, qos=1)
        time.sleep(5)  # every 5 seconds
except KeyboardInterrupt:
    print("Stopped by user")
