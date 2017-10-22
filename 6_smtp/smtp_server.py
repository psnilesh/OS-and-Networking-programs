import socket
import pwd
import sys
import re
import logging
from datetime import datetime
# Custom modules
from common import *

MAX_MESSAGE_SIZE = 1024 * 4
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

TEMPLATE = """

From {sender}  {formatted_date}
Return-Path: <{sender}>
X-Original-To: <{target}>
Delivered-To: <{target}>
Received: from {hostname} {ip}
        by {hostname}
        for {target}; {formatted_date}
Date: {formatted_date}
From: {sender}
Status: 0

{message}
  
"""

class SmtpServer:

    PATTERN = {
        'helo' : re.compile('HELO +[a-z0-9\-_]+', re.IGNORECASE),
        'from' : re.compile('MAIL FROM: *<[a-z0-9_@.\-]+>', re.IGNORECASE),
        'rcpt' : re.compile('RCPT TO: *<[a-z0-9_@.\-]+>', re.IGNORECASE),
    }

    def __init__(self, hostname='', port=3300):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((hostname, port))
        self.connected = False
        self.next_handler = self.handle_helo
        # Details regarding email
        self.sender_ip = ''
        self.sender_host = 'unknown-hostname'
        self.mail_from = None
        self.recps = []
        self.data = ''

    def connect(self):
        msg, addr = self.sock.recvfrom(MAX_MESSAGE_SIZE)
        self.connected = True
        self.next_handler = self.handle_helo
        logging.info("Connected with %s." % str(addr))
        self.sender_ip = addr[0]
        send_response(self.sock, addr, 
            Response(220, 
                     socket.gethostname() + ' (Linux) MySMTPServer v0.1'))

    def accept(self):
        if not self.connected:
            raise Exception("Cannot proceed without a valid connection.")
        self.msg, addr = self.sock.recvfrom(MAX_MESSAGE_SIZE)
        # Call the current handler function
        self.msg = self.msg.decode('utf8')
        logging.debug("Received \"%s\" from %s." % ( self.msg, str(addr)))
        # Call the current handler function
        resp = self.next_handler()
        if resp is not None:
            send_response(self.sock, addr, resp) 

    def handle_helo(self):
        if self.msg.lower().startswith('helo'):
            if not SmtpServer.PATTERN['helo'].fullmatch(self.msg):
                return Response(501, 'Syntax: HELO hostname')
            self.sender_host = self.msg.split(' ')[1]
            return Response(250, socket.gethostname())
        elif self.msg.lower().startswith('mail from:'):
            return self.handle_mail()
        return SmtpServer.invalid_command()

    def handle_mail(self):
        if not SmtpServer.PATTERN['from'].fullmatch(self.msg):
            return Response(501, '5.5.4 Syntax: MAIL FROM: <address>')
        lt_index, gt_index = self.msg.find('<'), self.msg.find('>')
        self.mail_from = self.msg[lt_index + 1: gt_index]
        self.next_handler = self.handle_rcpt
        return Response(250, '2.1.0 Ok')

    def handle_rcpt(self):
        if not SmtpServer.PATTERN['rcpt'].fullmatch(self.msg):
            return Response(501, '5.5.4 Syntax: RCPT TO: <address>')
        lt_index, gt_index = self.msg.find('<'), self.msg.find('>')
        to = self.msg[lt_index + 1 : gt_index]
        if not is_valid_mail(to):
            return Response(550,  ('5.1.1 %s: Recipient address rejected: ' + \
                'User unknown in local recipient table') % \
                self.msg[lt_index : gt_index + 1])
        self.next_handler = self.handle_data
        self.recps.append(to)
        return Response(250, '2.1.5 Ok')

    def handle_data(self):
        if self.msg.lower().startswith('rcpt'):
            return self.handle_rcpt()
        elif self.msg.lower() == 'data':
            self.next_handler = self.store_data
            self.data = ''
            return None
        return SmtpServer.invalid_command()

    def store_data(self):
        if self.msg == '.':
            self.save_mail()
            self.reset()
            return Response(250, 'Ok')
        self.data += self.msg

    def save_mail(self):
        # print(TEMPLATE.format(sender=self.mail_from, \
        #                       target=self.recps[0],
        #                       hostname=self.sender_host,
        #                       message=self.data,
        #                       formatted_date='Sat, Sep 2 22:15:20 +05:30',
        #                       ip=self.sender_ip))
        for user in self.recps:
            fp = open("/var/mail/" + user[:user.find('@')], 'a')
            fp.write(TEMPLATE.format(sender=self.mail_from, \
                              target=user,
                              hostname=self.sender_host,
                              message=self.data,
                              formatted_date=datetime.now().ctime(),
                              ip=self.sender_ip))
            fp.close()
        return Response(250, 'Ok. Message queued.')

    def reset(self):
        self.mail_from = None
        self.recps = []
        self.next_handler = self.handle_helo
        self.data = b''
        self.sender_host = None

    @staticmethod
    def invalid_command():
        return Response(502, '5.5.2 Error: command not recognized.')


if __name__ == '__main__':
    server = SmtpServer('', 3300 if len(sys.argv) < 2 else int(sys.argv[1]))
    logging.info("Waiting for connection..")
    server.connect()
    while True:
        try:
            server.accept()
        except KeyboardInterrupt:
            break
    logging.info("closing server..")
    sys.exit(0)
