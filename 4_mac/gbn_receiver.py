import socket
import sys
import random
import logging


from common import *


logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s.%(msecs)-03d  %(message)s',
                datefmt='%H:%M:%S')

# Socket for listening for incoming connections
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('', 3300 if len(sys.argv) <= 1 else int(sys.argv[1])))
logging.debug('Connected..')
expected_seq_no = 0

data_recvd = []

while True:
    try:
        # Wait for packet
        pkt = recv_packet(sock)
        if pkt.is_corrupt():
            continue
        if pkt.seq_no == expected_seq_no:
            logging.info('[RECV]  : Received %s.' % pkt)
            expected_seq_no = (expected_seq_no + 1) % (MAX_SEQ_NO + 1)
            data_recvd.append(pkt.data)
        else:
            logging.info('[ERR]   :  %s arrived out of order.' % pkt)
        ack_pkt = Packet(expected_seq_no, ptype=Packet.TYPE_ACK)
        logging.info('[ACK]   : %s' % ack_pkt)
        send_packet(sock, ack_pkt)
    except socket.error as e:
        logging.error(str(e))
        break
    except KeyboardInterrupt as e:
        break

logging.info('Transfer complete. Data received = \"%s\"' % ''.join())
sock.close()

sys.exit(0)







