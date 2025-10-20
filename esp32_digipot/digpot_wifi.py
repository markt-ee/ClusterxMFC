import socket
import time

ESP32_IP = "192.168.0.30"  # Replace with your ESP32's IP
PORT = 1234
resistance_steps = [100, 10, 1, 0]
current_step = 0

def send_command(cmd):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ESP32_IP, PORT))
        s.sendall((cmd + '\n').encode())
        print(f"Sent: {cmd}")

if __name__ == "__main__":
    while True:
        # command = input("Enter command to send to ESP32: ")
        # if command.lower() == "exit":
        #      break
        # send_command(command)
    
    #automation to go from 100k -> 10k -> 10 ohms
        if current_step == 4: 
            current_step = 0
        resistance = resistance_steps[current_step]
        print(f"pot {resistance}")
        send_command(f"pot {resistance}")
     #   time.sleep(2)
     #   send_command(f"pot {resistance}")
        print("60 second delay")
        time.sleep(60)
        send_command("pot off") #current issue, pot off has to go all the way down to 0 first, and then back up.. weird
        time.sleep(2)
        send_command("pot off")
        print("120 second delay")
        time.sleep(120)
        current_step = current_step + 1





