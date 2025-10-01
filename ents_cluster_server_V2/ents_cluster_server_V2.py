#!/usr/bin/env python3
"""
ents_cluster_server_V2
Released on 10/1/2025
Maria Katherine 


upgraded version of X3 with multipot, multi ents capabilities
Features:
- Per-logger cycle arrays and counters
- start_timer_pot runs a pot step in a daemon thread
- Thread-safety via per-logger lock
- MQTT publishes at key points
- PNG plotting on cycle completion
- Prometheus metrics, Flask endpoints, CSV logging

Missing:
- capability to start potentiometer test from iOS app
"""

from pathlib import Path
import csv
import sys
import time
import json
import socket
import hashlib
import threading
import datetime
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt

from flask import Flask, jsonify, request
from prometheus_client import start_http_server, Gauge
from soil_power_sensor_protobuf.proto import decode_measurement

# -------------------------
# Configuration
# -------------------------
POT_LIST = [80, 40, 11, 8, 6,  5, 4, 3, 2, 1]
TIMER_MINUTES = 1
ESP_PORT = 1234

# CSV / file locations
USER_FILENAME = sys.argv[1] if len(sys.argv) > 1 else "default"
TIMESTAMP_STR = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")
SAVEFILE = f"entscluster_X3_{TIMESTAMP_STR}_{USER_FILENAME}.csv"
FILEDIR = Path("C:/Users/kathe/Desktop/ClusterxSMFC/ClusterxMFC/python_entsserver/ents_cluster_server_V2")
FILEDIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = FILEDIR / SAVEFILE

# MQTT broker
# MQTT_BROKER = "192.168.2.5"
# MQTT_PORT = 1883

#Lab MQTT Setup
MQTT_BROKER = "192.168.0.157"
MQTT_PORT = 1883

# Prometheus
start_http_server(8000, addr="0.0.0.0")

# Global mobile toggle (controlled by mobile app)
pot0_en = True  # If False, cancel/disable pot runs triggered by mobile

# -------------------------
# Helper logging functions
# -------------------------
def initialize_csv():
    with open(CSV_PATH, mode="w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Timestamp", "local ts", "logger id", "Current", "Voltage", "Temperature", "Humidity", "Power (mW)", "Log", "error"])

def log_excel(data):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {data}"
    print(entry)
    with open(CSV_PATH, mode="a", newline="") as f:
        w = csv.writer(f)
        w.writerow(["", "", "", "", "", "", "", "", entry])

def log_vi(meas):
    with open(CSV_PATH, mode="a", newline="") as f:
        w = csv.writer(f)
        w.writerow([TIMESTAMP_STR, meas.get("ts", ""), meas.get("loggerId", ""), meas["data"].get("current", ""), meas["data"].get("voltage", "")])

def log_th(meas):
    with open(CSV_PATH, mode="a", newline="") as f:
        w = csv.writer(f)
        w.writerow([TIMESTAMP_STR, meas.get("ts", ""), meas.get("loggerId", ""), "", "", meas["data"].get("temperature", ""), meas["data"].get("humidity", "")])

# -------------------------
# EntsLogger class
# -------------------------
class EntsLogger:
    def __init__(self, id, module, pot_ip, pot_en=False, mppt_en=False, pot_count=0, ocv=0.5, v=0.0, i=0.0, h = 0.0, t = 0.0, vpot_array=None, ipot_array=None):
        self.id = id
        self.module = module
        self.pot_ip = pot_ip
        self.pot_en = pot_en            # whether pot is currently enabled
        self.mppt_en = mppt_en          # whether mppt/pot test is allowed
        self.pot_count = pot_count      # index into POT_LIST
        self.ocv = ocv
        self.v = v                      # last voltage (V)
        self.i = i   
        self.h = h
        self.t = t                   # last current (A)
        n = len(POT_LIST)
        self.vpot_array = np.zeros(n) if vpot_array is None else vpot_array
        self.ipot_array = np.zeros(n) if ipot_array is None else ipot_array
        self.lock = threading.Lock()    # protects vpot/ipot/pot_count
        self.timer_running = False      # guard against concurrent start_timer_pot threads
        self.continuous = False         # if True, run cycles continuously

    def __repr__(self):
        return f"EntsLogger(id={self.id}, module={self.module}, ip={self.pot_ip})"

