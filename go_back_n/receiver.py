import socket
import sys
import random
import logging as log
# Custom modules
from common import *


log.basicConfig(level=log.DEBUG, format='%(message)s')

# Socket for listening for incoming connections
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', int(sys.argv[1]) if len(sys.argv) >= 2 else 3300))
sock.listen(5)

# Accept a client connection
client, addr = sock.accept()
log.debug("Connected..")
expected_seq_no = 0

while True:
    # Wait for packet
    try:
        pkt = recv_packet(client)
        if pkt.is_corrupt():
            # Simply Drop the packet
            continue
        if pkt.get_seq() == expected_seq_no:
            log.info("[RECV]\t\t ==> Packet %d received." % pkt.get_data())
            expected_seq_no = (expected_seq_no + 1) % SEQ_NO_UPPER_BOUND
        else:
            log.info("[ERR]\t\t ==> Packet %d arrived out of order." % pkt.get_data())
            send_packet(client, Packet(expected_seq_no, ptype=Packet.TYPE_ACK))
    except socket.error as e:
        log.error(str(e))
    except KeyboardInterrupt as e:
        break

log.info("Closing..")
client.close()
sock.close()

sys.exit(0)







