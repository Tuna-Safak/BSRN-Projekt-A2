import socket

HOST = ''
PORT = 5000
BUFFER_SIZE = 1024

def run_server():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((HOST, PORT))
        print(f"Server listening on port {PORT}...")

        while True:
            data, address = server_socket.recvfrom(BUFFER_SIZE)
            message = data.decode('utf-8')
            print(f"Received message from {address}: {message}")

            response = f"Server received: {message}".encode('utf-8')
            server_socket.sendto(response, address)

            if message.strip().upper() == "STOP":
                print("STOP message received.  Shutting down server.")
                break

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        server_socket.close()
        print("Server socket closed.")

if __name__ == "__main__":
    run_server()
