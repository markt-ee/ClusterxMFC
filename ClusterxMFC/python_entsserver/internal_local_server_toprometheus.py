
from flask import Flask, jsonify
from flask import request
from soil_power_sensor_protobuf.proto import encode_response, decode_measurement
import csv
import time
import datetime
from prometheus_client import start_http_server, Gauge
import threading
import socket
import re
import sys

#ESP32______________________________________________________________________
#variables for ESP32 connection digital potentiometer
ESP32_IP = "192.168.2.21"  # MyCafe2.4
#ESP32_IP = "192.168.0.31" # TPLink_8FE0
PORT = 1234
timer_started = False
pot_list = [100, 50, 25, 10, 8, 6, 4, 2, 1, 0]
pot_count = 0
timer = 20

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ESP32_IP, PORT))
        s.sendall((cmd + '\n').encode())
        log_excel(f"Sent: {cmd}")

#to try to send command to esp32
# if __name__ == "__main__":
#     while True:
#         command = input("Enter command to send to ESP32: ")
#         if command.lower() == "exit":
#             break
#         send_command(command)

# function to run in the thread
def start_timer_pot(pot):
    global timer_started
    global timer
    log_excel(f"Voltage = 0.5 detected. Timer started for {timer} minutes.")

    #send command to set potentiometer
    send_command(f"pot {pot}")
    #log_excel("esp pot{pot}")

    time.sleep(timer * 60)  # # minutes delay
    timer_started = False
    log_excel("Timer ended. Flag set to 1.")
    send_command("pot off") #need to debug why run twice
    send_command("pot off")
    time.sleep(2 * 60) #wait before next cycle


#Generate CSV______________________________________________________________________________________
#Generate a new filename with a timestamp
userfilename = sys.argv[1]
timestamp = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")  # Example: "07APR2025_134755"
csv_filename = f"C:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/ENTS_data_{timestamp}.csv"
# Initialize headers in CSV
def initialize_csv():
    with open(userfilename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Voltage (V)", "Current (A)"])

#Data Logging to CSV
def log_excel(data):
    # with open(userfilename, mode='a', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(data)
    print(data)
    with open(userfilename, "a") as file:
        file.write(str(data) + "\n")
   
initialize_csv()
log_excel(f"Log file initialized for run {userfilename}")
log_excel(["TEST PROFILE_____________________\n pot increments: ", pot_count, "\ntimer:", timer, "\n" ])

#Prometheus setup
voltage_gauge = Gauge('soil_sensor_voltage', 'Voltage from soil sensor',['logger_id'])
current_gauge = Gauge('soil_sensor_current', 'Current from soil sensor',['logger_id'])
temperature_gauge = Gauge('soil_sensor_temperature', 'Current from soil sensor',['logger_id'])
humidity_gauge = Gauge('soil_sensor_humidity', 'Current from soil sensor',['logger_id'])

# Start HTTP server on port 8000 (Prometheus will scrape here)
start_http_server(8000, addr='0.0.0.0') #prometheus


#main repeating loop
app = Flask(__name__)

@app.route('/api/', methods=['GET'])
def health_check():
    return jsonify({"message": "API is running"}), 200  # Always return 200 if healthy


@app.route('/data', methods=['POST'])
def receive_data():
    data = request.data #data is raw in hex that requires decoding
    try:
        meas = decode_measurement(data, raw=False) #function from soil_power_protobuf to decode the message
        log_excel(meas)
        if meas['type'] == 'power':
            voltage = meas['data']['voltage']
            current = meas['data']['current']
            print("Voltage: ", voltage, " Current: ", current)
            #voltage_gauge.labels(logger_id=str(meas['loggerId'])).set(voltage)
            #current_gauge.labels(logger_id=str(meas['loggerId'])).set(current)
            #log_excel([voltage, current])

            # Voltage threshold trigger involving threading (background task)
            #if voltage >= 0.490 and not timer_started:
            global timer_started
            global pot_count
            global pot_list

            if not timer_started:
                log_excel("starting potentiometer")
                if (pot_count == len(pot_list)):
                    pot_count = 0
                timer_started = True
                threading.Thread(target=start_timer_pot(pot_list[pot_count]), daemon=True).start()
                pot_count = pot_count + 1
                log_excel(["pot count: ", pot_count])
    
        if meas['type'] == 'bme280':
            temperature = meas['data']['temperature']
            humidity = meas['data']['humidity']
            print("Temp: ", temperature, "Humidity: ", humidity, "\n")
            temperature_gauge.labels(logger_id=str(meas['loggerId'])).set(temperature)
            humidity_gauge.labels(logger_id=str(meas['loggerId'])).set(humidity)
            #log_excel([temperature, humidity])

    # except:
    #     print("exception occured")
    #     log_excel("exception occured") 
    #     return jsonify({"message": "exception occurred"}), 200 #exception occur but im just going to continue on anyway 

    except Exception as e:
        print("Exception occurred:", e)
        log_excel(["exception occurred", str(e)])
        return jsonify({"message": "exception occurred", "error": str(e)}), 500



    # ts = meas['ts']
    # voltage = meas['data']['voltage']
    # current = meas['data']['current']
    # temperature = meas['data']['temperature']
    # humidity = meas['data']['current']

    # print(voltage, current, temperature, humidity)
    
    # Use labels in Prometheus to track different boards
    # voltage_gauge.labels(logger_id=str(meas['loggerId'])).set(voltage)
    # current_gauge.labels(logger_id=str(meas['loggerId'])).set(current)
    # temperature_gauge.labels(logger_id=str(meas['loggerId'])).set(temperature)
    # humidity_gauge.labels(logger_id=str(meas['loggerId'])).set(humidity)

    #log_excel(meas)

    # print(f"Logged: TS: {ts}, Voltage: {voltage} V, Current: {current} A")

    return jsonify({"message": "Data received"}), 200
    #return

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) #this is the port that the ENTs sends to 


