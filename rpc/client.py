from xmlrpc.client import ServerProxy
import sys


def help():
	print("Usage : remote_finger [-lmsp] user..")

if __name__ == '__main__':
	sys.argv = sys.argv[1:]
	if len(sys.argv) == 0:
		help()
		sys.exit(1)
	client = ServerProxy('http://localhost:8000')
	print(client.finger(sys.argv))
	sys.exit(0)