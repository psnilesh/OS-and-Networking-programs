import socket
import pickle
import re
import pwd

MAX_RESP_SIZE = 1024


class Response:

    def __init__(self, status=250, message=''):
        self.status = status
        self.message = message

    def get_status(self):
        return self.status

    def get_message(self):
        return self.message

    def __str__(self):
        return str(self.status) + "   " + self.message


def send_response(sock, dest, resp):
    raw_data = pickle.dumps(resp)
    if sock.sendto(raw_data, dest) != len(raw_data):
        raise socket.error("Transfer not completed.")
    return True


def recv_response(sock):
    data, addr = sock.recvfrom(MAX_RESP_SIZE)
    resp = pickle.loads(data)
    return resp, addr


def is_valid_mail(addr):
    if not re.fullmatch('[a-z0-9_\-]+@[a-z0-9_\-]+', addr, re.IGNORECASE):
        return False
    name, host = [s.strip() for s in addr.split('@')]
    #print(name, host)
    if host != socket.gethostname(): return False
    try:
        pwd.getpwnam(name)
        return True
    except KeyError:
        pass
    return False
        



