
from flask import Flask, jsonify
from flask import request
from soil_power_sensor_protobuf.proto import encode_response, decode_measurement
import csv
import time
import datetime

# Generate a new filename with a timestamp
timestamp = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")  # Example: "07APR2025_134755"
csv_filename = f"C:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/ENTS_data_{timestamp}.csv"

# Initialize headers in CSV
def initialize_csv():
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Voltage (V)", "Current (A)"])

   
initialize_csv()
print(f"CSV initialized: {csv_filename}")     

def log_data(data):
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data['ts'], data['data']['voltage'], data['data']['current']])

app = Flask(__name__)

@app.route('/api/', methods=['GET'])
def health_check():
    return jsonify({"message": "API is running"}), 200  # Always return 200


@app.route('/data', methods=['POST'])
def receive_data():
    data = request.data
    #print("Received Data:", data) #raw data in some kind of hex that requires decoding
    meas = decode_measurement(data, raw=False) #uses function from soil_power_protobuf to decode the message
    ts = meas['ts']
    voltage = meas['data']['voltage']
    current = meas['data']['current']

    log_data(meas)  # Log new entry
    print(f"Logged: TS: {ts}, Voltage: {voltage} V, Current: {current} A")

    return jsonify({"message": "Data received"}), 200
    #return

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