# -------------------------
# Create logger instances and map
# -------------------------
ents11 = EntsLogger(11, "Hans",  "192.168.2.24", pot_en=False, mppt_en=True, ocv=0.6)
ents12 = EntsLogger(12, "Chewy",  "192.168.2.29", pot_en=False, mppt_en=True, ocv=0.6)
#ents13 = EntsLogger(13, "Hans", "192.168.2.29", pot_en=False, mppt_en=False, ocv= 0.6)
ents15 = EntsLogger(15, "Luke",  "192.168.2.24", pot_en=False, mppt_en=False, ocv=0.6)



#At Lab Setup
ents13 = EntsLogger(13, "Leia",  "192.168.0.147", pot_en=False, mppt_en=True, ocv=0.6)


ENTS_MAP = {str(l.id): l for l in (ents11, ents12, ents13, ents15)}

# -------------------------
# Networking: send command to ESP (digipot)
# -------------------------
def send_command(cmd, ip, max_attempts=5, port=ESP_PORT, timeout=1):
    """Send a single-line command to an ESP device with retries."""
    for attempt in range(1, max_attempts + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((ip, port))
                s.sendall((cmd + "\n").encode())
                try:
                    reply = s.recv(1024).decode().strip()
                    if reply:
                        log_excel(f"Reply from {ip}: {reply}")
                except socket.timeout:
                    pass
            log_excel(f"Sent to {ip}: {cmd}")
            return True
        except Exception as e:
            log_excel(f"Attempt {attempt} failed for {ip}: {cmd} | Error: {e}")
            if attempt < max_attempts:
                time.sleep(1)
    log_excel(f"Failed to send command to {ip} after {max_attempts} attempts.")
    return False

# -------------------------
# MQTT
# -------------------------
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

def generate_mqtt_data(logger: EntsLogger):
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "logger_id": logger.id,
        "module": logger.module,
        "voltage": float(logger.v),
        "current": float(logger.i),
        "humidity": float(logger.h),
        "temperature":float(logger.t),
        "v_pot_complete": str(logger.vpot_array),
        "i_pot_complete": str(logger.ipot_array)

        #"v_pot_complete": list(map(float, logger.vpot_array.tolist())), instead of str() and then parse 
        #"i_pot_complete": list(map(float, logger.ipot_array.tolist()))
    }
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    checksum = hashlib.sha256(raw_json.encode()).hexdigest()
    payload["checksum"] = checksum
    return json.dumps(payload)

# -------------------------
# Plotting
# -------------------------
def generate_png(currents_mA, voltages_mV, power_uW, logger: EntsLogger):
    timestamp_local = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(currents_mA, voltages_mV, marker='o', linestyle='-', color='blue', label='Voltage')
    ax1.set_xlabel("Current (mA)")
    ax1.set_ylabel("Voltage (mV)")
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(currents_mA, power_uW, marker='s', linestyle='-', color='red', label='Power')
    ax2.set_ylabel("Power (uW)")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="best")

    title = f"MudWatt Polarization Curve {POT_LIST}, {TIMER_MINUTES} min, logger {logger.id} ({logger.module})"
    fig.suptitle(title)

    png_path = FILEDIR / f"{logger.id}_polarization_{TIMER_MINUTES}mins_{logger.ocv}_{timestamp_local}_{USER_FILENAME}.png"
    plt.savefig(png_path, format="png", dpi=300)
    plt.close()
    log_excel(f"Plot saved to: {png_path}")

