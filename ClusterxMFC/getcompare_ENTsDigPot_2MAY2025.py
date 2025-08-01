import requests
import time

SERVER_URL = 'http://localhost:5000/latest'  # or replace localhost with ESP32/PC IP

def poll_latest_data():
    while True:
        try:
            response = requests.get(SERVER_URL)
            if response.status_code == 200:
                data = response.json()
                print(f"Timestamp: {data['ts']}, Voltage: {data['data']['voltage']} V, Current: {data['data']['current']} A")
            else:
                print("No new data available.")
        except Exception as e:
            print("Error fetching data:", e)
        
        time.sleep(2)  # Poll every 2 seconds

if __name__ == "__main__":
    poll_latest_data()
