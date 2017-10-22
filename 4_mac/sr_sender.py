#!/usr/bin/python3
import socket
import sys
import os
import logging
import pickle
from threading import Timer, Lock
from time import sleep

from common import *


logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s.%(msecs)-03d : %(message)s',
                datefmt='%H:%M:%S')


message, msglen, next_msg_char = '', 0, 0
pbuffer = [None] * SRP_WINDOW_SIZE
timers = [None] * SRP_WINDOW_SIZE
S_n, S_f, outstanding_frames = 0, 0, 0
sock, client = None, None
client_sync_lock = Lock()


def callback_timeout(index):
    # Resent pkt and restart timer
    with client_sync_lock:
        # Handle possible race condition silently
        if pbuffer[index] is not None:
            logging.info('[TIMEOUT]   :  Resending %s' % pbuffer[index])
            send_packet(client, pbuffer[index])
            start_timer(index)


# Start the timer for packet with given seqno
def start_timer(ind):
    timers[ind] = Timer(3, callback_timeout, args=(ind, ))
    timers[ind].start()


def stop_timer(ind):
    if timers[ind] is None:
        raise Error('Timer %d not running!' % ind)
    if timers[ind].is_alive():
        timers[ind].cancel()
    timers[ind] = None


def is_valid_ackno(ack):
    if outstanding_frames <= 0: return False
    seq = (S_f + 1) % (MAX_SEQ_NO + 1)
    while 1:
        if ack == seq: return True
        if seq == S_n: break
        seq = (seq + 1) % (MAX_SEQ_NO + 1)
    return False


def acknowledge_frames(ackno):
    global S_f, outstanding_frames
    frames_acknowledged = []
    if is_valid_ackno(ackno):
        while S_f != ackno:
            ind = S_f % SRP_WINDOW_SIZE
            pbuffer[ind] = None # Purge
            stop_timer(ind)
            frames_acknowledged.append(str(S_f))
            S_f = (S_f + 1) % (MAX_SEQ_NO + 1)
            outstanding_frames -= 1
    return frames_acknowledged


def handle_recvd_pkt(pkt_recvd):
    global outstanding_frames, S_f
    if pkt_recvd is None: return
    if pkt_recvd.is_corrupt():
        logging.info('[CHKSUMERR] : %s', pkt_recvd)
        return
    logging.info('[RECV]      :  Received %s.', pkt_recvd)
    if pkt_recvd.ptype == Packet.TYPE_NACK:
        ind = pkt_recvd.seq_no % SRP_WINDOW_SIZE
        if pbuffer[ind] and pbuffer[ind].seq_no == pkt_recvd.seq_no:
            logging.info('[NACK_SEND] : %s.', pbuffer[ind])
            stop_timer(ind)
            send_packet(client, pbuffer[ind])
            start_timer(ind)
    elif pkt_recvd.ptype == Packet.TYPE_ACK:
        ackno = pkt_recvd.seq_no
        frames = acknowledge_frames(ackno)
        logging.info('[ACK]       : %s frames acknowledged', ', '.join(frames))
    else:
        raise Error('Unknown packet type - %s', str(pkt_recv.ptype))


def main():
    global outstanding_frames, S_n, next_msg_char
    while 1:
        try:
            if outstanding_frames < SRP_WINDOW_SIZE and next_msg_char < msglen:
                pkt = Packet(seq_no=S_n, data=message[next_msg_char], 
                        ptype=Packet.TYPE_DATA)
                next_msg_char += 1
                ind = S_n % SRP_WINDOW_SIZE
                pbuffer[ind] = pkt
                logging.info('[SEND]      : %s', pkt)
                # Acquire lock before writing to client socket.
                with client_sync_lock:
                    send_packet(client, pkt)
                # Lock is released during __exit__ phase
                start_timer(ind)
                S_n = (S_n + 1) % (MAX_SEQ_NO + 1)
                outstanding_frames += 1
            # Wait a second
            sleep(1)
            # Check for an incoming packet.
            pkt_recvd = recv_packet_nblock(client)
            handle_recvd_pkt(pkt_recvd)
            if outstanding_frames == 0 and next_msg_char >= msglen:
                break
        except KeyboardInterrupt as e:
            break
            
    logging.info('Transfer complete!')
    client.close()
    sock.close()


if __name__ == '__main__':
    message = input('Enter a message : ')
    msglen = len(message)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 3300 if len(sys.argv) <= 1 else int(sys.argv[1])))
    sock.listen(5)
    client, _addr = sock.accept()
    main()
    sys.exit(0)

