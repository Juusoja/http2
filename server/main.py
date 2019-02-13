import socket
import json
import h2.connection
import h2.events
import IPython
import threading

tags = []

def send_response(conn, event):
    stream_id = event.stream_id
    response_data = json.dumps(dict(event.headers)).encode('utf-8')
    print("\nResponse data:\n")
    print(response_data)
    print(len(response_data))

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
        #end_stream=True
    )

def send_indexes(conn, event):
    stream_id = event.stream_id
    response_data = json.dumps(dict([["image0","/image0.jpg"],["image1","/image1.jpg"],
                                        ["image2","/image2.jpg"]])).encode('utf-8')
    print("\nResponse data:\n")
    print(response_data)

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

def send_data(conn, event, data, end=True, status=True):
    stream_id = event.stream_id
    response_data = data
    print("Sending {} bytes of data...".format(str(len(response_data))))
    
    if status:
        conn.send_headers(
            stream_id = stream_id,
            headers = [
                (':status', '200'),
                ('server', 'basic-h2-server/1.0'),
                ('content-length', str(len(response_data))),
                ('content-type', 'application/json'),
            ],
        )
    else:
        conn.send_headers(
            stream_id = stream_id,
            headers = [
                ('server', 'basic-h2-server/1.0'),
                ('content-length', str(len(response_data))),
                ('content-type', 'application/json'),
            ],
        )

    conn.send_data(
        stream_id=stream_id,
        data=response_data,
        end_stream=end
    )

def send_notification(conn):
    pass

def add_tag(tag):
    global tags
    if not tag in tags:
        tags.append(tag)
    print("Tags: ", end='')
    print(tags)
    return tags

def get_tags():
    print(tags)

def handle(sock):
    print("Incoming connection")
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
            print(event)
            if isinstance(event, h2.events.RequestReceived):
                #send_response(conn, event)
                for i in range(0,len(event.headers)):
                    if event.headers[i][0]==':path':
                        path = event.headers[i][1]
                    if event.headers[i][0]==':method':
                        method = event.headers[i][1]
            if isinstance(event, h2.events.DataReceived):
                #print(event.data)
                if path=='/image' and method=='POST':
                    f = open("image","wb+")
                    f.write(event.data)
                    f.close
                elif path=='/notification' and method=='GET':
                    #send_notification()
                    send_to = conn.get_next_available_stream_id()
                    print("Notification sent!")
                    print("{} - {}".format(event.stream_id,send_to))
                    conn.push_stream(event.stream_id, send_to,
                        [(':path', '/notification'),(':method', 'POST'),
                        (':scheme', 'http'),(':authority', 'localhost'),
                        ('content-length', str(len('data'))),
                        ('content-type', 'application/json')])
                elif path=='/tags' and method=='POST':
                    add_tag(event.data.decode('utf-8'))
                elif path=='/tags' and method=='GET':
                    get_tags()  


                elif path=='/push' and method=='GET':
                    print("push getterino")
                    send_to = conn.get_next_available_stream_id()
                    print("Notification sent!")
                    print("{} - {}".format(event.stream_id,send_to))
                    conn.push_stream(event.stream_id, send_to,
                        [(':path', '/notification'),(':method', 'POST'),
                        (':scheme', 'http'),(':authority', 'localhost'),
                        ('content-length', str(len('data'))),
                        ('content-type', 'application/json')])
                elif path=='/' and method=='GET':
                    print("plain getterino")
                    send_indexes(conn, event)
                elif method=='GET':
                    try:
                        print(path[1:]+" requested")
                        resource = open(path[1:],"rb")
                        data = b""
                        for b in resource:
                            if len(data + b) > 16384:
                                send_data(conn, event, data, end=False)
                                sock.sendall(conn.data_to_send())
                                data = b""
                            data = data + b
                        send_data(conn, event, data, end=False)
                        sock.sendall(conn.data_to_send())
                    except Error as e:
                        print(e)
                        print(path[1:]+" NOT FOUND")
                else:
                    print(event.data)

        data_to_send = conn.data_to_send()
        print(data_to_send)
        if data_to_send:
            try:
                sock.sendall(data_to_send)
            except BrokenPipeError:
                pass


sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 8080))
sock.listen(5)

while True:
    try:
        threading.Thread(target=handle, args=(sock.accept()[0],)).start()
    except ConnectionResetError:
        pass