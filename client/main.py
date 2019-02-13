import h2.connection
import socket
import time
import json
import argparse
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

def save_resource(data, name):
    f = open(name,"wb+")
    f.write(data)
    f.close

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-m","--multiplex", help="multiplex traffic", action="store_true")
    parser.add_argument("-p", "--push", help="push resources to client", action="store_true")
    args = parser.parse_args()

    connection = establish_tcp_connection()
    http2_connection = h2.connection.H2Connection()
    http2_connection.initiate_connection()
    connection.sendall(http2_connection.data_to_send())
    _ = connection.recv(65536)

    if args.multiplex:
        print("Multiplexing is set")
    if args.push:
        print("Server push is set")


    print("Connection set")

    if args.push:
        print("push ghet")
        # Get indexed resources
        send_response(http2_connection, "", path='/', method='GET', close_stream=False)
        
        # Recevie ack
        print("ACK:")
        print(http2_connection.receive_data(connection.recv(65536)))
        
        # Send GET request
        tosend = http2_connection.data_to_send()
        print(tosend)
        connection.sendall(tosend)
        print("GET Sent")

        # Receive response for get
        response = http2_connection.receive_data(connection.recv(65536))
        print("Response: ", end='')
        print(response)
        
        # Get resources
        for e in response:
            if isinstance(e, h2.events.DataReceived):
                resources = json.loads(u''+e.data.decode('utf-8'))

        # Fetch each of the resources
        for r in resources:
            print(resources[r])
            path = resources[r]
            send_response(http2_connection, "", path=path, method='GET', close_stream=False)
            connection.sendall(http2_connection.data_to_send())
            response = http2_connection.receive_data(connection.recv(65536))
            print(response)
            
            for e in response:
                if isinstance(e, h2.events.DataReceived):
                    print("Attempt to save "+path[1:])
                    save_resource(e.data, path[1:])

    elif args.multiplex:
        # Get indexed resources
        send_response(http2_connection, "", path='/', method='GET', close_stream=False)
        
        # Recevie ack
        print(http2_connection.receive_data(connection.recv(65536)))
        
        # Send GET request
        tosend = http2_connection.data_to_send()
        connection.sendall(tosend)

        # Receive response for get
        response = http2_connection.receive_data(connection.recv(65536))
        
        # Get resources
        for e in response:
            if isinstance(e, h2.events.DataReceived):
                resources = json.loads(u''+e.data.decode('utf-8'))

        resource_list = []

        # Fetch each of the resources
        for r in resources:
            resource_list.append([http2_connection.get_next_available_stream_id(), resources[r][1:]])
            send_response(http2_connection, "", path=resources[r], method='GET', close_stream=False)
        
        connection.sendall(http2_connection.data_to_send())
        time.sleep(1)
        response = http2_connection.receive_data(connection.recv(655360))
            
        for e in response:
            if isinstance(e, h2.events.DataReceived):
                for r in resource_list: 
                    if e.stream_id == r[0]: 
                        save_resource(e.data, r[1])

    else:
        # Get indexed resources
        send_response(http2_connection, "", path='/', method='GET', close_stream=False)
        
        # Recevie ack
        print(http2_connection.receive_data(connection.recv(65536)))
        
        # Send GET request
        tosend = http2_connection.data_to_send()
        connection.sendall(tosend)

        # Receive response for get
        response = http2_connection.receive_data(connection.recv(65536))
        
        # Get resources
        for e in response:
            if isinstance(e, h2.events.DataReceived):
                resources = json.loads(u''+e.data.decode('utf-8'))

        # Fetch each of the resources
        for r in resources:
            path = resources[r]
            send_response(http2_connection, "", path=path, method='GET', close_stream=False)
            connection.sendall(http2_connection.data_to_send())
            response = http2_connection.receive_data(connection.recv(65536))
            print(response)
            
            for e in response:
                if isinstance(e, h2.events.DataReceived):
                    print("Attempt to save "+path[1:])
                    save_resource(e.data, path[1:])



if __name__ == "__main__":
    main()