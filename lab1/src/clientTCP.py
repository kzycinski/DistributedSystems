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
neighbour_socket = None
neighbour_ip = None
neighbour_port = None
has_token = False
protocol = None
logger_socket = None
conn = None

logger_ip = "230.0.0.0"
logger_port = 9000

token_lock = Lock()
next_lock = Lock()
conn_lock = Lock()


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
    global client_socket, neighbour_ip, neighbour_port, conn
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
        Thread(target=infinite_listening).start()
        print('exit')
    else:
        print("Connection error")
        exit(1)


def join_client():
    global client_socket, neighbour_ip, neighbour_port, neighbour_socket, conn
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


def infinite_listening():
    global conn
    while True:
        temp_conn, addr = client_socket.accept()
        conn_lock.acquire()
        conn.close()
        conn = temp_conn
        conn_lock.release()


def listening():
    global neighbour_ip, neighbour_port, neighbour_socket
    temp_conn, addr = client_socket.accept()
    msg = temp_conn.recv(4096).decode("utf-8")
    temp_conn.close()
    msg = msg.split(":")
    if msg[0] == str(TokenType.REQUEST.value):
        next_lock.acquire()
        neighbour_socket.close()
        neighbour_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        neighbour_socket.connect((msg[1], int(msg[2])))
        neighbour_socket.send(bytes("{}:{}:{}".format(TokenType.ACK.value, neighbour_ip, neighbour_port), 'utf-8'))
        neighbour_ip = msg[1]
        neighbour_port = msg[2]
        print("New next node - {}:{}".format(neighbour_ip, neighbour_port))
        next_lock.release()
    else:
        print("Connection error")
        exit(1)


def send_token():
    global has_token
    sleep(1)
    token_lock.acquire()
    if has_token:
        next_lock.acquire()
        neighbour_socket.send(bytes("{}".format(TokenType.TOKEN.value), 'utf-8'))
        has_token = False
        next_lock.release()
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
        conn_lock.acquire()
        buffer = conn.recv(4096)
        conn_lock.release()
        msg = str(buffer, 'utf-8')
        try:
            token_type = int(msg.split(":")[0])
        except ValueError:
            continue
        if token_type == TokenType.TOKEN.value:
            log_token()
            Thread(target=send_token).start()
        elif token_type == TokenType.MESSAGE.value:
            msg = msg.split(":")
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
                    next_lock.acquire()
                    neighbour_socket.send(buffer)
                    next_lock.release()


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
        next_lock.acquire()
        neighbour_socket.send(bytes(message, 'utf-8'))
        next_lock.release()
        has_token = False
        print("Message sent")
        token_lock.release()


def main():
    init()
    if has_token:
        Thread(target=send_token).start()
    Thread(target=receive_messages).start()
    Thread(target=send_messages).start()


if __name__ == '__main__':
    main()
