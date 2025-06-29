import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

IMEI = os.getenv("IMEI")
TCP_PORT = int(os.getenv("TCP_PORT", "39111"))

connections: dict[str, asyncio.StreamWriter] = {}

async def handle_lock(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        connections[IMEI] = writer
        print(f"Kilit {IMEI} bağlandı.")

        while not reader.at_eof():
            data = await reader.readline()
            if data:
                text = data.decode().strip()
                print(f"Gelen veri: {text}")
    except Exception as e:
        print("Hata:", e)
    finally:
        for k, w in list(connections.items()):
            if w is writer:
                del connections[k]
                print(f"Kilit {k} bağlantısı kapandı.")
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_lock, "0.0.0.0", TCP_PORT)
    print(f"TCP dinleniyor: {TCP_PORT}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())