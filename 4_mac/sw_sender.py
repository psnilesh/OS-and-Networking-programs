import socket
import sys
import common
import time
import logging as log

from common import *


logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s.%(msecs)-03d : %(message)s',
                datefmt='%H:%M:%S')


# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', int(sys.argv[1]) if len(sys.argv) >= 2 else 3300))
sock.listen(1)
next_seq_no = 0
message = input('Enter a message : ').strip()

client, _addr = sock.accept()

for char in message:
    pack = Packet(next_seq_no, ptype=Packet.TYPE_DATA, data=char)
    log.info('[SENT]    : %s' % pack)
    send_packet(client, pack)
    next_seq_no = 1 - next_seq_no
    ack = recv_packet(client, timeout=5)
    while ack is None or ack.is_corrupt() or \
          ack.ptype != Packet.TYPE_ACK or \
          ack.seq_no != next_seq_no:
        if ack is None:
            log.info('[TIMEOUT] : Sending %s again' % pack)
        elif ack.is_corrupt():
            log.info('[CHKSERR] : Received corrupted ACK packet.' + \
                     ' Sending %s again.' % pack)
        send_packet(client, pack)
        ack = recv_packet(client, timeout=5)
    log.info('[ACK]     : %s' % ack)
    time.sleep(1)


log.info('Closing chanel..')
client.close()
sock.close()
sys.exit(0)
