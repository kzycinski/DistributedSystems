import sys
import socket
from enum import Enum
from threading import Thread, Lock
from time import sleep

client_id = None
client_port = None
client_ip = None
client_socket = None
neighbour_socket = None
neighbour_ip = None
neighbour_port = None
has_token = False
protocol = None
logger_socket = None


class TokenType(Enum):
    REQUEST = 1
    ACK = 2


def init():
    read_args()
    init_client()


def read_args():
    if len(sys.argv) != 7 and len(sys.argv) != 8:
        raise AttributeError("Wrong number of arguments, see Example file")

    global client_id, client_ip, client_port, neighbour_ip, neighbour_port, has_token, protocol
    client_id = sys.argv[1]
    client_ip = sys.argv[2]
    client_port = int(sys.argv[3])
    neighbour_ip = sys.argv[4]
    neighbour_port = int(sys.argv[5])
    protocol = sys.argv[6]

    if len(sys.argv) == 8 and sys.argv[7] == '1':
        has_token = True


def init_sockets():
    global client_socket, logger_socket, neighbour_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.bind((client_ip, client_port))
    neighbour_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Successfully initiated TCP client")
    print("This IP: {}:{}\n".format(client_socket.getsockname()[0], client_socket.getsockname()[1]))


def init_client():
    init_sockets()
    if client_ip == neighbour_ip and client_port == neighbour_port:
        start_new_client()
    else:
        join_client()


def start_new_client():
    global client_socket, neighbour_ip, neighbour_port
    client_socket.listen(1)
    print("Waiting for request...")
    conn, addr = client_socket.accept()
    message = conn.recv(4096).decode("utf-8")
    message = message.split(":")
    if message[0] == str(TokenType.REQUEST.value):
        answer = "{}:{}:{}".format(TokenType.ACK.value, neighbour_ip, neighbour_port)
        neighbour_ip = message[1]
        neighbour_port = int(message[2])
        neighbour_socket.connect((neighbour_ip, neighbour_port))
        neighbour_socket.send(bytes(answer, 'utf-8'))
        print("Connected, next node: {}:{}".format(neighbour_ip, neighbour_port))
        Thread(target=listening()).start()
    else:
        print("Connection error")
        exit(1)


def join_client():
    global client_socket, neighbour_ip, neighbour_port, neighbour_socket
    client_socket.listen(1)
    neighbour_socket.connect((neighbour_ip, neighbour_port))
    neighbour_socket.send(bytes("{}:{}:{}".format(TokenType.REQUEST.value, client_ip, client_port), 'utf-8'))
    print("Sent request, waiting for response...")
    conn, addr = client_socket.accept()
    message = conn.recv(4096).decode("utf-8")
    message = message.split(":")
    if message[0] == str(TokenType.ACK.value):
        if neighbour_ip != message[1] or neighbour_port != int(message[2]):
            neighbour_socket.close()
            neighbour_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            neighbour_ip = message[1]
            neighbour_port = int(message[2])
            neighbour_socket.connect((neighbour_ip, neighbour_port))
        print("Connected, next node: {}:{}".format(neighbour_ip, neighbour_port))
        Thread(target=listening).start()
    else:
        print("Connection error")
        exit(1)


def listening():
    sleep(1000)


def main():
    init()


if __name__ == '__main__':
    main()
