import socket
import pickle
import random

# Constants

FRAME_HEADER_SEQ_NO_BIT_WIDTH = 2
SEQ_NO_UPPER_BOUND            = 1 << FRAME_HEADER_SEQ_NO_BIT_WIDTH
WINDOW_SIZE                   = SEQ_NO_UPPER_BOUND - 1


""" This class forms the basic transfer unit between the endpoints"""

class Packet:
    TYPE_DATA, TYPE_ACK = range(2)

    def __init__(self, seq_no=0, ptype=TYPE_DATA, data=b''):
        self._seq_no = seq_no
        self._data = data
        self._type = ptype
        self._corrupt = 0

    def get_seq(self):
        return self._seq_no

    def get_data(self):
        return self._data

    def get_type(self):
        return self._type

    def is_corrupt(self):
        if self._corrupt == 0:
            self._corrupt = random.randint(1, 10)
        return self._corrupt < 4


""" Read exactly `remaining` bytes from the socket.
    Blocks until the required bytes are available and
    returns the data read as raw bytes.
"""


def read_k_bytes(sock, remaining=0):
    ret = b''  # Return byte buffer
    while remaining > 0:
        d = sock.recv(remaining)
        ret += d
        remaining -= len(d)
    return ret


""" Send the packet. `pack` is an instance of Packet class. 
    The first 4 bytes specify the size of packet that 
    follows 
"""


def send_packet(sock, pack):
    if pack is None or (sock is None or type(sock) != socket.socket):
        return  # Nothing to send
    pack_raw_bytes = pickle.dumps(pack)
    dsize = len(pack_raw_bytes)
    sock.sendall(dsize.to_bytes(4, byteorder='big'))
    sock.sendall(pack_raw_bytes)
    return True



""" Read a Packet object from the socket. The protocol 
    dictates that first 4 bytes of the stream is the size (S) of
    the object in bytes.  Next S bytes read from the socket and
    and decoded to get a Packet object.

    @args timeout  If None, this call will block until a packet is 
                   available in the socket. If timeout = k, then
                   this method will wait k seconds for
                   a packet and return it, or None if no packet 
                   arrived within K seconds
"""


def recv_packet(sock, timeout=None):
    if sock is None or type(sock) != socket.socket:
        raise TypeError("Socket expected!")
    # Read the size from the channel first
    if timeout is not None:
        sock.settimeout(timeout)  # Do not wait for more that `timeout`  seconds
    try:
        pack_len = int.from_bytes(read_k_bytes(sock, 4), 'big')
        if pack_len is None:
            raise socket.timeout
        pack = pickle.loads(read_k_bytes(sock, pack_len))
    except socket.timeout:
        pack = None
    finally:
        sock.settimeout(None)  # Change back to blocking mode
    return pack
