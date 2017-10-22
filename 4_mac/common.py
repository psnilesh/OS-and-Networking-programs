import socket
import pickle
from random import randint

# Bit available for seq no in frame header
SEQ_NO_BIT_WIDTH = 3

# Maximum possible seq no
MAX_SEQ_NO = (2 ** SEQ_NO_BIT_WIDTH) - 1

# Go back N buffer size
GBN_WINDOW_SIZE = MAX_SEQ_NO

# Selective Repeat buffer size
SRP_WINDOW_SIZE = 2 ** (SEQ_NO_BIT_WIDTH - 1)


class Packet:

    TYPE_DATA, TYPE_ACK, TYPE_NACK = range(3)

    def __init__(self, seq_no, data='', ptype=TYPE_DATA):
        self.seq_no = seq_no
        self.data = data
        self.ptype = ptype
        self.corrupt = 0

    def is_corrupt(self):
        if not self.corrupt:
            self.corrupt = randint(1, 10)
        return self.corrupt < 3

    def __str__(self):
        if self.ptype == Packet.TYPE_DATA:
            return 'Packet(seq_no=%d, data=%s)' % \
                 (self.seq_no, str(self.data))
        elif self.ptype == Packet.TYPE_NACK:
            return 'Packet(nack_no=%d)' % self.seq_no
        return 'Packet(ack_no=%d)' % self.seq_no


def read_k_bytes(sock, remaining=0):
    ''' 
        Read exactly `remaining` bytes from the socket.
        Blocks until the required bytes are available and
        return the data read as raw bytes. Call to this
        function blocks until required bytes are available
        in the socket.

        Arguments
        ---------
        remaining :- The no of bytes to read from socket.
    '''
    ret = b''  # Return byte buffer
    while remaining > 0:
        d = sock.recv(remaining)
        ret += d
        remaining -= len(d)
    return ret


def send_packet(sock, pack):
    ''' 
        Send a packet to remote socket. We first send
        the size of packet in bytes followed by the
        actual packet. Packet is serialized using 
        cPickle module.

        Arguments
        ---------
        sock  : Destination socket
        pack  : Instance of class Packet.
    '''
    if pack is None or (sock is None or type(sock) != socket.socket):
        return  # Nothing to send
    pack_raw_bytes = pickle.dumps(pack)
    dsize = len(pack_raw_bytes)
    sock.sendall(dsize.to_bytes(4, byteorder='big'))
    sock.sendall(pack_raw_bytes)
    return True


def recv_packet(sock, timeout=None):
    '''
        Receive a packet from the socket.

        Reads the size of packet first followed by the actual data.
        Packet is then de-serialized and returned as an instance 
        of class Packet.

        Arguments
        ----------
        sock    :- The socket to read from.
        timeout :- If None, the call will block till a packet is 
                   available. Else it will wait for specified seconds for 
                   a packet.

        Return None if no packet has arrived.
    '''
    if sock is None or type(sock) != socket.socket:
        raise TypeError('Socket expected!')
    # Read the size from the channel first
    if timeout is not None:
        # Do not wait for more that `timeout`  seconds
        sock.settimeout(timeout)  
    try:
        pack_len = int.from_bytes(read_k_bytes(sock, 4), 'big')
        # Switch to blocking mode
        sock.settimeout(None)
        pack = pickle.loads(read_k_bytes(sock, pack_len))
    except socket.timeout:
        pack = None
    finally:
        # Blocking mode
        sock.settimeout(None)  
    return pack



def recv_packet_nblock(sock):
    ''' 
        Peek the socket for a packet. If a packet is found,
        block till the entire packet is read and return it.
        If no packet was found, return None.

        Arguments
        ---------
        sock  : The socket object to read from
    '''
    sock.setblocking(False)
    try:
        size = int.from_bytes(read_k_bytes(sock, 4), 'big')
        sock.setblocking(True)
        return pickle.loads(read_k_bytes(sock, size))
    except BlockingIOError as be:
        return None
    finally:
        sock.setblocking(True)
