import socketserver
import http.server
import requests
import datetime

class server:
    def __init__(self, config, qosmodel, port = 8081, portqos = 8082, faasserver = '127.0.0.1', faasport = 8080):
        server.port = port
        server.portqos = portqos
        server.faasserver = faasserver
        server.faasport = faasport
        server.config = config
        server.qosmodel = qosmodel

    class handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            req = self.path[1:]
            fname = server.config.getFunction(req)
            self.send_response(200)
            self.end_headers()
            if fname == None:
                print('Bad request: unknown function: ' + req)
            else:
                print('Requesting function ' + fname)
                r = requests.get("http://" + server.faasserver + ":" + str(server.faasport) + '/' + fname)
                print(r.text)

    class handlerqos(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            req = self.path[1:]
            print('QoS request: ' + req)
            vals = req.split('=', 1)
            action = vals[0]
            value = vals[1]
            if action == "objective":
                server.qosmodel.readObjective(value)
            if action == "tmax":
                server.qosmodel.tmax = value
                print("tmax set to " + value)
            if action == "cmax":
                server.qosmodel.cmax = value
                print("cmax set to " + value)
            start_time = datetime.datetime.now()
            server.qosmodel.createZ3Model(server.config)
            end_time = datetime.datetime.now()
            time_diff = (end_time - start_time)
            execution_time = time_diff.total_seconds() * 1000
            print(f'Reconfiguration time: {execution_time:.2f} milliseconds')
            self.send_response(200)
            self.end_headers()

    def start(self):
        with socketserver.ThreadingTCPServer(('', server.port), server.handler) as httpd:
            print("Function server started")
            httpd.serve_forever()

    def startqos(self):
        with socketserver.TCPServer(('', server.portqos), server.handlerqos) as httpd:
            print("QoS server started")
            httpd.serve_forever()