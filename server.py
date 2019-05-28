from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from threading import Thread
from os import path


class AbstractTokenHandler(BaseHTTPRequestHandler):
    @property
    def client():
        pass

    @property
    def listener(self):
        pass

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        script_dir = path.dirname(path.realpath(__file__))
        file_path = path.join(script_dir, "index.html")
        with open(file_path, "rb") as file:
            data = file.read()
            self.wfile.write(data)

        params = parse_qs(self.path[2:])

        if "code" in params:
            Thread(target=self.client.stop).start()
            self.listener(params["code"][0])


class OAuthServer(object):
    def __init__(self, address, port, listener=(lambda code: code)):
        self._address = address
        self._port = port
        self._listener = listener
        self._server = None
        self._server_thread = None

    @property
    def is_alive(self):
        return self._server_thread is not None\
            and self._server_thread.is_alive()

    def set_listener(self, listener):
        self._listener = listener

    def start(self):
        if self.is_alive:
            return

        client, listener = self, self._listener

        class ClientHandler(AbstractTokenHandler):
            @property
            def client(self):
                return client

            @property
            def listener(self):
                return listener

        self._server = HTTPServer((self._address, self._port), ClientHandler)
        self._server_thread = Thread(target=self._server.serve_forever,
                                     args=(0.01, ))
        # Exit the server thread when the main thread terminates
        self._server_thread.daemon = True
        self._server_thread.start()

    def stop(self, wait=True):
        if not self.is_alive:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server_thread.join()
        self._server_thread = None
        self._server = None
