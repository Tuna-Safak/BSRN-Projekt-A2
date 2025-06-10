import socket

SERVER_IP = '192.168.1.100'  # Replace with the server's IP address
PORT = 5000
BUFFER_SIZE = 1024

def run_client():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while True:
            message = input("Enter message (or 'STOP' to quit): ")
            client_socket.sendto(message.encode('utf-8'), (SERVER_IP, PORT))

            data, address = client_socket.recvfrom(BUFFER_SIZE)
            response = data.decode('utf-8')
            print(f"Received from server: {response}")

            if message.strip().upper() == "STOP":
                break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        client_socket.close()
        print("Client socket closed.")

if __name__ == "__main__":
    run_client()
