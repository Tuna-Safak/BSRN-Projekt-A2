import socket

HOST = ' '
PORT = 5000

sd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    sd.bind((HOST, PORT))
    print(f"Server läuft auf Port {PORT}. Warte auf Nachrichten...")

    while True: 
        data, addr = sd.recvfrom(1024)
        message = data.decode()
        print(f"Empfangen von {addr}: {message}")

        if message.strip().upper() == "STOP":
            print("STOP empfangen. Server wird beendet.")
            break
finally:
    sd.close()
    print("Socket geschlossen.")
