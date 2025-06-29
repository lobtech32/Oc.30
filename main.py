import os
import asyncio
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

IMEI = os.getenv("IMEI")
TCP_PORT = int(os.getenv("TCP_PORT", "39051"))

connections: dict[str, asyncio.StreamWriter] = {}

async def handle_lock(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        data = await reader.readline()
        text = data.decode().strip()
        print(f"Gelen veri: {text}")
        parts = text.split(',')
        if len(parts) >= 4:
            imei = parts[2]
            connections[imei] = writer
            print(f"Kilit {imei} bağlandı.")
        while not reader.at_eof():
            await reader.readline()
    except Exception as e:
        print("Hata:", e)
    finally:
        for k, w in list(connections.items()):
            if w is writer:
                del connections[k]
                print(f"Kilit {k} bağlantısı kapandı.")
        writer.close()
        await writer.wait_closed()

@app.on_event("startup")
async def start_tcp_server():
    server = await asyncio.start_server(handle_lock, '0.0.0.0', TCP_PORT)
    print(f"TCP dinleniyor: {TCP_PORT}")
    asyncio.create_task(server.serve_forever())

def get_writer():
    writer = connections.get(IMEI)
    if not writer:
        raise HTTPException(status_code=404, detail="Kilit bağlı değil")
    return writer

@app.get("/unlock")
async def unlock():
    cmd = f"*CMDS,OM,{IMEI},000000000000,L0,0,0,0#\\n"
    writer = get_writer()
    writer.write(cmd.encode())
    await writer.drain()
    return {"status": "sent", "command": cmd}

@app.get("/lock")
async def lock():
    cmd = f"*CMDS,OM,{IMEI},000000000000,L1,0,0,0#\\n"
    writer = get_writer()
    writer.write(cmd.encode())
    await writer.drain()
    return {"status": "sent", "command": cmd}