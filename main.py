import os
import socket
import threading
import datetime
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

TCP_PORT = int(os.getenv("TCP_PORT", 39111))
HTTP_PORT = int(os.getenv("HTTP_PORT", 8020))
IMEI = os.getenv("IMEI")

app = Flask(__name__)

lock_connections: dict[str, socket.socket] = {}
conn_lock = threading.Lock()

def handle_client(conn, addr):
    imei = None
    print(f"[+] TCP bağlantısı: {addr}")
    try:
        buffer = b""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                msg = line.decode(errors="ignore").strip()
                print(f"[{addr}] <<< {msg}")
                if "*CMDR" in msg and not imei:
                    parts = msg.split(",")
                    if len(parts) >= 3:
                        imei = parts[2]
                        with conn_lock:
                            lock_connections[imei] = conn
                        print(f"[+] Kilit IMEI kaydedildi: {imei}")
    except Exception as e:
        print(f"[!] TCP hatası ({addr}): {e}")
    finally:
        print(f"[-] TCP bağlantısı kapandı: {addr}")
        with conn_lock:
            if imei and imei in lock_connections:
                del lock_connections[imei]
                print(f"[-] Kilit IMEI silindi: {imei}")
        conn.close()

def tcp_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", TCP_PORT))
    srv.listen()
    print(f"[TCP] Dinleniyor: 0.0.0.0:{TCP_PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

@app.route("/")
def alive():
    return "OK", 200

if __name__ == "__main__":
    threading.Thread(target=tcp_server, daemon=True).start()
    print(f"[HTTP] Flask ayakta: 0.0.0.0:{HTTP_PORT}")
    app.run(host="0.0.0.0", port=HTTP_PORT)