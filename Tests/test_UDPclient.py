import socket

HOST = 'localhost'
PORT = 5000

message = input("Bitte geben Sie eine Nachricht ein: ")

sd.socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sd.sendto(message.encode(), (HOST, PORT))
print("Nachricht gesendet")

print("Nachricht wurde erfolgreich gesendet")

sd.close()