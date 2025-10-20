# Compatible with esp8266_digipot_V1
# This script communicates with the IP Address of the digipot to run command pot <0-99> over wifi


import socket

IP = "192.168.0.116" #change IP of digipot


PORT = 1234

def interactive():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP, PORT))
        print("Connected to ESP. Type 'exit' to quit.\n")

        while True:
            cmd = input("Enter command: ").strip()
            if cmd.lower() == "exit":
                break
            if not cmd:
                continue

            s.sendall((cmd + '\n').encode())

            try:
                s.settimeout(2.0)  # give ESP time to respond
                reply = s.recv(1024).decode().strip()
                if reply:
                    print("ESP replied:", reply)
            except socket.timeout:
                print("No reply (timeout)")

if __name__ == "__main__":
    interactive()
