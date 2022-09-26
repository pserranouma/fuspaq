import socketserver
import http.server
import requests
import configuration

class server:
    def __init__(self, config, port = 8081, faasserver = '127.0.0.1', faasport = 8080):
        server.port = port
        server.faasserver = faasserver
        server.faasport = faasport
        server.config = config

    class handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            fname = server.config.getFunction(self.path[1:])
            self.send_response(200)
            self.end_headers()
            print('Requesting function ' + fname)
            r = requests.get("http://" + server.faasserver + ":" + str(server.faasport) + '/' + fname)
            print(r.text)

    def start(self):
        with socketserver.ThreadingTCPServer(('', server.port), server.handler) as httpd:
            print("Server started")
            httpd.serve_forever()