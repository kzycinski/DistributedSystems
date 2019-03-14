from clientTCP import main as main_tcp
from clientUDP import main as main_udp
import sys

if len(sys.argv) != 7 and len(sys.argv) != 8:
    raise AttributeError("Wrong number of arguments, see Example file")

protocol = sys.argv[6]

if protocol == 'tcp':
    main_tcp()
elif protocol == 'udp':
    main_udp()
else:
    raise AttributeError("Wrong protocol, see example file")


