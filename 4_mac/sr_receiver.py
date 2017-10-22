#!/usr/bin/python3
import socket
import sys
import os
import logging
from time import sleep

from common import *


logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s.%(msecs)-03d : %(message)s',
                datefmt='%H:%M:%S')
sock = None
R_n = 0
pbuffer  = [None] * SRP_WINDOW_SIZE
nack_sent, ack_needed = False, False
data_recvd = []


def send_nack():
    pkt = Packet(seq_no=R_n, data=b'', ptype=Packet.TYPE_NACK)
    send_packet(sock, pkt)
    logging.info('[NACK]    :  %s' % pkt)
    

def send_ack():
    pkt = Packet(seq_no=R_n, ptype=Packet.TYPE_ACK)
    send_packet(sock, pkt)
    logging.info('[ACK]     :  %s' % pkt)
    
    
def is_valid_seqno(seqno):
    return seqno in [(R_n + i) % (MAX_SEQ_NO + 1) for i in range(SRP_WINDOW_SIZE)]
    

def to_network_layer(char):
    data_recvd.append(char)
        
    
def main():
    global nack_sent, ack_needed, R_n
    while 1:
        pkt = recv_packet(sock)
        # print('--received %s', pkt)
        if pkt.is_corrupt():
            if not nack_sent:
                send_nack()
                nack_sent = True
            continue
            
        if pkt.seq_no != R_n and not nack_sent:
            send_nack()
            nack_sent = True

        if is_valid_seqno(pkt.seq_no):
            if pbuffer[pkt.seq_no % SRP_WINDOW_SIZE] is None:
                pbuffer[pkt.seq_no % SRP_WINDOW_SIZE] = pkt
                logging.info('[RECV]    :  %s' % pkt)
                while pbuffer[R_n % SRP_WINDOW_SIZE]:
                    to_network_layer(pbuffer[R_n % SRP_WINDOW_SIZE].data)
                    pbuffer[R_n % SRP_WINDOW_SIZE] = None # Purge
                    R_n = (R_n + 1) % (MAX_SEQ_NO + 1)
                    ack_needed = True
                if ack_needed:
                    send_ack()
                    ack_needed = False
                    nack_sent = False
        elif nack_sent:
            send_ack()
        sleep(.75)
       
       
if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('', 3300 if len(sys.argv) <= 1 else int(sys.argv[1])))
    try:
        main()
    except ConnectionResetError:
        pass
    logging.info('Transfer complete. Received \'%s\'' % ''.join(data_recvd))
    sys.exit(0)

