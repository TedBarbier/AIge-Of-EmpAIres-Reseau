import socket
import threading

def listen_for_messages():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('localhost', 1234))
    print("Python server listening on port 1234")

    while True:
        data, addr = server_socket.recvfrom(1024)
        print(f"Received from {addr}: {data.decode('utf-8')}")

def send_messages():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target_address = ('localhost', 12345)

    while True:
        message = input("Enter message to send: ")
        client_socket.sendto(message.encode('utf-8'), target_address)

def start_server():
    listen_thread = threading.Thread(target=listen_for_messages)
    send_thread = threading.Thread(target=send_messages)

    listen_thread.start()
    send_thread.start()

    listen_thread.join()
    send_thread.join()

if __name__ == "__main__":
    start_server()
