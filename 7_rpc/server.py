from xmlrpc.server import SimpleXMLRPCServer
import subprocess
import sys


def finger(args):
    proc = subprocess.run(["finger", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout if proc.returncode == 0 else proc.stderr


if __name__ == '__main__':
    try:
        server = SimpleXMLRPCServer(( "localhost", 8000))
        server.register_function(finger, 'finger')
        print("Server running at port 8000 ..")
        server.serve_forever()

    except KeyboardInterrupt:
        print("Stopping server...")

    sys.exit(0)
