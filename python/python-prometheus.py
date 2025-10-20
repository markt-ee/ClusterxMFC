from prometheus_client import start_http_server, Gauge
import time
import random  # or your real sensor reading logic

# Define Prometheus metrics
voltage_gauge = Gauge('soil_sensor_voltage', 'Voltage from soil sensor')
current_gauge = Gauge('soil_sensor_current', 'Current from soil sensor')

# Start HTTP server on port 8000 (Prometheus will scrape here)
start_http_server(8000, addr='0.0.0.0'))

print("✅ Prometheus metrics server started on :8000")

while True:
    # Get your real sensor data here
    voltage = round(random.uniform(0.7, 0.9), 2)
    current = round(random.uniform(0.004, 0.006), 4)

    # Update Prometheus metrics
    voltage_gauge.set(voltage)
    current_gauge.set(current)

    print(f"Updated metrics: Voltage={voltage}V, Current={current}A")

    time.sleep(10)
