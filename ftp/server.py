#!/usr/bin/python3
import socket
import os
import sys
import logging as log
import pwd
import subprocess

import auth
from helper import *


log.basicConfig(format="[%(levelname)s]  %(message)s", level=log.DEBUG)


class ServerError(Exception):
    pass


class RequestHandler:

    COMMAND_PREFIX = 'command__'

    def __init__(self):
        methods = [
            m for m in dir(RequestHandler)
            if m.startswith(RequestHandler.COMMAND_PREFIX)]
        self.commands = [
            c[len(RequestHandler.COMMAND_PREFIX):]
            for c in methods if callable(getattr(RequestHandler, c))]
        self.anonymous = False
        self.is_authenticated = False
        self.user_data = None

    def handle_request(self, req):
        if type(req) != FTPRequest:
            raise TypeError("Expected an instance of FTPRequest.")
        if req.command not in self.commands:
            return FTPResponse(404, 'Query not valid!')
        try:
            return getattr(
                self,
                RequestHandler.COMMAND_PREFIX + req.command)(*req.args)
        except TypeError as e:
            return FTPResponse(401, str(e))

    def command__auth(self, username, password):
        try:
            if username == 'anonymous':
                self.is_authenticated = True
                self.anonymous = True
            else:
                user_id = auth.authenticate(username, password)
                if user_id is None:  # Authentication failed
                    return FTPResponse(530, 'Login Incorrect')
                self.is_authenticated = True
                self.anonymous = False
                self.user_data = pwd.getpwnam(username)
                # Change effective user id of the program
                os.seteuid(user_id)
                os.chdir(self.user_data.pw_dir)
                return FTPResponse(
                    230,
                    'User ' + username +
                    " logged in.\nUsing binary mode to" +
                    " transfer files.")
        except ValueError:
            return FTPResponse(530, "Login incorrect.\nLogin failed.")

    def command__pwd(self):
        return FTPResponse(
            257,
            '\"%s\" is the current directory.' % os.getcwd())

    def command__cd(self, target=None):
        try:
            os.chdir(target if target is not None else self.user_data.pw_dir)
            return FTPResponse(250, 'CWD command successful')
        except Exception as e:
            return FTPResponse(550, '%s : %s' % (target, str(e)))

    def command__ping(self):
        return FTPResponse(200)

    def command__ls(self, *_args):
        args = list(_args)
        args.insert(0, "ls")
        proc = subprocess.Popen(
            args,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return FTPResponse(
                200,
                'Successfull',
                stdout,
                FTPResponse.ACTION_DISPLAY)
        return FTPResponse(
            226,
            'Transfer complete.',
            data=stderr,
            action=FTPResponse.ACTION_DISPLAY)

    def command__mkdir(self, *_args):
        args = list(_args)
        args.insert(0, "mkdir")
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return FTPResponse(
                257,
                '"%s" directory(s) created.' % (' '.join(_args)))
        return FTPResponse(550, '', stderr, FTPResponse.ACTION_DISPLAY)

    def command__rmdir(self, *_args):
        args = list(_args)
        args.insert(0, "rmdir")
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return FTPResponse(
                250, "RMD command successfull.")
        return FTPResponse(550, stderr)

    def command__size(self, *args):
        try:
            if not os.path.isfile(args[0]):
                raise OSError('File doesnt exists or is a directory.')
            st_info = os.stat(args[0])
            return FTPResponse(213, str(st_info.st_size))
        except OSError:
            return FTPResponse(500, '%s: not a plain file' % args[0])
        except KeyError:
            return FTPResponse(552, 'No filename provided.')

    def command__get(self, arg_filename=''):
        try:
            file = os.path.join(os.getcwd(), arg_filename)
            if not os.path.isfile(file):
                return FTPResponse(
                    550,
                    '%s : No such file or directory.' % arg_filename,
                    data=None,
                    action=FTPResponse.ACTION_IGNORE)
            return FTPResponse(
                226,
                'Transfer Complete',
                data=FileWrapper(
                    arg_filename,
                    open(file, 'rb').read()),
                action=FTPResponse.ACTION_SAVE)
        except Exception as e:
            return FTPResponse(550, str(e))

    def command__put(self, wrapper=FileWrapper()):
        if type(wrapper) != FileWrapper or wrapper is None:
            return FTPResonse(520, 'Bad Request.')
        try:
            file_path = os.path.join(os.getcwd(), wrapper.get_name())
            if os.path.exists(file_path):
                return FTPResponse(527,
                    '%s already exists in this directory.' % wrapper.get_name())
            wrapper.write(os.getcwd())
            return FTPResponse(226, 'Transfer complete.')
        except OSError as e:
            return FTPResponse(530, str(e))

    def shutdown(self):
        self.is_authenticated = False
        self.anonymous = False
        self.user_data = None
        # Revert back to the privileaged user
        os.seteuid(0)


class FTPServer:

    def __init__(self):
        self.sock = None
        self.max_connections = 5
        self.handler = RequestHandler()

    def bind_server(self, port=3302):
        if self.sock is not None:
            raise ServerError("Server alreading up and running!")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', port))
        log.info("Server running (localhost, %s) .. " % str(port))
        self.sock.listen(self.max_connections)

    def accept(self):
        if self.sock is None:
            raise ServerError("Call bind_server first.")
        client, addr = self.sock.accept()
        log.info("Connection received from  %s .. " % str(addr))
        sock_ignore(client)
        sock_send(client, FTPResponse(
            220,
            socket.gethostname() +
            ' FTP Server (Linux) Ready.'))
        self.main(client, addr)

    def main(self, client, addr):
        while True:
            req = sock_recv(client)
            log.info(req)
            if (req.command == 'close'):
                break
            response = self.handler.handle_request(req)
            sock_send(client, response)
        log.info("Detatching from %s .. " % str(addr))
        client.close()  # Close the socket
        self.handler.shutdown()

    """ Close the socket and clear all flags """
    def close(self):
        if self.sock is not None:
            log.info("Closing connection .. ")
            self.sock.close()
            self.sock = None
            self.handler.shutdown()


# Main loop
if __name__ == '__main__':
    serv = FTPServer()
    serv.bind_server(3302)
    while True:
        try:
            serv.accept()
        except KeyboardInterrupt:
            serv.close()
            break
        except Exception as e:
            log.error(e)
    # Goodbye !
    sys.exit(0)
