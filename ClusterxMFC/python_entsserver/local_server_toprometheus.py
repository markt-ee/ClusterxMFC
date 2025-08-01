
from flask import Flask, jsonify
from flask import request
from soil_power_sensor_protobuf.proto import encode_response, decode_measurement
import csv
import time
import datetime
from prometheus_client import start_http_server, Gauge
import threading

import socket


#variables for ESP32 connection
ESP32_IP = "192.168.0.31"  # Replace with your ESP32's IP
PORT = 1234
timer_started = False

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ESP32_IP, PORT))
        s.sendall((cmd + '\n').encode())
        print(f"Sent: {cmd}")

# if __name__ == "__main__":
#     while True:
#         command = input("Enter command to send to ESP32: ")
#         if command.lower() == "exit":
#             break
#         send_command(command)



# function to run in the thread
def start_timer_pot(pot):
    global timer_started
    print("Voltage = 0.5 detected. Timer started for 20 minutes.")
    #send command to set potentiometer
    send_command(f"pot {pot}")
    time.sleep(5 * 60)  # # minutes delay
    timer_started = False
    print("Timer ended. Flag set to 1.")
    send_command("pot off") #need to debug why run twice
    send_command("pot off")
    time.sleep(2 * 60) #wait before next cycle


if not timer_started:
    timer_started = True
    threading.Thread(target=start_timer_pot(100), daemon=True).start()

#Generate CSV
# Generate a new filename with a timestamp
timestamp = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")  # Example: "07APR2025_134755"
csv_filename = f"C:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/ENTS_data_011_{timestamp}.csv"

# Initialize headers in CSV
def initialize_csv():
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Voltage (V)", "Current (A)"])
   
initialize_csv()
print(f"CSV initialized: {csv_filename}")


#Data Logging to CSV
def log_data(data):
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data['ts'], data['data']['voltage'], data['data']['current']])


#Send data to prometheus
# Define Prometheus metrics
voltage_gauge = Gauge('soil_sensor_voltage', 'Voltage from soil sensor')
current_gauge = Gauge('soil_sensor_current', 'Current from soil sensor')
# Start HTTP server on port 8000 (Prometheus will scrape here)
start_http_server(8000, addr='0.0.0.0')


#main 
app = Flask(__name__)

@app.route('/api/', methods=['GET'])
def health_check():
    return jsonify({"message": "API is running"}), 200  # Always return 200


@app.route('/data', methods=['POST'])
def receive_data():
    data = request.data
    #print("Received Data:", data) #raw data in some kind of hex that requires decoding
    meas = decode_measurement(data, raw=False) #uses function from soil_power_protobuf to decode the message
    print(meas)

    ts = meas['ts']
    voltage = meas['data']['voltage']
    current = meas['data']['current']
    
    # Update Prometheus metrics
    voltage_gauge.set(voltage)
    current_gauge.set(current)


    log_data(meas)  # Log new entry to excel file 
    print(f"Logged: TS: {ts}, Voltage: {voltage} V, Current: {current} A")


    # Voltage threshold trigger
    if voltage >= 0.490 and not timer_started:
        timer_started = True
        threading.Thread(target=start_timer_pot(100), daemon=True).start()


    return jsonify({"message": "Data received"}), 200
    #return

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


