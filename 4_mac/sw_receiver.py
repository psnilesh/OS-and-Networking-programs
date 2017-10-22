import socket
import sys
import random
import logging

from common import *


logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s.%(msecs)-03d : %(message)s',
                datefmt='%H:%M:%S')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('', int(sys.argv[1]) if len(sys.argv) >= 2 else 3300))
recvd_data = []
expected_seq_no = 0


def to_network_layer(frame):
    recvd_data.append(frame)


while True:
    try:
        pack = recv_packet(sock)
        if pack.seq_no != expected_seq_no:
            logging.info("[ERR]  : %s arrived out of order." % pack)
            send_packet(sock, Packet(expected_seq_no, ptype=Packet.TYPE_ACK))
        else:
            # No need to replicate `packet not arrived` scenorio.
            if not pack.is_corrupt():
                expected_seq_no = 1 - expected_seq_no
                to_network_layer(pack.data)
                logging.info("[RECV] : %s" % pack)
                send_packet(sock,
                    Packet(expected_seq_no, Packet.TYPE_ACK))
                logging.info('[ACK]  : ack_no = %d' % expected_seq_no)
            else: 
        	   # Simply drop the packet. The timer at the sender will
        	   # eventually timeout and send the packet again.
                logging.debug("[CHKSERR] : Dropping %s" % pack)
    except ConnectionResetError:
        break
    except KeyboardInterrupt:
        break

logging.info("Closing connection..")
sock.close()
logging.info("Data received = %s", ''.join(recvd_data))
sys.exit(0)