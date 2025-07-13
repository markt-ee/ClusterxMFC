from flask import Flask, jsonify, request
from soil_power_sensor_protobuf.proto import encode_response, decode_measurement
import csv
import time
import datetime
from prometheus_client import start_http_server, Gauge
import threading
import socket
import sys

# ESP32 Configuration
ESP32_IP = "192.168.2.31"
PORT = 1234
timer_started = True #disable timer stuff for now
pot_list = [100, 50, 25, 10, 8, 6, 4, 2, 1, 0]
pot_count = 0
timer = 20  # Timer duration in minutes

# Logging Setup
userfilename = sys.argv[1]
timestamp = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")
csv_filename = f"C:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/ENTS_data_{timestamp}.csv"
savefile = "ents_cluster_server_" + f"{timestamp}_" + userfilename + ".csv"

def initialize_csv():
    with open(savefile, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Voltage (V)", "Current (A)"])

def log_excel(data):
    log_entry = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {str(data)}"
    print(log_entry)
    with open(savefile, "a") as file: 
        file.write(log_entry + "\n")

initialize_csv()
log_excel(f"Log file initialized: {userfilename}")
log_excel(["TEST PROFILE", f"Pot increments: {len(pot_list)}", f"Timer: {timer} min"])
log_excel("--------------------------------------------------")

# ESP32 Communication
def send_command(cmd):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ESP32_IP, PORT))
            s.sendall((cmd + '\n').encode())
            log_excel(f"Sent to ESP32: {cmd}")
    except Exception as e:
        log_excel(f"Failed to send command: {cmd} | Error: {e}")

def start_timer_pot(pot):
    global timer_started, timer
    log_excel("Voltage threshold reached. Starting timer.")

    send_command(f"pot {pot}")
    time.sleep(timer * 60)
    timer_started = False
    log_excel("Timer ended. Turning off potentiometer.")
    send_command("pot off")
    send_command("pot off")  # Redundant call (can be debugged)
    time.sleep(2*60)

# Prometheus Metrics
voltage_gauge = Gauge('soil_sensor_voltage', 'Voltage from soil sensor', ['logger_id'])
current_gauge = Gauge('soil_sensor_current', 'Current from soil sensor', ['logger_id'])
temperature_gauge = Gauge('soil_sensor_temperature', 'Temperature from BME280', ['logger_id'])
humidity_gauge = Gauge('soil_sensor_humidity', 'Humidity from BME280', ['logger_id'])
start_http_server(8000, addr='0.0.0.0')

# Flask App Setup
app = Flask(__name__)

@app.route('/api/', methods=['GET'])
def health_check():
    return jsonify({"message": "API is running"}), 200

@app.route('/data', methods=['POST'])
def receive_data():
    global timer_started, pot_count, pot_list
    data = request.data

    try:
        meas = decode_measurement(data, raw=False)
        log_excel(f"Received data: {meas}")

        if meas['type'] == 'power':
            voltage = meas['data']['voltage']
            current = meas['data']['current']
            logger_id = str(meas['loggerId'])

            log_excel(f"Voltage: {voltage:.3f} V | Current: {current:.6f} A")
            voltage_gauge.labels(logger_id=logger_id).set(voltage)
            current_gauge.labels(logger_id=logger_id).set(current)

            if not timer_started:
                log_excel("Starting potentiometer adjustment thread")
                if pot_count >= len(pot_list):
                    pot_count = 0
                timer_started = True
                threading.Thread(
                    target=start_timer_pot, args=(pot_list[pot_count],), daemon=True
                ).start()
                pot_count += 1
                log_excel(f"Next pot value index: {pot_count}")

        elif meas['type'] == 'bme280':
            temperature = meas['data']['temperature']
            humidity = meas['data']['humidity']
            logger_id = str(meas['loggerId'])

            log_excel(f"Temperature: {temperature:.2f} C | Humidity: {humidity:.2f} %")
            temperature_gauge.labels(logger_id=logger_id).set(temperature)
            humidity_gauge.labels(logger_id=logger_id).set(humidity)

        return jsonify({"message": "Data received"}), 200

    except Exception as e:
        error_msg = f"Exception occurred while decoding: {e}"
        print(error_msg)
        log_excel(error_msg)
        return jsonify({"message": "Exception occurred", "error": str(e)}), 500

# Run Server
if __name__ == '__main__':
    log_excel("Flask server starting on port 5000...")
    app.run(host='0.0.0.0', port=5000)
