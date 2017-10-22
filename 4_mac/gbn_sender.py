import socket
import sys
import os
from threading import *
from common import *
from time import time, sleep
from math import floor
from collections import deque
import logging


sock  = None
pbuffer = deque([], maxlen=GBN_WINDOW_SIZE)
S_f, S_n = 0, 0
message, msglen = '', 0

# Time to wait for an acknowledgement.
ACK_WAIT_TIME = 3000

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                format='%(asctime)s.%(msecs)-03d : %(message)s',
                datefmt='%H:%M:%S')


class basic_timer:

    def __init__(self):
        self.start_time = None

    def start(self, interval):
        self.start_time = basic_timer.current_time_in_millis()
        self.interval = interval

    def has_timeout_occured(self):
        cur_time = basic_timer.current_time_in_millis()
        return cur_time - self.start_time > self.interval

    def is_running(self):
        return self.start_time != None

    def stop(self):
        self.start_time = None
        self.interval = None

    def restart(self, interval):
        self.start(interval)

    @staticmethod
    def current_time_in_millis():
        return int(floor(time() * 1000))


def outstanding_frames():
    return len(pbuffer) 


def is_valid_ackno(ack_no):
    if outstanding_frames() <= 0: return False
    t = (S_f + 1) % (MAX_SEQ_NO + 1)
    while t != S_n:
        if t == ack_no: return True
        t = (t + 1) % (MAX_SEQ_NO + 1)
    return ack_no == S_n


def main():
    global S_n, S_f, pbuffer

    timer = basic_timer()
    next_msg_index = 0
    while 1:
        while outstanding_frames() < GBN_WINDOW_SIZE and \
                                    next_msg_index < msglen:
            # There is space in buffer
            pack = Packet(S_n, data=message[next_msg_index])
            send_packet(client, pack)
            logging.info('[SEND]    : Sending %s.' % pack)
            pbuffer.append(pack)
            S_n = (S_n + 1) % (MAX_SEQ_NO + 1)
            if not timer.is_running():
                timer.start(ACK_WAIT_TIME)
            next_msg_index += 1

        sleep(.7)
        resp = recv_packet_nblock(client)

        if resp is not None and not resp.is_corrupt():
            if not is_valid_ackno(resp.seq_no):
                logging.info('[EACK]    : Invalid ACK %s.' % resp)
            else:
                # Remove packets from buffer
                tmp = []
                while len(pbuffer) > 0 and pbuffer[0].seq_no != resp.seq_no:
                    tmp.append(str(pbuffer.popleft().seq_no))
                    S_f = (S_f + 1) % (MAX_SEQ_NO + 1)
                logging.info(('[ACK]     : Ack received %s. Packets (%s) ' +\
                     'are acknowledged.') % ( resp, ','.join(tmp)))

        sleep(.8)

        if timer.has_timeout_occured():
            for p in pbuffer:
                logging.info('[TIMEOUT] : Resending %s.' % p)
                send_packet(client, p)
            timer.start(ACK_WAIT_TIME)

        if outstanding_frames() == 0 and next_msg_index >= msglen:
            logging.info('Transfer complete.')
            break
        # else
        sleep(1)


if __name__ == '__main__':

    message = input('Enter a message : ')
    msglen = len(message) 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 3300 if len(sys.argv) <= 1 else int(sys.argv[1])))
    sock.listen(5)
    client, _addr = sock.accept()
    main()
    sock.close()
    client.close()
