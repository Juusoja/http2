import h2.connection
import socket
import time
import json
import IPython


def establish_tcp_connection():
    return socket.create_connection(('localhost', 8080))


def send_response(conn, data, path='/post', method='POST', close_stream=True):
    #response_data = json.dumps(data).encode('utf-8')
    try:
        response_data = data.encode('utf-8')
    except AttributeError:
        response_data = data

    stream_id = conn.get_next_available_stream_id()
    #IPython.embed()
    conn.max_outbound_frame_size=65536

    conn.send_headers(
        stream_id=stream_id,
        headers=[
            (':path', path),
            (':method', method),
            (':scheme', 'http'),
            (':authority', 'localhost'),
            ('content-length', str(len(data))),
            ('content-type', 'application/json'),
        ],
    )
    conn.send_data(
        stream_id=stream_id,
        data=response_data,
        end_stream=close_stream
    )

def wait_for_notification(connection, http2_connection):
    data = b''
    time.sleep(1)
    raw_data = connection.recv(65536)
    events = http2_connection.receive_data(raw_data)
    for e in events:
        print(e)

def send_data(data_to_send, connection):
    if data_to_send:
            connection.sendall(data_to_send)

def main():
    connection = establish_tcp_connection()
    http2_connection = h2.connection.H2Connection()
    http2_connection.initiate_connection()
    connection.sendall(http2_connection.data_to_send())

    print("Connection set")

    while True:
        while True:
            data = ""
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
                send_response(http2_connection, data, path='/image')
                break
            elif (choice=="n" or choice=="N"):
                choice = input("Test a notification? (y/n): ")
                if (choice=="y" or choice=="Y"):
                    send_response(http2_connection, data, path='/notification', method='GET', close_stream=False)
                    send_data(http2_connection.data_to_send(), connection)
                    wait_for_notification(connection, http2_connection)
                    break
                elif (choice=="n" or choice=="N"):
                    choice = input("Post a tag? (y/n): ")
                    if (choice=="y" or choice=="Y"):
                        data = input("Tag: ")
                        send_response(http2_connection, data, path='/tags', close_stream=False)
                        send_data(http2_connection.data_to_send(), connection)
                        break
                    elif (choice=="n" or choice=="N"):
                        data = input("Message to send: ")
                        send_response(http2_connection, data)
                        break
                    else:
                        print("Please write either 'y' or 'n'")
                        break
                else:
                    print("Please write either 'y' or 'n'")
                    break
            else:
                print("Please write either 'y' or 'n'")

        send_data(http2_connection.data_to_send(), connection)


if __name__ == "__main__":
    main()