import socketserver
import common
import threading

class SLRPCHandler(socketserver.BaseRequestHandler):
    pass

class RPCServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    request_handler = SLRPCHandler

    def __init__(self, ip, port):
        self.address = Address(ip, port)
        super().__init__((ip, port), self.request_handler)

    def start(self, bg=False):
        if bg:
            self.thread = threading.Thread(target=self.serve_forever)
            self.thread.start()
        else:
            self.thread = None
            self.serve_forever()
