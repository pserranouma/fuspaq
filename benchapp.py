# Benchmark application for measuring energy consumption of the configuration process varying the number of operations and alternative functions

import repository
import model
import qos
import server
import datetime
from time import process_time
from auxfunc import readData

numtasks = 5
numops = 3
numfunc = 3
results = []
measurements = 100
sys_energy = 0.697
req = "http://127.0.0.1:9090/api/v1/query?query=kepler_node_core_joules_total"

# energy of the application:
start_energy, start_ienergy = readData(req, 2, "Energy", True)

for i in range(measurements):
    rep = repository.repository()
    rep.loadDummy(numtasks, numops, numfunc, 1, 1, 0, 0, 10)
    rep.save('repository-bench')
    mod = model.model()
    #mod.loadDummyOps('modeltest',numtasks, numops)
    mod.loadDummy(numtasks, numops)
    qosmodel = qos.qos(rep, mod)
    qosmodel.objective = qos.MINENERGY
    qosmodel.objective2 = qos.MAXUX
    start_time = datetime.datetime.now()
    start_ptime = process_time()
    config = qosmodel.createZ3Model()
    end_ptime = process_time()
    end_time = datetime.datetime.now()
    s = server.server(config, qosmodel)
    ptime_diff = (end_ptime - start_ptime)
    pexecution_time = ptime_diff * 1000
    print(f'Process time: {pexecution_time:.2f} milliseconds')
    time_diff = (end_time - start_time)
    execution_time = time_diff.total_seconds() * 1000
    print(f'Execution time: {execution_time:.2f} milliseconds')
    #config.save(mod, 'config-bench')
    #s.start()
    result = {}
    result["ptime"] = pexecution_time
    result["time"] = execution_time
    result["opt_time"] = config.opt_time
    result["model_time"] = config.model_time
    result["qos_time"] = config.qos_time
    results.append(result)

end_energy, end_ienergy = readData(req, 2, "Energy", True)
energy = end_energy - start_energy
print("Total energy: " + str(energy))

total_time = 0
total_ptime = 0
opt_time = 0
model_time = 0
qos_time = 0
for i in range(measurements):
    total_ptime += results[i]["ptime"]
    #print(results[i]["ptime"])
    total_time += results[i]["time"]
    #print(results[i]["time"])
    opt_time += results[i]["opt_time"]
    model_time += results[i]["model_time"]
    qos_time += results[i]["qos_time"]

#print(f'Average process time: {total_ptime/measurements:.2f} milliseconds')
print(f'Average execution time: {total_time/measurements:.2f} milliseconds')
print(f'Average modeling time: {model_time/measurements:.2f} milliseconds')
print(f'Average qos time: {qos_time/measurements:.2f} milliseconds')
print(f'Average optimization time: {opt_time/measurements:.2f} milliseconds')
print(f'Average reconfiguration time: {(opt_time + qos_time) / measurements:.2f} milliseconds')

app_energy = energy - sys_energy
print("App energy: " + str(app_energy))