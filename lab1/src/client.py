import sys
import socket

client_id = None
client_port = None
client_ip = None
client_socket_tcp = None
client_socket_udp = None
neighbour_ip = None
neighbour_port = None
has_token = False
protocol = None
logger_socket = None


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


def init_tcp_client():
    global client_socket_tcp, logger_socket
    client_socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket_tcp.bind((client_ip, client_port))
    logger_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("Successfully initiated TCP client")
    print("This IP: {}:{}\n".format(client_socket_tcp.getsockname()[0], client_socket_tcp.getsockname()[1]))


def init_udp_client():
    pass


def init():
    read_args()
    if protocol == 'tcp':
        init_tcp_client()
    elif protocol == 'udp':
        init_udp_client()
    else:
        raise AttributeError("Protocol has to be tcp or udp, see Example")


def main():
    init()


if __name__ == '__main__':
    main()
