import sys
import socket
from enum import Enum
from threading import Thread, Lock
from time import sleep
from datetime import datetime

client_id = None
client_port = None
client_ip = None
client_socket = None

neighbour_ip = None
neighbour_port = None

has_token = False

protocol = None

conn = None

logger_ip = "230.0.0.0"
logger_port = 9000
logger_socket = None

token_lock = Lock()



class TokenType(Enum):
    REQUEST = 1
    ACK = 2
    TOKEN = 3
    MESSAGE = 4


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
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((client_ip, client_port))
    logger_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Successfully initiated TCP client")
    print("This IP: {}:{}\n".format(client_socket.getsockname()[0], client_socket.getsockname()[1]))


def init_client():
    init_sockets()


def join_client():
    print("Connecting to token ring...")
    message = "{}:{}".format(TokenType.REQUEST.value, neighbour_ip)
    client_socket.sendto(bytes(message, 'utf-8'), (neighbour_ip, neighbour_port))



def send_token():
    global has_token
    sleep(1)
    token_lock.acquire()
    if has_token:
        client_socket.sendto(bytes("{}".format(TokenType.TOKEN.value), 'utf-8'), (neighbour_ip, neighbour_port))
        has_token = False
    token_lock.release()


def log_token():
    global has_token
    token_lock.acquire()
    logger_socket.sendto(bytes("{} - {} got token".format(datetime.now(), client_id), 'utf-8'), (logger_ip, logger_port))
    has_token = True
    token_lock.release()


def receive_messages():
    global has_token, neighbour_ip, neighbour_port
    buffer = []
    while True:
        buffer, source_address = client_socket.recvfrom(4096)
        msg = str(buffer, 'utf-8')
        msg = msg.split(":")
        try:
            token_type = int(msg[0])
        except ValueError:
            continue
        if token_type == TokenType.TOKEN.value:
            log_token()
            Thread(target=send_token).start()
        elif token_type == TokenType.MESSAGE.value:
            if msg[1] == client_ip and int(msg[2]) == client_port:
                log_token()
                print("Got message from {}: \n '{}'".format(msg[3], msg[4]))
                Thread(target=send_token).start()
            else:
                if msg[4] == client_id:
                    log_token()
                    print("Message came back to me, deleting.")
                    Thread(target=send_token).start()
                else:
                    print("Forwarding message...")
                    sleep(1)
                    logger_socket.sendto(bytes("{} - {} got token".format(datetime.now(), client_id), 'utf-8'),
                                         (logger_ip, logger_port))
                    client_socket.sendto(buffer, (neighbour_ip, neighbour_port))

        elif token_type == TokenType.REQUEST.value:
            message = "{}:{}:{}:{}".format(TokenType.ACK.value, source_address[0], neighbour_ip, neighbour_port)
            client_socket.sendto(bytes(message, 'utf-8'), source_address)
            neighbour_ip = source_address[0]
            neighbour_port = int(source_address[1])

        elif token_type == TokenType.ACK.value:
            if msg[1] == client_ip:
                neighbour_ip = msg[2]
                neighbour_port = int(msg[3])
            print("Connected.")


def send_messages():
    global has_token
    while True:
        receiver = input("Enter receiver data ( IP:PORT ):\n")
        message = input("Enter message: \n")
        receiver_ip = receiver.split(':')[0]
        receiver_port = receiver.split(':')[1]
        message = "{}:{}:{}:{}:{}".format(TokenType.MESSAGE.value, receiver_ip, receiver_port, client_id, message)
        token_lock.acquire()
        while not has_token:
            token_lock.release()
            sleep(1)
            token_lock.acquire()
        client_socket.sendto(bytes(message, 'utf-8'), (neighbour_ip, neighbour_port))
        has_token = False
        print("Message sent")
        token_lock.release()


def main():
    init()
    if has_token:
        Thread(target=send_token).start()
    if client_ip != neighbour_ip or client_port != neighbour_port:
        join_client()
    Thread(target=receive_messages).start()
    Thread(target=send_messages).start()


if __name__ == '__main__':
    main()
