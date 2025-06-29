import os
import socket
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

IMEI = os.getenv("IMEI")
LOCK_HOST = os.getenv("LOCK_HOST")
LOCK_PORT = int(os.getenv("LOCK_PORT"))

def send_to_lock(cmd: str) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((LOCK_HOST, LOCK_PORT))
    sock.sendall(cmd.encode())
    resp = sock.recv(1024).decode()
    sock.close()
    return resp

@app.get("/unlock")
def unlock():
    cmd = f"*CMDS,OM,{IMEI},000000000000,L0,0,0,0#"
    try:
        response = send_to_lock(cmd)
        return {"status": "success", "lock_response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lock")
def lock():
    cmd = f"*CMDS,OM,{IMEI},000000000000,L1,0,0,0#"
    try:
        response = send_to_lock(cmd)
        return {"status": "success", "lock_response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))