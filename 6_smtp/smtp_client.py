import socket
import sys
import logging
from common import *


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Setup hostname and port from CL args, if available
hostname = 'localhost' if len(sys.argv) < 2 else sys.argv[1]
port = 3300 if len(sys.argv) < 3 else int(sys.argv[2])

address = (hostname, port)

try:
    # Send a connect message to server. Only needed in UDP.
    sock.sendto(b'connect', address)
except socket.error as e:
    log.error(str(e))
    sys.exit(1)

wait_for_response = True

while True:
    try:
        if wait_for_response:
            resp, _ = recv_response(sock)
            logging.info(str(resp))
            if resp.get_status() == 221: 
                logging.error("Connection closed by foreign host.")
                break
        # Read next input
        line = input(">> ").strip()
        if len(line) > 0:
            if line.lower() == 'quit':
                break
            elif line.lower() == 'data':
                wait_for_response = False
            elif line.lower() == '.' and not wait_for_response:
                wait_for_response = True
            sock.sendto(line.encode('ascii'), address)
    except KeyboardInterrupt as ke:
        logging.info('Closing connection')
        break

sock.close()
sys.exit(0)
