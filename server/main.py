import h2.connection
import socket

sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 8080))
sock.listen(5)

conn = h2.connection.H2Connection()
conn.send_headers(stream_id=stream_id, headers=headers)
conn.send_data(stream_id, data)
socket.sendall(conn.data_to_send())
events = conn.receive_data(socket_data)

while True:
    print(sock.accept())
