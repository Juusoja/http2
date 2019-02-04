import socket
import json
import h2.connection
import h2.events
import IPython

def send_response(conn, event):
    stream_id = event.stream_id
    response_data = json.dumps(dict(event.headers)).encode('utf-8')

    conn.send_headers(
        stream_id = stream_id,
        headers = [
            (':status', '200'),
            ('server', 'basic-h2-server/1.0'),
            ('content-length', str(len(response_data))),
            ('content-type', 'application/json'),
        ],
    )
    conn.send_data(
        stream_id=stream_id,
        data=response_data,
        end_stream=True
    )

def handle(sock):
    print("Incoming data")
    conn = h2.connection.H2Connection(client_side=False)
    conn.initiate_connection()
    conn.max_inbound_frame_size = 65536
    sock.sendall(conn.data_to_send())

    while True:
        data = sock.recv(65535)

        if not data:
            break

        events = conn.receive_data(data)
        path = ''
        method = ''
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                send_response(conn, event)
                for i in range(0,len(event.headers)):
                    if event.headers[i][0]==':path':
                        path = event.headers[i][1]
                    if event.headers[i][0]==':method':
                        method = event.headers[i][1]
            if isinstance(event, h2.events.DataReceived):
                #print(event.data)
                if path=='/post' and method=='POST':
                    f = open("guru99","wb+")
                    f.write(event.data)
                    f.close
                else:
                    print(event.data)

        data_to_send = conn.data_to_send()
        if data_to_send:
            sock.sendall(data_to_send)


sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 8080))
sock.listen(5)

while True:
    handle(sock.accept()[0])