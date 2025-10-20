import socket

ESP32_IP = "192.168.0.31"  # Replace with your ESP32's IP
PORT = 1234

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ESP32_IP, PORT))
        s.sendall((cmd + '\n').encode())
        print(f"Sent: {cmd}")

if __name__ == "__main__":
    while True:
        command = input("Enter command to send to ESP32: ")
        if command.lower() == "exit":
            break
        send_command(command)
