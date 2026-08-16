import csv
import sys
from pathlib import Path

DATA_FIELDS = [
    "local_time", "sensor_ts", "logger_id", "pot_value", "type",
    "voltage", "current", "power", "temperature", "humidity",
]


def extract_number(text, key):
    marker = f"'{key}':"
    start = text.find(marker)
    if start == -1:
        return None

    after = text[start + len(marker):]
    comma_pos = after.find(",")
    brace_pos = after.find("}")
    candidates = [p for p in (comma_pos, brace_pos) if p != -1]
    end = min(candidates) if candidates else len(after)

    value_str = after[:end].strip()
    try:
        return float(value_str)
    except ValueError:
        return None  # e.g. "<class 'float'>", not an actual reading


def extract_string(text, key):
    marker = f"'{key}':"
    start = text.find(marker)
    if start == -1:
        return None

    after = text[start + len(marker):].strip()
    if not after.startswith("'"):
        return None

    after = after[1:]
    end = after.find("'")
    return after[:end] if end != -1 else None


def parse_file(input_path):
    data_rows = []
    log_rows = []
    current_pot_value = None

    with open(input_path, "r", errors="replace") as f:
        for raw_line in f:
            raw_line = raw_line.rstrip("\n")
            if not raw_line.strip():
                continue

            has_timestamp = (
                raw_line.startswith("[")
                and len(raw_line) > 10
                and raw_line[9] == "]"
            )
            if not has_timestamp:
                log_rows.append({"local_time": "", "message": raw_line})
                continue

            local_time = raw_line[1:9]
            rest = raw_line[11:]

            if rest.startswith("Sent to ESP32: pot "):
                pot_val = rest[len("Sent to ESP32: pot "):].strip()
                current_pot_value = None if pot_val == "off" else pot_val
                log_rows.append({"local_time": local_time, "message": rest})
                continue

            if rest.startswith("Voltage threshold reached"):
                log_rows.append({"local_time": local_time, "message": rest})
                continue

            if rest.startswith("Received data: "):
                blob = rest[len("Received data: "):]
                rtype = extract_string(blob, "type")
                logger_id_raw = extract_number(blob, "loggerId")
                ts_raw = extract_number(blob, "ts")
                logger_id = int(logger_id_raw) if logger_id_raw is not None else None
                ts = int(ts_raw) if ts_raw is not None else None

                if rtype == "power":
                    voltage = extract_number(blob, "voltage")
                    current = extract_number(blob, "current")
                    power = (voltage * current) if (voltage is not None and current is not None) else None
                    data_rows.append({
                        "local_time": local_time, "sensor_ts": ts, "logger_id": logger_id,
                        "pot_value": current_pot_value, "type": "power",
                        "voltage": voltage, "current": current, "power": power,
                        "temperature": None, "humidity": None,
                    })
                elif rtype == "bme280":
                    temperature = extract_number(blob, "temperature")
                    humidity = extract_number(blob, "humidity")
                    data_rows.append({
                        "local_time": local_time, "sensor_ts": ts, "logger_id": logger_id,
                        "pot_value": current_pot_value, "type": "bme280",
                        "voltage": None, "current": None, "power": None,
                        "temperature": temperature, "humidity": humidity,
                    })
                else:
                    log_rows.append({"local_time": local_time, "message": rest})
                continue

            if rest.startswith("Voltage:") or rest.startswith("Temperature:"):
                continue

            log_rows.append({"local_time": local_time, "message": rest})

    return data_rows, log_rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    args = [a for a in sys.argv[1:] if a != "--no-log"]
    skip_log = "--no-log" in sys.argv

    if len(args) < 1:
        print("Usage: python3 parse_smfc_log.py <input_file> [output_dir] [--no-log]")
        sys.exit(1)

    input_path = Path(args[0])
    out_dir = Path(args[1]) if len(args) > 1 else input_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = input_path.stem
    data_out = out_dir / f"{stem}_parsed_data.csv"

    data_rows, log_rows = parse_file(input_path)

    write_csv(data_out, data_rows, DATA_FIELDS)

    if not skip_log:
        log_out = out_dir / f"{stem}_parsed_log.csv"
        write_csv(log_out, log_rows, ["local_time", "message"])


if __name__ == "__main__":
    main()