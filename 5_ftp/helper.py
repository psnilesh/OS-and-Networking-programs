import logging as log
import os
import pickle
import socket


log.basicConfig(level=log.DEBUG, format="%(message)s")

MAX_PACKET_LEN = 1024 * 1024 * 1024 * 5   # 5 MB max size


# FTP Request object
class FTPRequest:

    def __init__(self, command="", args=[]):
        self.command = command
        self.args = args

    def __str__(self):
        return self.command + '  ' +\
            ' '.join([s for s in self.args if isinstance(s, str)])


# FTP Response object
class FTPResponse:
    # Specifies the action to be taken with field data
    ACTION_DISPLAY = 1
    ACTION_SAVE = 2
    ACTION_IGNORE = 3

    def __init__(self, code=200, message="", data=b'', action=ACTION_IGNORE):
        self.code = code
        self.message = message
        self.data = data
        self.action = action  # Specifies what to do with :data

    def __str__(self):
        return "%d  %s" % (self.code, self.message)


class FileWrapper:

    def __init__(self, name='', content=b''):
        self._name = name
        self._content = content

    def size(self):
        return len(self._content)

    def get_content(self):
        return self._content

    def get_name(self):
        return self._name

    def write(self, loc='/tmp'):
        loc = os.path.join(loc, self._name)
        fd = open(loc, 'wb')
        fd.write(self._content)
        fd.close()

    def __str__(self):
        return self._name


"""
    Read exactly 'bc' bytes from the socket. This method will block till
    required bytes are read from the socket.
"""


def read_bytes(sock, bc=1):
    if sock is None or type(sock) != socket.socket:
        raise TypeError("socket expected!")
    data = b''
    while bc > 0:
        d = sock.recv(bc)
        data += d
        bc -= len(d)
    return data


"""
    Send an object through the socket to the other end using
    some custom protocol.
"""


def sock_send(sock, obj):
    if sock is None or type(sock) != socket.socket:
        raise TypeError("Socket error.")
    # Marshall Object
    data = pickle.dumps(obj)
    # Length in bytes
    size = len(data)
    # Packet size should not exceed MAX_PACKET_LEN
    if size > MAX_PACKET_LEN:
        raise OverflowError("Packet too large!")
    # Send packet size first
    sock.sendall((size).to_bytes(4, byteorder='big'))
    # Followed by payload
    sock.sendall(data)
    # Success
    return True


def sock_recv(sock):
    if sock is None:
        raise TypeError("Not a socket")
    # Read the size of incoming packet
    size = int.from_bytes(read_bytes(sock, 4), 'big')
    # Read 'size' bytes
    data = read_bytes(sock, size)
    # Unmarshall
    obj = pickle.loads(data)
    # Success
    return obj


def sock_ignore(sock):
    # Simply ignore the next packet
    sock_recv(sock)


COMMANDS = [
    "account", "cd", "get", "ls", "mkdir", "put", "pwd",
    "rmdir", "rename", "size", "?"
]