# -------------------------
# start_timer_pot: main function you flagged as missing
# -------------------------
def start_timer_pot(pot_index: int, pot_value: int, logger: EntsLogger):
    """
    pot_index: the index into POT_LIST we're running (0..N-1)
    pot_value: the digipot command value to send (e.g., 80)
    logger: the EntsLogger instance
    Behavior:
      - sets logger.pot_en True
      - sends "pot <value>" to logger.pot_ip
      - waits TIMER_MINUTES
      - stores logger.v and logger.i at logger.vpot_array[pot_index] and ipot_array[pot_index]
      - increments logger.pot_count
      - if cycle completed: publish, generate PNG, reset arrays or leave if continuous
    """
    try:
        # avoid double-starting for the same logger
        with logger.lock:
            if logger.timer_running:
                log_excel(f"Timer already running for logger {logger.id}; skipping start.")
                return
            logger.timer_running = True
            logger.pot_en = True

        log_excel(f"[logger {logger.id}] Starting pot step index={pot_index}, value={pot_value}")
        send_command(f"pot {pot_value}", logger.pot_ip)

        # wait
        time.sleep(TIMER_MINUTES * 60)

        # capture end-of-timer measurements
        with logger.lock:
            idx = pot_index
            # guard index
            if 0 <= idx < len(logger.vpot_array):
                logger.vpot_array[idx] = logger.v
                logger.ipot_array[idx] = logger.i
            else:
                log_excel(f"[logger {logger.id}] pot_index out of range: {idx}")
            logger.pot_count += 1
            cycle_complete = (logger.pot_count >= len(POT_LIST))

        # turn pot off
        send_command("pot off", logger.pot_ip)
        logger.pot_en = False

        # publish current status via MQTT
        try:
            payload = generate_mqtt_data(logger)
            topic = f"/sensor_data/{logger.id}"
            mqtt_client.publish(topic, payload, qos=1)
        except Exception as e:
            log_excel(f"MQTT publish failed for logger {logger.id}: {e}")

        log_excel(f"[logger {logger.id}] Completed pot idx={idx}. Recorded v={logger.v}, i={logger.i}")

        # if cycle finished, handle plotting and reset (or loop if continuous)
        if cycle_complete:
            with logger.lock:
                v_arr = logger.vpot_array.copy()
                i_arr = logger.ipot_array.copy()

            # compute power in uW (v in V * i in A * 1e6)
            power_uW = np.array(v_arr) * np.array(i_arr) * 1e6

            # generate PNG
            try:
                generate_png(i_arr * 1000, v_arr * 1000, power_uW, logger)
            except Exception as e:
                log_excel(f"Failed to generate PNG for logger {logger.id}: {e}")

            log_excel(f"[logger {logger.id}] Cycle complete. power_uW: {power_uW}")

            # publish final cycle via MQTT
            try:
                payload = generate_mqtt_data(logger)
                mqtt_client.publish(f"/sensor_data/{logger.id}/cycle", payload, qos=1)
            except Exception as e:
                log_excel(f"MQTT publish (cycle) failed for logger {logger.id}: {e}")

            # reset or repeat depending on continuous flag
            with logger.lock:
                if logger.continuous:
                    logger.vpot_array[:] = 0.0
                    logger.ipot_array[:] = 0.0
                    logger.pot_count = 0
                    log_excel(f"[logger {logger.id}] Continuous mode: restarting cycle.")
                else:
                    logger.vpot_array[:] = 0.0
                    logger.ipot_array[:] = 0.0
                    logger.pot_count = 0
                    logger.mppt_en = False  # optional: disable after single run
                    log_excel(f"[logger {logger.id}] Single-run done: resetting counters and disabling mppt_en.")

    except Exception as e:
        log_excel(f"Exception in start_timer_pot for logger {logger.id}: {e}")
        # ensure pot is off
        try:
            send_command("pot off", logger.pot_ip)
            logger.pot_en = False
        except Exception:
            pass
    finally:
        with logger.lock:
            logger.timer_running = False

# -------------------------
# Prometheus metrics
# -------------------------
voltage_gauge = Gauge('soil_sensor_voltage', 'Voltage from soil sensor', ['logger_id'])
current_gauge = Gauge('soil_sensor_current', 'Current from soil sensor', ['logger_id'])
temperature_gauge = Gauge('soil_sensor_temperature', 'Temperature from BME280', ['logger_id'])
humidity_gauge = Gauge('soil_sensor_humidity', 'Humidity from BME280', ['logger_id'])

