import socket
import sys
import random
import logging
# Custom modules
import common
from common import Packet

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
# Create a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', int(sys.argv[1]) if len(sys.argv) >= 2 else 3300))
sock.listen(1)


expected_seq_no = 0
client, addr = sock.accept()
while True:
    try:
        pack = common.recv_packet(client)
        if pack.get_seq() != expected_seq_no:
            logging.info("[ERR]\t\t ==> Packet %d arrived out of order." % pack.get_data())
            # Send ack again
            common.send_packet(client, Packet(expected_seq_no, ptype=Packet.TYPE_ACK))
        else:
            # No need to replicate `packet not arrived` scenorio.
            if pack.is_corrupted():
                expected_seq_no = 1 - expected_seq_no
                print("[RECV]\t\t ==> Packet %d." % pack.get_data())
                common.send_packet(
                    client,
                    Packet(expected_seq_no, Packet.TYPE_ACK))
            else: 
        	   # Simply drop the packet. The timer at the sender will
        	   # eventually timeout and send the packet again.
                logging.debug("[DROP]\t\t ==> Dropping packet %d." % pack.get_data())
    except socket.error as e:
        logging.error(str(e))
    except KeyboardInterrupt:
        logging.info("Closing client..")
        break

sock.close()
sys.exit(0)

