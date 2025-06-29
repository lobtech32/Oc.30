import socket

TCP_PORT = 39111

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.bind(("0.0.0.0", TCP_PORT))
srv.listen()
print(f"[TCP] Dinleniyor: {TCP_PORT}")

while True:
    conn, addr = srv.accept()
    print(f"[+] Bağlantı: {addr}")
    conn.close()