import os
import socket
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()

# Ortam değişkeni: JSON formatta IMEI->host:port eşlemesi. Örneğin:
# {"123456789012345": "1.2.3.4:12345", "987654321098765": "5.6.7.8:23456"}
# Railway’de ENV var olarak ekleyeceğiz:
# DEVICE_MAP='{"123456789012345":"cihaz_ip:cihaz_port"}'
import json
_device_map = {}
_device_map_str = os.getenv("DEVICE_MAP", "")
if _device_map_str:
    try:
        _device_map = json.loads(_device_map_str)
    except Exception:
        print("DEVICE_MAP parse error")

def get_device_address(imei: str):
    addr = _device_map.get(imei)
    if not addr:
        raise HTTPException(status_code=400, detail=f"IMEI için adres ayarlı değil: {imei}")
    parts = addr.split(":")
    if len(parts) != 2:
        raise HTTPException(status_code=500, detail=f"DEVICE_MAP formatı hatalı: {addr}")
    return parts[0], int(parts[1])

def format_ts_fields():
    # YYMMDDhhmmss formatı
    now = datetime.utcnow()
    ts_str = now.strftime("%y%m%d%H%M%S")
    # Unix timestamp integer
    unix_ts = int(time.time())
    return ts_str, unix_ts

def send_tcp_command(imei: str, cmd: str, userid: str = "0"):
    host, port = get_device_address(imei)
    ts_str, unix_ts = format_ts_fields()
    # Komut formatı: *CMDS,OM,IMEI,YYMMDDhhmmss,CMD,0,USERID,UnixTS#
    payload = f"*CMDS,OM,{imei},{ts_str},{cmd},0,{userid},{unix_ts}#"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((host, port))
            s.sendall(payload.encode())
            data = s.recv(1024)
            resp = data.decode(errors="ignore")
            return resp
    except socket.timeout:
        raise HTTPException(status_code=504, detail="Cihaza bağlanırken zaman aşımı")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TCP hatası: {e}")

class UnlockParams(BaseModel):
    imei: str
    userid: str

@app.get("/unlock")
def unlock(imei: str = Query(...), userid: str = Query(...)):
    """
    Kilidi aç: L0 komutu gönderir.
    Örnek: /unlock?imei=123456789012345&userid=10001
    """
    resp = send_tcp_command(imei, "L0", userid)
    return {"raw_response": resp}

@app.get("/lock")
def lock(imei: str = Query(...), userid: str = Query(...)):
    """
    Kilidi kapat: L1 komutu gönderir.
    Örnek: /lock?imei=123456789012345&userid=10001
    """
    resp = send_tcp_command(imei, "L1", userid)
    return {"raw_response": resp}

@app.get("/gps")
def gps(imei: str = Query(...)):
    """
    GPS konumu al: D0 komutu gönderir.
    Örnek: /gps?imei=123456789012345
    """
    resp = send_tcp_command(imei, "D0", "0")
    # İstersen burada gelen stringi parse edip JSON’a çevirebilirsin.
    return {"raw_response": resp}

@app.get("/status")
def status(imei: str = Query(...)):
    """
    Cihaz durumu al: S5 komutu.
    Örnek: /status?imei=123456789012345
    """
    resp = send_tcp_command(imei, "S5", "0")
    return {"raw_response": resp}

@app.get("/sim")
def sim(imei: str = Query(...)):
    """
    SIM ICCID al: I0 komutu.
    Örnek: /sim?imei=123456789012345
    """
    resp = send_tcp_command(imei, "I0", "0")
    return {"raw_response": resp}

@app.get("/alarm/set")
def alarm_set(imei: str = Query(...), mode: int = Query(...)):
    """
    Alarm modunu ayarla: W0 komutu.
    mode: alarm parametresine göre değişir (dokümana bak).
    Örnek: /alarm/set?imei=...&mode=1
    """
    # Bazı cihazlarda W0 komut formatı: W0,<param>
    # Örneğin payload: "*CMDS,OM,IMEI,TS,W0,1#"
    ts_str, unix_ts = format_ts_fields()
    host, port = get_device_address(imei)
    payload = f"*CMDS,OM,{imei},{ts_str},W0,{mode}#"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((host, port))
            s.sendall(payload.encode())
            data = s.recv(1024)
            resp = data.decode(errors="ignore")
            return {"raw_response": resp}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TCP hatası: {e}")

@app.get("/alarm/off")
def alarm_off(imei: str = Query(...)):
    """
    Alarmı sustur: (Dokümanda A0 veya ilgili komut varsa).
    Örnek: /alarm/off?imei=...
    """
    # Eğer cihazda A0 gibi komut varsa, aynı send_tcp_command ile kullan:
    resp = send_tcp_command(imei, "A0", "0")
    return {"raw_response": resp}
