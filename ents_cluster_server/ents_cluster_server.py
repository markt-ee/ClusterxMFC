from flask import Flask, jsonify, request
from soil_power_sensor_protobuf.proto import encode_response, decode_measurement
import csv
import time
import datetime
from prometheus_client import start_http_server, Gauge
import threading
import socket
import sys
import numpy as np

# ESP32 Configuration
#ESP32_IP = "192.168.0.31"
ESP32_IP = "192.168.0.30"

PORT = 1234
timer_started = False 
pot_list = [3,2,1,0]
v_pot_cycle_complete = np.zeros(len(pot_list)+2)
i_pot_cycle_complete = np.zeros(len(pot_list)+2)
pot_count = 0
timer = 20  # Timer duration in minutes
pot_threshold = 0.6
voltage = 0.0
current = 0.0


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
log_excel(pot_list)
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

def open_ckt():
    log_excel("open ckt potentiometer\n")
    send_command("pot off")
    send_command("pot off") #redudant call but need troubleshooting
    time.sleep(60)

#open ckt pot 
open_ckt()


def start_timer_pot(pot):
    global timer_started, timer, pot_cycle_complete, pot_count, voltage, current
    log_excel("Voltage threshold reached. Starting timer.")
    send_command("pot 1")
    time.sleep(2)
    send_command(f"pot {pot}")
    time.sleep(timer * 60)
    log_excel("Timer ended. Turning off potentiometer. Saving Potentiometer Cycle Voltage and Current Values")
    v_pot_cycle_complete[pot_count] = voltage
    i_pot_cycle_complete[pot_count] = current
    #log_excel(v_pot_cycle_complete)
    #log_excel(i_pot_cycle_complete)

    
    send_command("pot off")
    send_command("pot off") #redudant call but need troubleshooting
    time.sleep(60)
    timer_started = False

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
    global timer_started, pot_count, pot_list,pot_threshold, pot_cycle_complete, voltage,current
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

            if (voltage>pot_threshold) and (not timer_started):
                log_excel("f{voltage} detected above {pot_threshold} Starting potentiometer adjustment thread")
                if pot_count >= len(pot_list):
                    pot_count = 0
                    print(v_pot_cycle_complete)
                    print(i_pot_cycle_complete)
                    v_pot_cycle_complete = np.zeros(len(pot_list))
                    i_pot_cycle_complete = np.zeros(len(pot_list))
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
