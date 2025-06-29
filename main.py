import os
import socket
import threading
import time
from dotenv import load_dotenv

load_dotenv()

TCP_PORT = int(os.getenv("TCP_PORT", 39111))
IMEI = os.getenv("IMEI")

def handle_client(conn, addr):
    imei = None
    print(f"[+] TCP bağlantısı: {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode(errors="ignore").strip()
            print(f"[{addr}] <<< {msg}")

            # Gelen mesajda *CMDR ve Q0 varsa L0 komutu gönder
            if "*CMDR" in msg and "Q0" in msg:
                print("[✓] Cihaz veri gönderdi, şimdi manuel olarak L0 komutu gönderiliyor.")
                cmd = f"*CMDS,OM,{IMEI},000000000000,L0,0,0,{int(time.time())}#\n"
                conn.sendall(cmd.encode())
                print(f"[>>] Gönderildi: {cmd.strip()}")

    except Exception as e:
        print(f"[!] Hata: {e}")
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
    tcp_server()