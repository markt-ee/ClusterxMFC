#ggenerate_dummy_data.py
# this function generates dummy data to sent to the api address in case the sensor doesnt work

import random
import time
import requests

def generate_dummy_data():
    """Generate random sensor data for testing."""
    return {
        "temperature": round(random.uniform(20, 30), 2),  # Random temp between 20-30°C
        "humidity": round(random.uniform(30, 70), 2),  # Random humidity between 30-70%
        "pressure": round(random.uniform(900, 1100), 2)  # Random pressure in hPa
    }

API_ENDPOINT = "http://192.168.2.5:5000/data"  # Change this to your actual local API


while True:
    data = generate_dummy_data()
    print("Sending data:", data)

    try:
        response = requests.post(API_ENDPOINT, json=data)
        print("Response:", response.status_code, response.text)
    except Exception as e:
        print("Failed to send data:", e)

    time.sleep(5)  # Send data every 5 seconds