# -------------------------
# Flask App & Endpoints
# -------------------------
app = Flask(__name__)

@app.route('/api/', methods=['GET'])
def health_check():
    return jsonify({"message": "API is running"}), 200

@app.route('/toggle', methods=['POST'])
def toggle():
    global pot0_en
    data = request.json or {}
    pot0_en = bool(data.get("isOn", False))
    log_excel(f"Mobile toggle changed: pot0_en={pot0_en}")
    if not pot0_en:
        # best-effort turn off all pots
        for l in ENTS_MAP.values():
            try:
                send_command("pot off", l.pot_ip)
                l.pot_en = False
            except Exception:
                pass
    return jsonify({"status": "ok"}), 200

@app.route('/get_value', methods=['GET'])
def get_value():
    return jsonify({"pot0_en": pot0_en}), 200

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        raw = request.data
        meas = decode_measurement(raw, raw=False)
        log_excel(f"Received data: {meas}")

        if meas['type'] == 'power':
            voltage = float(meas['data']['voltage'])
            current = float(meas['data']['current'])
            logger_id = str(meas['loggerId'])

            logger = ENTS_MAP.get(logger_id)
            if logger is None:
                log_excel(f"Unknown logger id: {logger_id}")
                return jsonify({"message": "Unknown logger id"}), 400

            # update logger state
            logger.v = voltage
            logger.i = current

            # CSV and Prometheus
            log_vi(meas)
            voltage_gauge.labels(logger_id=logger_id).set(voltage)
            current_gauge.labels(logger_id=logger_id).set(current)

            # publish status MQTT
            try:
                mqtt_client.publish(f"/sensor_data/{logger.id}", generate_mqtt_data(logger), qos=1)
            except Exception as e:
                log_excel(f"MQTT publish error: {e}")

            # decide to start a pot thread:
            # conditions: voltage > ocv, mppt enabled, pot not already running, global pot0_en true
            if (voltage > logger.ocv) and logger.mppt_en and (not logger.pot_en):
                log_excel(f"[logger {logger.id}] voltage {voltage} > ocv {logger.ocv} -> scheduling potentiometer step")
                next_idx = logger.pot_count
                if next_idx < len(POT_LIST):
                    pot_value = POT_LIST[next_idx]
                    threading.Thread(target=start_timer_pot, args=(next_idx, pot_value, logger), daemon=True).start()
                else:
                    log_excel(f"[logger {logger.id}] No more pot steps (pot_count={logger.pot_count}).")

        elif meas['type'] == 'bme280':
            temperature = float(meas['data']['temperature'])
            humidity = float(meas['data']['humidity'])
            logger_id = str(meas['loggerId'])

            # update logger state
            logger = ENTS_MAP.get(logger_id)
            logger.h = humidity
            logger.t = temperature

            log_th(meas)
            temperature_gauge.labels(logger_id=logger_id).set(temperature)
            humidity_gauge.labels(logger_id=logger_id).set(humidity)

        return jsonify({"message": "Data received"}), 200

    except Exception as e:
        log_excel(f"Failed to decode/process incoming data: {e}")
        return jsonify({"message": "Exception occurred", "error": str(e)}), 500

# -------------------------
# Startup
# -------------------------
if __name__ == "__main__":
    initialize_csv()
    log_excel(f"Log file initialized at: {CSV_PATH}")
    log_excel([repr(l) for l in ENTS_MAP.values()])

    # optional: open circuit at startup (turn off pot for ents13 as example)
    try:
        send_command("pot off", ents13.pot_ip)
        # send_command("pot off", ents11.pot_ip)
        # send_command("pot off", ents12.pot_ip)
        log_excel("Open-circuit pot off on ents13 executed at startup")
    except Exception as e:
        log_excel(f"Failed to run open-circuit at startup: {e}")

    log_excel("Flask server starting on port 5000...")
    app.run(host="0.0.0.0", port=5000)
