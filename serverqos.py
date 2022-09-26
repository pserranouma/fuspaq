import socketserver
import http.server
import requests
import configuration

class serverqos:
    def __init__(self, config, port = 8082):
        serverqos.port = port
        serverqos.config = config

    class handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            request = self.path[1:]
            self.send_response(200)
            self.end_headers()
            print('QoS set to ' + request)

    def start(self):
        with socketserver.ThreadingTCPServer(('', serverqos.port), serverqos.handler) as httpd:
            print("QoS server started")
            httpd.serve_forever()