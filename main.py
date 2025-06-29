import os
import asyncio
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

IMEI = os.getenv("IMEI")
TCP_PORT = int(os.getenv("TCP_PORT", "39111"))

# Kilit bağlantılarını burada saklıyoruz
connections: dict[str, asyncio.StreamWriter] = {}

async def handle_lock(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        # IMEI'yi .env'den alarak doğrudan kaydet
        connections[IMEI] = writer
        print(f"Kilit {IMEI} bağlandı.")

        # Veri gelmese bile bağlantı açık kalsın
        while not reader.at_eof():
            data = await reader.readline()
            if not data:
                continue
            text = data.decode().strip()
            print(f"Gelen veri: {text}")

    except Exception as e:
        print("Hata:", e)

    finally:
        # Bağlantı kapanınca sil
        for k, w in list(connections.items()):
            if w is writer:
                del connections[k]
                print(f"Kilit {k} bağlantısı kapandı.")
        writer.close()
        await writer.wait_closed()

@app.on_event("startup")
async def start_tcp_server():
    server = await asyncio.start_server(handle_lock, "0.0.0.0", TCP_PORT)
    print(f"TCP dinleniyor: {TCP_PORT}")
    asyncio.create_task(server.serve_forever())

def get_writer():
    writer = connections.get(IMEI)
    if not writer:
        raise HTTPException(status_code=404, detail="Kilit bağlı değil")
    return writer

@app.get("/unlock")
async def unlock():
    cmd = f"*CMDS,OM,{IMEI},000000000000,L0,0,0,0#\n"
    writer = get_writer()
    writer.write(cmd.encode())
    await writer.drain()
    return {"status": "sent", "command": cmd}

@app.get("/lock")
async def lock():
    cmd = f"*CMDS,OM,{IMEI},000000000000,L1,0,0,0#\n"
    writer = get_writer()
    writer.write(cmd.encode())
    await writer.drain()
    return {"status": "sent", "command": cmd}