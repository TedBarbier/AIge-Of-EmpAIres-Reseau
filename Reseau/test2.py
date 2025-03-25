import asyncio

class UDPServerProtocol:
    def __init__(self):
        self.packets_received = 0

    def connection_made(self, transport):
        self.transport = transport
        print("Serveur en écoute...")

    def datagram_received(self, data, addr):
        self.packets_received += 1
        print(f"Reçu de {addr}: {data.decode('utf-8')} (Paquets reçus: {self.packets_received})")

async def main():
    loop = asyncio.get_running_loop()

    print("Serveur Python en écoute sur le port 1234")

    # Créer le point de terminaison de transport
    listen = loop.create_datagram_endpoint(
        lambda: UDPServerProtocol(),
        local_addr=('127.0.0.1', 1234))

    transport, protocol = await listen

    # Attendre indéfiniment pour garder le serveur en écoute
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Arrêt du programme...")
        transport.close()

if __name__ == "__main__":
    asyncio.run(main())