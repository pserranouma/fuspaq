import socketserver
import http.server
import requests
import datetime
import subprocess
import csv
import locale
import qos
import urllib.parse
import json
from auxfunc import readData, readDataOpenFaaS

MAXRATE = 60000
TRIGGER_PERCENT = 30


class server:
    def __init__(self, config, qosmodel, filename = '', port = 8083, portqos = 8082, faasserver = '127.0.0.1', faasport = 8080):
        server.port = port
        server.portqos = portqos
        server.faasserver = faasserver
        server.faasport = faasport
        server.htppd = None
        server.config = config
        server.qosmodel = qosmodel
        server.filename = filename
        server.llamadas = 0
        server.verbose = True
        server.dummyFunctions = False
        server.AVG_INTERVAL = 60  # number of seconds for moving average
        server.startTime = datetime.datetime.now()
        if filename != '':
            header = ['time', 'function', 'num replicas', 'avg time', 'rate', 'instance consumption', 'total consumption', 'unitary consumption', 'avg energy', 'energy', 'idle energy', 'energy dram', 'idle energy dram', 'event']
            locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
            with open(filename + '.csv', 'w', encoding = 'UTF8', newline = '') as file:
                writer = csv.writer(file, delimiter = ';')
                writer.writerow(header)

    class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True

    class handler(http.server.SimpleHTTPRequestHandler):
        def getInstance(self, fname):
            proc = subprocess.run(["faas", "logs", fname, "--instance", "--lines", "1", "--tail=false"], capture_output=True, text=True)
            i = proc.stdout.find("(")
            j = proc.stdout.find(")")
            instance = proc.stdout[i+1:j]
            return instance

        def getInstances(self, fname):  # search all active instances (replicas):
            instances = []   
            proc = subprocess.run(["sudo", "crictl", "ps"], capture_output=True, text=True)
            i = 0
            m = 0
            while True:
                instance = {}
                i = proc.stdout.find(fname, m+1)
                if i == -1: break
                j = proc.stdout.rfind('\n', 0, i)
                k = proc.stdout.find(' ', j)
                m = proc.stdout.find('\n', i)
                l = proc.stdout.rfind(' ', m)
                iname = proc.stdout[l:m]
                if proc.stdout.find(" Running", j, i) != -1:
                    cid = proc.stdout[j+1:k]
                    instance['name'] = iname
                    instance['cid'] = cid
                    instances.append(instance)
            return instances

        def getPid(self, cid):  # search pid of a container:
            proc = subprocess.run(["crictl", "inspect", cid], capture_output=True, text=True)
            i = proc.stdout.find("pid", 0)
            j = proc.stdout.find(':', i)
            k = proc.stdout.find(',', j)
            pid = proc.stdout[j+1:k].strip()
            return pid

        def do_GET(self):
            self.handle_request(method="GET")

        def do_POST(self):
            self.handle_request(method="POST")

        def handle_request(self, method):
            """ intervalo=24000
            server.llamadas += 1
            if server.llamadas == intervalo: server.AVG_INTERVAL=60
            elif server.llamadas == intervalo*2: server.AVG_INTERVAL=120
            elif server.llamadas == intervalo*3: server.AVG_INTERVAL=300
            elif server.llamadas == intervalo*4: server.AVG_INTERVAL=600
            elif server.llamadas == intervalo*5:
                server.AVG_INTERVAL=30
                server.llamadas=0 """
            if method == "GET":
                # parse parameters:
                req = self.path[1:]
                func, _, query_string = req.partition('?')
                query = urllib.parse.parse_qs(query_string)
            elif method == "POST":
                # read POST body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                content_type = self.headers.get('Content-Type', '')

                if 'application/json' in content_type:
                    try:
                        query = json.loads(post_data)
                    except json.JSONDecodeError:
                        query = {}
                elif 'application/x-www-form-urlencoded' in content_type:
                    query = urllib.parse.parse_qs(post_data)
                else:
                    query = {}
                print(query)

                # Extract function from path without query string
                req = self.path[1:]
                func = req.strip('/')
                print(func)
            else:
                if server.verbose: print('Bad request: unknown method')
                self.send_response(405)
                self.end_headers()
                return
            fname = server.config.getFunction(func)
            f = server.qosmodel.rep.getFunctionByName(fname)
            if fname == None:
                if server.verbose: print('Bad request: unknown function: ' + req)
                self.send_response(400)
            else:
                if server.verbose: print('Requesting function ' + fname)
                if server.dummyFunctions:
                    fname = 'func'
                    query_string = "mode=" + str(f.energy)
                    query = urllib.parse.parse_qs(query_string)
                # mix config parameters with user parameters:
                f.params.update(query)
                r = None
                try:
                    if method == "GET":
                        r = requests.get("http://" + server.faasserver + ":" + str(server.faasport) + '/function/' + fname, data=query)
                    elif method == "POST":
                        r = requests.post("http://" + server.faasserver + ":" + str(server.faasport) + '/function/' + fname, json=query)
                except:
                    if server.verbose: print("Error: FaaS server not reachable")
                    self.send_response(500)
                    self.end_headers()
                    return
                t = datetime.datetime.now()
                # r = requests.Response()             ###
                # r.status_code = 200                 ###
                # r._content = b'{ "resp" : "ok" }'   ###
                
                # monitor function behaviour:
                if r is not None and r.status_code == 200:
                    self.send_response(200, r.text)
                    if server.verbose: print(r.text)
                    event = ''
                    # get prometheus information (execution time and rate):
                    exectime, nd = readDataOpenFaaS("http://" + server.faasserver + ":9090" + "/api/v1/query?query=(rate(gateway_functions_seconds_sum{function_name=\"" + fname + ".openfaas-fn\"}[1m])/rate(gateway_functions_seconds_count{function_name=\"" + fname + ".openfaas-fn\"}[1m]))", "Execution time", server.verbose)
                    rate, nd = readDataOpenFaaS("http://" + server.faasserver + ":9090" + "/api/v1/query?query=increase(gateway_function_invocation_total{function_name=\"" + fname + ".openfaas-fn\"}[1m])" , "Rate", server.verbose)
                    if (rate == None) or (rate < 1): rate = 1
                    instances = self.getInstances(fname)
                    # search all active instances (replicas) to also capture idle consumptions:
                    total_cons = 0
                    total_energy = 0
                    total_ienergy = 0
                    total_energy_dram = 0
                    total_ienergy_dram = 0
                    cons_instance = 0
                    num_replicas = len(instances)
                    if server.verbose: print("Number of replicas: " + str(num_replicas))
                    if num_replicas > 1:
                        iname = self.getInstance(fname)
                        if server.verbose: print(iname)
                    else: iname = instances[0]['name']
                    for i in range(num_replicas):
                        instance = instances[i]['cid']
                        pid = self.getPid(instance)
                        if server.verbose:
                            print("instance " + str(i) + " " + instance)
                            print("pid " + pid)
                        cons, nd = readData("http://" + server.faasserver + ":9090" + "/api/v1/query?query=rate(kepler_container_joules_total{container_name=~\"" + fname + "\",container_id=~\"" + instance + ".*\"}[1m])" , "Consumption", server.verbose)
                        if iname == instances[i]['name']:
                            cons_instance = cons
                            if server.verbose: print("(Main instance)")
                        total_cons += cons
                        energy, ienergy = readData("http://" + server.faasserver + ":9090" + "/api/v1/query?query=increase(kepler_container_joules_total{container_name=~\"" + fname + "\",container_id=~\"" + instance + ".*\"}[1m])" , "Energy", server.verbose)                      
                        if iname == instances[i]['name']:
                            energy_instance = energy
                        total_energy += energy
                        total_ienergy += ienergy
                        energy_dram, ienergy_dram = readData("http://" + server.faasserver + ":9090" + "/api/v1/query?query=increase(kepler_container_dram_joules_total{container_name=~\"" + fname + "\",container_id=~\"" + instance + ".*\"}[1m])" , "Energy dram", server.verbose)
                        if iname == instances[i]['name']:
                            energy_instance = energy_dram
                        total_energy_dram += energy_dram
                        total_ienergy_dram += ienergy_dram
                    #if server.verbose: print("Total consumption: " + str(total_cons))
                    unitary_cons = total_cons / rate #* server.AVG_INTERVAL / rate / num_replicas  # first moving average
                    unitary_energy = total_energy / rate
                    unitary_ienergy = total_ienergy / rate
                    unitary_energy_dram = total_energy_dram / rate
                    unitary_ienergy_dram = total_ienergy_dram / rate

                    if server.verbose:
                        print("Unitary consumption: " + str(unitary_cons))
                        print("Unitary energy: " + str(unitary_energy))
                    # calculate second moving average
                    tambuffer = int(MAXRATE)
                    if f.consDataTotal == -1:  # initialize
                        f.startTime = t
                        f.consDataTotal = round(rate/num_replicas)  # number of samples
                        f.consDataLast = 0  # last index
                        for i in range(tambuffer):
                            f.consData.append(f.energy)
                    f.consData[f.consDataLast] = unitary_energy
                    f.consDataLast = (f.consDataLast + 1) % tambuffer
                    #if server.verbose: print("last: " + str(f.consDataLast))
                    avg_energy = 0
                    f.consDataTotal = round(rate/num_replicas)
                    for j in range(1, f.consDataTotal+1):
                        avg_energy += f.consData[(f.consDataLast - j) % tambuffer]
                        """if server.verbose:
                            print((f.consDataLast - j) % tambuffer)
                            print(f.consData[(f.consDataLast - j) % tambuffer])"""
                    avg_energy = avg_energy / f.consDataTotal
                    if server.verbose: print("Average energy: " + str(avg_energy))
                    # update function values if necessary:
                    energy = avg_energy
                    time_diff = t - f.startTime
                    seconds = time_diff.total_seconds()
                    if seconds > (server.AVG_INTERVAL*2):  # setup time
                        if server.qosmodel.objective == qos.MINENERGY or server.qosmodel.objective2 == qos.MINENERGY:
                            if (energy > (f.energy + f.energy*TRIGGER_PERCENT/100)) or (energy < (f.energy - f.energy*TRIGGER_PERCENT/100)):
                                event = fname + ' reconfiguration. Avgenergy: ' + str(energy) + " F.energy: " + str(f.energy)
                                f.startTime = t
                                f.execTime = exectime
                                f.replicas = num_replicas
                                f.energy = energy
                                # reconfigure model with the new parameters:
                                #server.config = server.qosmodel.createZ3Model()
                                if server.verbose: print(event)
                    # save data
                    if server.filename != '':
                        time_diff = t - server.startTime
                        seconds = time_diff.total_seconds()
                        value = []
                        value.append(seconds)
                        value.append(fname)
                        value.append(num_replicas)
                        value.append(exectime)
                        value.append(rate)
                        value.append(cons_instance)
                        value.append(total_cons)
                        value.append(unitary_cons)
                        value.append(avg_energy)
                        value.append(unitary_energy)
                        value.append(unitary_ienergy)
                        value.append(unitary_energy_dram)
                        value.append(unitary_ienergy_dram)
                        value.append(event)
                        with open(server.filename + '.csv', 'a', encoding = 'UTF8', newline = '') as file:
                            writer = csv.writer(file, delimiter = ';')
                            writer.writerow(value)
                else:
                    self.send_response(r.status_code)
            self.end_headers()
            self.wfile.write(r.content)

    class handlerqos(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            req = self.path[1:]
            if server.verbose: print('QoS request: ' + req)
            vals = req.split('=', 1)
            action = vals[0]
            value = vals[1]
            status_code = 200
            if action == "IsActiveTask":  # get configuration data
                if server.config.getTask(value) == None:
                    status_code = 404
                else:
                    status_code = 200
            else:  # set qos data
                resp = "ok"
                if action == "objective":
                    server.qosmodel.readObjective(value)
                elif action == "tmax":
                    server.qosmodel.tmax = value
                    if server.verbose: print("tmax set to " + value)
                elif action == "cmax":
                    server.qosmodel.cmax = value
                    if server.verbose: print("cmax set to " + value)
                else:
                    status_code = 400
                if status_code != 400:
                    start_time = datetime.datetime.now()
                    # reconfigure model with the new parameters:
                    server.config = server.qosmodel.createZ3Model()
                    end_time = datetime.datetime.now()
                    time_diff = (end_time - start_time)
                    execution_time = time_diff.total_seconds() * 1000
                    if server.verbose: print(f'Reconfiguration time: {execution_time:.2f} milliseconds')
            self.send_response(status_code)
            self.end_headers()

    def start(self):
        with server.ReusableThreadingTCPServer(('', server.port), server.handler) as server.httpd:
            print("Function server started")
            server.httpd.serve_forever()
    
    def stop(self):
        if server.httpd:
            server.httpd.shutdown()

    def startqos(self):
        with socketserver.TCPServer(('', server.portqos), server.handlerqos) as httpd:
            print("QoS server started")
            httpd.serve_forever()