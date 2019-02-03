# -*- coding: utf-8 -*-

import h2.connection
import socket
import ssl
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


def get_http2_ssl_context():
    """
    This function creates an SSLContext object that is suitably configured for
    HTTP/2. If you're working with Python TLS directly, you'll want to do the
    exact same setup as this function does.
    """
    # Get the basic context from the standard library.
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

    # RFC 7540 Section 9.2: Implementations of HTTP/2 MUST use TLS version 1.2
    # or higher. Disable TLS 1.1 and lower.
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )

    # RFC 7540 Section 9.2.1: A deployment of HTTP/2 over TLS 1.2 MUST disable
    # compression.
    ctx.options |= ssl.OP_NO_COMPRESSION

    # RFC 7540 Section 9.2.2: "deployments of HTTP/2 that use TLS 1.2 MUST
    # support TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256". In practice, the
    # blacklist defined in this section allows only the AES GCM and ChaCha20
    # cipher suites with ephemeral key negotiation.
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")

    # We want to negotiate using NPN and ALPN. ALPN is mandatory, but NPN may
    # be absent, so allow that. This setup allows for negotiation of HTTP/1.1.
    ctx.set_alpn_protocols(["h2", "http/1.1"])

    try:
        ctx.set_npn_protocols(["h2", "http/1.1"])
    except NotImplementedError:
        pass

    return ctx


def negotiate_tls(tcp_conn, context):
    """
    Given an established TCP connection and a HTTP/2-appropriate TLS context,
    this function:

    1. wraps TLS around the TCP connection.
    2. confirms that HTTP/2 was negotiated and, if it was not, throws an error.
    """
    # Note that SNI is mandatory for HTTP/2, so you *must* pass the
    # server_hostname argument.
    tls_conn = context.wrap_socket(tcp_conn, server_hostname='localhost')

    # Always prefer the result from ALPN to that from NPN.
    # You can only check what protocol was negotiated once the handshake is
    # complete.
    negotiated_protocol = tls_conn.selected_alpn_protocol()
    if negotiated_protocol is None:
        negotiated_protocol = tls_conn.selected_npn_protocol()

    if negotiated_protocol != "h2":
        raise RuntimeError("Didn't negotiate HTTP/2!")

    return tls_conn


def send_response(conn, data):
    response_data = json.dumps(data).encode('utf-8')
    IPython.embed()
    conn.send_headers(
        headers=[
            ('content-length', str(len(response_data))),
            ('content-type', 'application/json'),
        ],
    )
    conn.send_data(
        data=response_data,
    )


def main():
    # Step 1: Set up your TLS context.
    context = get_http2_ssl_context()

    # Step 2: Create a TCP connection.
    connection = establish_tcp_connection()

    # Step 3: Wrap the connection in TLS and validate that we negotiated HTTP/2
    #tls_connection = negotiate_tls(connection, context)

    # Step 4: Create a client-side H2 connection.
    http2_connection = h2.connection.H2Connection()

    # Step 5: Initiate the connection
    http2_connection.initiate_connection()
    #tls_connection.sendall(http2_connection.data_to_send())
    connection.sendall(http2_connection.data_to_send())

    print("Connection set")
    #IPython.embed()
    while True:
        data = input("Message to send: ")
        send_response(http2_connection, data)



if __name__ == "__main__":
    main()
