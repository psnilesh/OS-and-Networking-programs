import socket
import sys
import time
from threading import Timer
import logging as log
# Custom
from common import *


log.basicConfig(level=log.DEBUG, format='%(message)s')

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', int(sys.argv[1]) if len(sys.argv) >= 2 else 3300))

packet_count = int(input("Enter no of packets : "))


# Window variables for next_seq_no and first outstanding frame
S_n = S_f = 0
# Buffer for storing packets
pbuffer = [None] * WINDOW_SIZE
# Buffer pointers
bstart = bend = 0
# An integer value unique to every packet
i = 1
# Timer 
clock = None
# No of outstanding frames
frames_out = 0


def callback(*args):
    # Send all outstanding packets again
    log.info("[TIMEOUT]\t ==> Timeout occured for the first outstanding packet.")
    i = bstart + 1
    while i != bend:
        log.info("[SEND]\t\t ==> Packet %d sent again." % pbuffer[i].get_data())
        send_packet(sock, pbuffer[i])
        i = (i + 1) % WINDOW_SIZE
    send_packet(sock, pbuffer[bend])
    # Start timer again
    start_timer()


def is_timer_running():
    return clock is not None and clock.isAlive()


def start_timer():
    global clock
    clock = Timer(5, callback)
    clock.start()


def stop_timer():
    clock.cancel()
    clock = None


def restart_timer():
    if is_timer_running:
        stop_timer()
    start_timer()


def has_valid_ack_no(pkt):
    if S_f == S_n: # Window empty. No seq no will be valid
        return False
    ackno = pkt.get_seq()
    if S_f < S_n:
        return S_f + 1 <= ackno <= S_n
    return (0 <= ackno <= S_n or S_f + 1 <= ackno < SEQ_NO_UPPER_BOUND)


def is_ack_valid(ack):
    return ack is not None and ack.get_type() == Packet.TYPE_ACK and \
    not ack.is_corrupt() and has_valid_ack_no(ack)


def is_buffer_full():
    return frames_out == WINDOW_SIZE


while True:
    if  not is_buffer_full(): # ie. window is not yet full
        # Save packet onto buffer
        pbuffer[bend] = Packet(S_n, ptype=Packet.TYPE_DATA, data=i)
        send_packet(sock, pbuffer[bend])
        # Update next free seq_no
        S_n = (S_n + 1) % SEQ_NO_UPPER_BOUND
        # Update buffer pointer
        bend = (bend + 1) % WINDOW_SIZE
        # Timer update
        if not is_timer_running():
            start_timer()
        # Increment packet_id
        i += 1
        frames_out += 1
    # Check for an ack packet
    try:
        ack = recv_packet(sock, 0)
        if is_ack_valid(ack):
            stop_timer()
            # Purge all acknowledged frames from buffer
            while frames_out != 0 and pbuffer[bstart].get_seq() != ack.get_seq():
                pbuffer[bstart] = None
                bstart = (bstart + 1) % WINDOW_SIZE
                frames_out -= 1
            if frames_out  != 0:
                S_f = ack.get_seq()
                restart_timer()
            else:
                # No more packets remaining
                stop_timer() 
                if i >= packet_count: break
    except BlockingIOError as e:
        pass
    finally:
        time.sleep(.55)

print("Transfer complete!")
sys.exit(0)




