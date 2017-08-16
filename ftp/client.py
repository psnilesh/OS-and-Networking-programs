#!/usr/bin/python3
import socket
import os
import sys
import logging as log
import getpass

from helper import *


log.basicConfig(format="[%(levelname)s]  %(message)s", level=log.DEBUG)


class FTPError(Exception):
    pass


class FTPClient:
    def __init__(self):
        self.sock = None
        self.is_connected = False
        self.is_authenticated = False
        self.server_name = ''

    # Establish a connection with remote FTP host
    def open(self, hostname='', port=3302):
        if self.is_connected:
            raise FTPError(
                'Already connected to %s, use close first.' % self.server_name)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        try:
            port = int(port)
        except ValueError:
            raise FTPError("Bad port address.")
        self.sock.connect((hostname, port))
        # Ping the server
        sock_send(self.sock, FTPRequest('ping'))
        # Print response
        print(sock_recv(self.sock))
        self.server_name = hostname  # Save hostname for later
        self.is_connected = True
        # Initialise authentication procedure
        self.init_auth()

    def is_open(self):
        return self.is_connected

    def init_auth(self):
        username = input("Name (%s) : " % self.server_name).strip()
        passwd = getpass.getpass("Password : ")
        # Authenticate with server
        sock_send(self.sock, FTPRequest('auth', [username, passwd]))
        response = sock_recv(self.sock)
        if response.code // 100 != 2:
            raise FTPError('%d %s' % (response.code, 'Login Incorect.'))
        print(response.message)
        self.is_authenticated = True

    def send(self, query):
        if not self.is_connected:
            raise FTPError('Not Connected.')
        if not self.is_authenticated:
            raise FTPError('530 Please login with USER and PASS.')
        if len(query) == 0:
            return None  # Silently ignore
        elif query[0] == 'get' or query[0] == 'put':
            if len(query) != 2:
                raise FTPError('Please provide a filename.')
            if query[0] == 'put':
                try:
                    pack = FTPRequest('put', [
                        FileWrapper(query[1],
                                    open(query[1], 'rb').read())])
                    sock_send(self.sock, pack)
                    return sock_recv(self.sock)
                except OSError as oe:
                    raise FTPError(str(oe))
        # else
        pack = FTPRequest(query[0], query[1:])
        sock_send(self.sock, pack)
        return sock_recv(self.sock)

    def close(self):
        if (self.sock is not None):
            sock_send(self.sock, FTPRequest('close'))
            self.sock.close()
            self.is_connected = False
            self.is_authenticated = False
            self.server_name = ''
            self.sock = None


client = FTPClient()


def main():
    global client
    while True:
        try:
            query = input("ftp> ").strip().split(" ")
            if len(query) == 0:
                continue
            if query[0] == '?':
                # Show a list of available features
                print('  '.join(COMMANDS))
            elif query[0] == 'open':
                # Establish a remote connection
                if len(query) == 1:
                    query.append(input("(to) "))
                client.open(query[1], query[2] if len(query) > 2 else 3302)
            elif query[0] == 'close':
                client.close()
                log.info("Disconnected.")
            elif query[0] == 'exit':
                client.close()
                break
            elif query[0] == 'lcd':
                try:
                    if len(query) == 2:
                        os.chdir(query[1])
                except Exception as e:
                    raise FTPError(str(e))
            elif query[0] not in COMMANDS:
                    log.error("Invalid command. Type ? for help")
            else:
                response = client.send(query)
                if response.action == FTPResponse.ACTION_DISPLAY:
                    log.info(response)
                    log.info(response.data.decode('utf8'))
                elif response.action == FTPResponse.ACTION_SAVE:
                    if type(response.data) != FileWrapper:
                        raise TypeError(
                            "Expected type of FileWrapper in Response.data." +
                            " Got %s." % str(type(response.data)))
                    try:
                        response.data.write(os.getcwd())
                        log.info(str(response))
                    except OSError as e:
                        log.error(str(e))
                elif response.action == FTPResponse.ACTION_IGNORE:
                    log.info(response)

        except FTPError as fe:
            log.error(str(fe))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        if client is not None:
            client.close()
            client = None
    sys.exit(0)
