import h2.connection
import socket
import time
import json
import IPython


def establish_tcp_connection():
    """
    This function establishes a client-side TCP connection. How it works isn't
    very important to this example. For the purpose of this example we connect
    to localhost.
    """
    return socket.create_connection(('localhost', 8080))


def handle(sock):
    conn = h2.connection.H2Connection(client_side=False)
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())

    while True:
        data = sock.recv(65535)
        if not data:
            break

        events = conn.receive_data(data)
        for event in events:
            if isinstance(event, h2.events.RequestReceived):
                send_response(conn, event)
            if isinstance(event, h2.events.DataReceived):
                print(event.data)
                send_response(conn, event)

        data_to_send = conn.data_to_send()
        if data_to_send:
            sock.sendall(data_to_send)


def send_response(conn, data):
    #response_data = json.dumps(data).encode('utf-8')
    try:
        response_data = data.encode('utf-8')
    except AttributeError:
        response_data = data

    stream_id = conn.get_next_available_stream_id()
    #IPython.embed()
    conn.max_outbound_frame_size=len(response_data)

    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (':path', '/post'),
            (':method', 'POST'),
            (':scheme', 'http'),
            (':authority', 'localhost'),
            ('content-length', str(len(response_data))),
            ('content-type', 'application/json'),
        ],
    )
    conn.send_data(
        stream_id=stream_id,
        data=response_data,
        end_stream=True
    )


def main():
    connection = establish_tcp_connection()
    http2_connection = h2.connection.H2Connection()
    http2_connection.initiate_connection()
    connection.sendall(http2_connection.data_to_send())

    print("Connection set")

    while True:
        while True:
            choice = input("Send an image? (y/n): ")
            if (choice=="y" or choice=="Y"):
                choice = input("Give image path or name: ")
                try:
                    image = open(choice, "rb")
                    data = b""
                    for b in image:
                        data = data + b
                except OSError as oserr:
                    print("Check file name: {0}".format(oserr))
                except:
                    print("Error")
                break
            elif (choice=="n" or choice=="N"):
                data = input("Message to send: ")
                break
            else:
                print("Please write either 'y' or 'n'")
        send_response(http2_connection, data)
        data_to_send = http2_connection.data_to_send()
        if data_to_send:
            connection.sendall(data_to_send)


if __name__ == "__main__":
    main()