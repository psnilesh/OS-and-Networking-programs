import socket
import sys
import common
import time
import logging as log


# init
log.basicConfig(level=log.DEBUG, format='%(message)s')


# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', int(sys.argv[1]) if len(sys.argv) >= 2 else 3300))
next_seq_no = 0
packet_count = int(input("Enter no of packets : "))


for packet_id in range(1, packet_count + 1):
    pack = common.Packet(next_seq_no, ptype=common.Packet.TYPE_DATA, data=packet_id)
    log.info("[SEND]\t\t ==> Packet %d" % packet_id)
    common.send_packet(sock, pack)
    next_seq_no = 1 - next_seq_no
    ack = common.recv_packet(sock, timeout=5)
    while ack is None or ack.is_corrupted() or ack.get_type() != common.Packet.TYPE_ACK \
          or ack.get_seq() != next_seq_no:
        if ack is None:
            log.info("[TIMEOUT]\t ==> Sending Packet %d again" % packet_id)
        elif ack.is_corrupted():
            log.info("[CHKSERR]\t ==> Received corrupted ACK packet.")
        common.send_packet(sock, pack)
        ack = common.recv_packet(sock, timeout=5)
    log.info("[ACK]\t\t ==> Packet %d" % packet_id)
    # A slight delay for demo purposes
    time.sleep(1)

log.info("Closing chanel..")
sock.close()
sys.exit(0)
