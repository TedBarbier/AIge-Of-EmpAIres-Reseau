import asyncio
import socket
import platform

async def send_packets(client_socket, target_address, packets_sent):
    for i in range(20000):  # Envoyer 200 000 paquets individuellement
        if platform.system() == 'Windows':
            # Sur Windows, on utilise sendto directement
            client_socket.sendto(f"Paquet {i}".encode('utf-8'), target_address)
        else:
            # Sur les autres systèmes, on utilise asyncio
            await asyncio.get_event_loop().sock_sendto(
                client_socket,
                f"Paquet {i}".encode('utf-8'),
                target_address
            )

        packets_sent += 1
        print(f"\rPaquets envoyés: {packets_sent}/200000", end="", flush=True)
    print("\nEnvoi terminé!")

async def receive_packets(server_socket, packets_received):
    while True:
        try:
            if platform.system() == 'Windows':
                # Sur Windows, on utilise recvfrom directement
                data, addr = server_socket.recvfrom(1024)
            else:
                # Sur les autres systèmes, on utilise asyncio
                data, addr = await asyncio.get_event_loop().sock_recvfrom(server_socket, 1024)

            packets_received += 1
            print(f"\rPaquets reçus: {packets_received}", end="", flush=True)
        except Exception as e:
            print(f"\nErreur de réception: {e}")
            break

async def main():
    # Créer les sockets
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Configuration
    server_socket.bind(('localhost', 1234))
    server_socket.setblocking(False)
    target_address = ('localhost', 12345)

    packets_sent = 0
    packets_received = 0

    print("Serveur Python en écoute sur le port 1234")
    print("Tapez 'start' pour commencer l'envoi de paquets et 'quit' pour quitter")

    # Lancer les tâches asynchrones
    receive_task = asyncio.create_task(receive_packets(server_socket, packets_received))

    while True:
        command = await asyncio.get_event_loop().run_in_executor(None, input)
        if command.lower() == 'quit':
            print("\nArrêt du programme...")
            receive_task.cancel()
            break
        elif command.lower() == 'start':
            print("\nEnvoi de paquets en cours...")
            await send_packets(client_socket, target_address, packets_sent)

if __name__ == "__main__":
    asyncio.run(main())