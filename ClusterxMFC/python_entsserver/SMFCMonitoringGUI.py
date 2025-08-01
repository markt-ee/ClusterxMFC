import tkinter as tk
from tkinter import messagebox
from flask import Flask, jsonify
from flask import request
from soil_power_sensor_protobuf.proto import encode_response, decode_measurement
import csv
import time
import datetime
from prometheus_client import start_http_server, Gauge
import threading
import socket
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure 
from tkinter import simpledialog





def plot_csv():
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

        try:
            df = pd.read_csv(file_path)


            plt.figure(figsize=(10, 6))
            plt.plot(df['Timestamp'], df['Voltage (V)'], marker='o', linestyle='-', color='b')
            plt.ylabel('Voltage (V)')
            plt.xlabel('Timestamp')
            plt.title('Voltage v Time')
            plt.grid(True)
            plt.show()

        except Exception as e:
            messagebox.showinfo("test","An Error occured while reading file")




# Function to be called when Button 2 is clicked
def datastream():
    userfilename = simpledialog.askstring("Input", "Enter file name?", parent=root)
    timestamp = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")  # Example: "07APR2025_134755"
    csv_filename = f"C:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/ENTS_data_{timestamp}_{userfilename}.csv"
    messagebox.showinfo("Save File",csv_filename)

    #initialize new file 
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Voltage (V)", "Current (A)"])
    
    def log_excel(data):
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(data)
    

    #Definitions for Prometheus
    voltage_gauge = Gauge('soil_sensor_voltage', 'Voltage from soil sensor',['logger_id'])
    current_gauge = Gauge('soil_sensor_current', 'Current from soil sensor',['logger_id'])
    # Start HTTP server on port 8000 (Prometheus will scrape here)
    start_http_server(8000, addr='0.0.0.0')


    #main 
    app = Flask(__name__)

    @app.route('/api/', methods=['GET'])
    def health_check():
        return jsonify({"message": "API is running"}), 200  # Always return 200 if healthy

    @app.route('/data', methods=['POST'])
    def receive_data():
        data = request.data #data is raw in hex that requires decoding
        try:
            meas = decode_measurement(data, raw=False) #function from soil_power_protobuf to decode the message
            print(meas)
        except:
            log_excel("exception occured") 

        log_excel(meas)
        return jsonify({"message": "Data received"}), 200 #healthy
        #return

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)





# Function to be called when Button 2 is clicked
def potentiometer_test():
    messagebox.showinfo("Starting Data Stream", "Button 2 was clicked!")


# Create the main application window
root = tk.Tk()
root.title("SMFC Monitoring GUI Version X1")
root.geometry("300x200") # Set the window size (width x height)

#create buttons
button1 = tk.Button(root, text="Plot", command=plot_csv)
button1.pack(pady=10) # Add some padding

button2 = tk.Button(root, text="Start ENTs Data Stream", command=datastream)
button2.pack(pady=10) # Add some padding

button2 = tk.Button(root, text="ESP32 Potentiometer Test", command=potentiometer_test)
button2.pack(pady=10) # Add some padding

# Run the Tkinter event loop
root.mainloop()