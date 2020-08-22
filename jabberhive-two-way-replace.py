#!/bin/env python3
import argparse
import re
import sys

import socket
import _thread

replacements = [
    ["!", " !"],
    ["?", " ?"],
    [".", " ."],
    [",", " ,"],
    [":", " :"],
    [";", " ;"],
    [")", " )"],
    ["(", "( "],
    [">", " >"],
    ["<", "< "],
    ["]", " ]"],
    ["[", "[ "],
    ["}", " }"],
    ["{", "{ "],
]

class ClientState:
    CLIENT_IS_SENDING_DOWNSTREAM = 1
    CLIENT_IS_SENDING_UPSTREAM = 2
    CLIENT_IS_CONNECTING = 3
    CLIENT_IS_TERMINATING = 4

def replace_client_to_server (string):
    prefix_size = (string.find(' ') + 1)
    prefix = string[:prefix_size]
    content = string[prefix_size:]

    for entry in replacements:
        content = content.replace(entry[0], entry[1])

    return (prefix + content)

def replace_server_to_client (string):
    prefix_size = (string.find(' ') + 1)
    prefix = string[:prefix_size]
    content = string[prefix_size:]

    for entry in replacements:
        content = content.replace(entry[1], entry[0])

    return (prefix + content)

def client_main (source, params):
    state = ClientState.CLIENT_IS_CONNECTING
    connect = None

    try:
        while True:
            if (state == ClientState.CLIENT_IS_SENDING_DOWNSTREAM):
                try:
                    in_data = b""

                    while True:
                        in_char = source.recv(1)
                        in_data = (in_data + in_char)

                        if (in_char == b"\n"):
                            break
                        elif (in_char == b''):
                            raise Exception("Disconnected client")

                    up_data = in_data.decode("UTF-8")
                    valid = 1
                except UnicodeDecodeError:
                    print("Could not decode UTF-8...")
                    valid = 0

                if (valid == 1):
                    up_data = replace_client_to_server(up_data)
                    connect.sendall(up_data.encode("UTF-8"))
                    state = ClientState.CLIENT_IS_SENDING_UPSTREAM
                else:
                    connect.sendall(in_data)
                    state = ClientState.CLIENT_IS_SENDING_UPSTREAM
            elif (state == ClientState.CLIENT_IS_SENDING_UPSTREAM):
                in_data = b""
                matched = 0
                c = b"\0"

                try:
                    while True:
                        in_char = connect.recv(1)
                        in_data = (in_data + in_char)

                        if (in_char == b"\n"):
                            break
                        elif (in_char == b''):
                            raise Exception("Disconnected server")


                    if ((in_data == b"!P \n") or (in_data == b"!N \n")):
                        print("Sending downstream without touching...")
                        state = ClientState.CLIENT_IS_SENDING_DOWNSTREAM
                    elif ((in_data.startswith(b"!GR "))):
                        print("Sending downstream, after checking...")
                        up_data = in_data.decode("UTF-8")
                        up_data = replace_server_to_client(up_data)
                        in_data = up_data.encode("UTF-8")

                except UnicodeDecodeError:
                    print("Could not decode UTF-8...")

                source.sendall(in_data)


            elif (state == ClientState.CLIENT_IS_CONNECTING):
                print("Connecting to downstream...")
                connect = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                connect.connect(params.destination)

                print("Sending downstream...")
                state = ClientState.CLIENT_IS_SENDING_DOWNSTREAM
            else:
                break
    except:
        print("Unexpected error:", sys.exc_info())
        print("Closing")
        source.close()
        connect.close()

################################################################################
## ARGUMENTS HANDLING ##########################################################
################################################################################

parser = argparse.ArgumentParser(
    description = (
        "Performs replacements both ways"
    )
)

parser.add_argument(
    '-s',
    '--socket-name',
    type = str,
    required = True,
    help = 'Name of the UNIX socket for this filter.'
)

parser.add_argument(
    '-d',
    '--destination',
    type = str,
    help = 'UNIX socket this filter sends to when a match is found.',
)

args = parser.parse_args()

################################################################################
## MAIN ########################################################################
################################################################################
server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

server_socket.bind(args.socket_name)
server_socket.listen(5)

while True:
    (client, client_address) = server_socket.accept()
    _thread.start_new_thread(client_main, (client, args))

