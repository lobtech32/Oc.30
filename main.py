import os
import socket
import threading
import time
from dotenv import load_dotenv
import traceback
from flask import Flask

load_dotenv()

# Ortam değişkenlerini al, yoksa varsayılan değerler ver
TCP_PORT = int(os.getenv("TCP_PORT", 39111))  # Railway'de 39111 olabilir
IMEI = os.getenv("IMEI", "862205059210023")  # Boşsa default IMEI koy
FLASK_PORT = int(os.getenv("PORT", 8082))    # Railway'den gelen HTTP portu

print(f"IMEI değeri: {IMEI}")
print(f"TCP Portu: {TCP_PORT}")
print(f"HTTP Portu (Flask): {FLASK_PORT}")

app = Flask(__name__)

@app.route("/")
def index():
    return "Server çalışıyor", 200

@app.route("/health")
def health():
    return "OK", 200

def handle_client(conn, addr):
    print(f"[+] TCP bağlantısı: {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode(errors="ignore").strip()
            print(f"[{addr}] <<< {msg}")

            if IMEI is None or IMEI == "":
                print("[!] IMEI boş, L0 komutu gönderilmiyor.")
                continue

            if "*CMDR" in msg and "Q0" in msg:
                print("[✓] Cihaz veri gönderdi, L0 komutu gönderiliyor.")
                cmd = f"*CMDS,OM,{IMEI},000000000000,L0,0,0,{int(time.time())}#\n"
                conn.sendall(cmd.encode())
                print(f"[>>] Gönderildi: {cmd.strip()}")

    except Exception as e:
        print(f"[!] Hata: {e}")
        traceback.print_exc()
    finally:
        print(f"[-] Bağlantı kapandı: {addr}")
        conn.close()

def tcp_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("0.0.0.0", TCP_PORT))
    srv.listen()
    print(f"[TCP] Dinleniyor: {TCP_PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    print("Sunucu başlıyor...")
    threading.Thread(target=tcp_server, daemon=True).start()
    app.run(host="0.0.0.0", port=FLASK_PORT)