# main.py
import os
import socket
import threading
import datetime
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Ortam değişkenlerini oku
load_dotenv()
TCP_PORT = int(os.getenv("TCP_PORT", 39111))
HTTP_PORT = int(os.getenv("HTTP_PORT", 8020))
IMEI = os.getenv("IMEI")

app = Flask(__name__)

# IMEI → socket bağlantılarını saklayacağız
lock_connections: dict[str, socket.socket] = {}
conn_lock = threading.Lock()

def handle_client(conn: socket.socket, addr):
    """
    Her yeni TCP bağlantısı için çalışan fonksiyon.
    Bağlanan kilidi IMEI'ye göre kaydeder, veri gelince loglar.
    """
    imei = None
    print(f"[+] TCP bağlantısı: {addr}")
    try:
        buffer = b""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            # Satır satır işle
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                msg = line.decode(errors="ignore").strip()
                print(f"[{addr}] <<< {msg}")
                # *CMDR... içeren ilk mesajdan IMEI al
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
    """
    Arka planda TCP sunucusunu başlatır.
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", TCP_PORT))
    srv.listen()
    print(f"[TCP] Dinleniyor: 0.0.0.0:{TCP_PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

@app.route("/unlock", methods=["POST"])
def open_lock():
    """
    POST /unlock
    JSON gövdesi yok, IMEI'yi .env'den alır.
    Bağlıysa L0 komutunu yollar.
    """
    with conn_lock:
        conn = lock_connections.get(IMEI)
    if not conn:
        return jsonify({"error": "Cihaz bağlı değil"}), 404

    try:
        ts = int(datetime.datetime.utcnow().timestamp())
        cmd = f"*CMDS,OM,{IMEI},000000000000,L0,0,0,{ts}#\n"
        conn.sendall(cmd.encode())
        print(f"[>>] Komut gönderildi: {cmd.strip()}")
        return jsonify({"ok": True, "command": cmd.strip()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # 1) TCP sunucuyu başlat
    threading.Thread(target=tcp_server, daemon=True).start()
    # 2) HTTP API'yi başlat
    print(f"[HTTP] Flask çalışıyor: 0.0.0.0:{HTTP_PORT}")
    app.run(host="0.0.0.0", port=HTTP_PORT)