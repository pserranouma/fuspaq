# Benchmark application for measuring energy consumption of the application varying the number of operations and alternative functions

import repository
import model
import qos
import server
import datetime
from time import process_time, sleep
from auxfunc import readData
import threading
import statistics
import csv
import locale

numtasks = 1
numops = 1000
numfunc = 100
results = []
measurements = 4
sys_energy = 0.697  # measured idle consumption of the system
energy_levels = 20  # number of energy levels of a dummy function
req = "http://127.0.0.1:9090/api/v1/query?query=kepler_node_core_joules_total"
save = True

if save:
    filename = 'btest' + str(numtasks) + '_' + str(numops) + '_' + str(numfunc) + '-' + str(energy_levels) + '_' + str(measurements)
    header = ['time', 'energy', 'energy_e', 'time_c', 'energy_c', 'energy_c_e', 'mean_t', 'med_t', 'std_t', 't_t', 'mean_c', 'med_c', 'std_c', 't_c', 'mean_a', 'med_a', 'std_a', 't_a']
    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
    with open(filename + '.csv', 'w', encoding = 'UTF8', newline = '') as file:
        writer = csv.writer(file, delimiter = ';')
        writer.writerow(header)

rep = repository.repository()
rep.loadDummy(numtasks, numops, numfunc, 1, 1, 0, 0, energy_levels)
#rep.save('repository-bench')
mod = model.model()
#mod.loadDummyOps('modeltest',numtasks, numops)
mod.loadDummy(numtasks, numops)
qosmodel = qos.qos(rep, mod)
qosmodel.objective = qos.MINENERGY
qosmodel.objective2 = qos.MAXUX
start_energy_c, start_ienergy_c = readData(req, 2, "Energy", True)
start_time_c = datetime.datetime.now()
config = qosmodel.createZ3Model()
end_time_c = datetime.datetime.now()
time_diff_c = (end_time_c - start_time_c)
end_energy_c, end_ienergy_c = readData(req, 2, "Energy", True)
energy_c = end_energy_c - start_energy_c
print("Total configuration energy: " + str(energy_c))
execution_time_c = time_diff_c.total_seconds() * 1000
print(f'Configuration time: {execution_time_c:.2f} milliseconds')
#config.save(mod, 'config-bench')
result = {}
result["energy_c"] = energy_c
result["time_c"] = execution_time_c
s = server.server(config, qosmodel)
x = threading.Thread(target=s.start, daemon=True)
x.start()

for i in range(measurements):
    start_energy, start_ienergy = readData(req, 2, "Energy", True)
    #print(start_energy)
    start_time = datetime.datetime.now()
    config.execServices()
    end_time = datetime.datetime.now()
    time_diff = (end_time - start_time)
    end_energy, end_ienergy = readData(req, 2, "Energy", True)
    energy = end_energy - start_energy
    print("Total energy: " + str(energy))
    execution_time = time_diff.total_seconds() * 1000
    print(f'Execution time: {execution_time:.2f} milliseconds')
    result["energy"] = energy
    result["time"] = execution_time
    results.append(result)
    s.stop()
    x.join()
    print("Function server stopped")
    if i < (measurements - 1):
        rep = repository.repository()
        rep.loadDummy(numtasks, numops, numfunc, 1, 1, 0, 0, energy_levels)
        #rep.save('repository-bench')
        mod = model.model()
        #mod.loadDummyOps('modeltest',numtasks, numops)
        mod.loadDummy(numtasks, numops)
        qosmodel = qos.qos(rep, mod)
        qosmodel.objective = qos.MINENERGY
        qosmodel.objective2 = qos.MAXUX
        start_energy_c, start_ienergy_c = readData(req, 2, "Energy", True)
        start_time_c = datetime.datetime.now()
        config = qosmodel.createZ3Model()
        end_time_c = datetime.datetime.now()
        time_diff_c = (end_time_c - start_time_c)
        end_energy_c, end_ienergy_c = readData(req, 2, "Energy", True)
        energy_c = end_energy_c - start_energy_c
        print("Total configuration energy: " + str(energy_c))
        execution_time_c = time_diff_c.total_seconds() * 1000
        print(f'Configuration time: {execution_time_c:.2f} milliseconds')
        #config.save(mod, 'config-bench')
        result = {}
        result["energy_c"] = energy_c
        result["time_c"] = execution_time_c
        s = server.server(config, qosmodel)
        x = threading.Thread(target=s.start, daemon=True)
        x.start()

# calculate averages
total_energy = 0
total_time = 0
total_energy_c = 0
total_time_c = 0
for i in range(measurements):
    total_energy += results[i]["energy"]
    total_time += results[i]["time"] / 1000
    total_energy_c += results[i]["energy_c"]
    total_time_c += results[i]["time_c"] / 1000

total_app_energy = round(total_energy - (sys_energy * total_time), 2)
app_energy_average = round(total_app_energy / measurements, 2)
time_average = round(total_time / measurements, 2)
total_conf_energy = round(total_energy_c - (sys_energy * total_time_c), 2)
conf_energy_average = round(total_conf_energy / measurements, 2)
time_average_c = round(total_time_c / measurements, 2)

# when execution time is not enough higher comparing to sample time (5s), we will use energy estimations:
for i in range(measurements):
    results[i]["energy_e"] = app_energy_average * (results[i]["time"] / 1000) / time_average
    results[i]["energy_c_e"] = conf_energy_average * (results[i]["time_c"] / 1000) / time_average_c

# mean:
mean_s = round(total_energy / measurements, 2)
mean_a = round(app_energy_average, 2)
mean_s_c = round(total_energy_c / measurements, 2)
mean_c = round(conf_energy_average, 2)
mean_s_t = round((total_energy + total_energy_c) / measurements, 2)
mean_t = round(app_energy_average + conf_energy_average, 2)

# median:
median = round(statistics.median((o["energy"] - (sys_energy * results[i]["time"] / 1000) for o in results)), 2)
median_e = round(statistics.median((o["energy_e"] for o in results)), 2)
median_c = round(statistics.median((o["energy_c"] - (sys_energy * results[i]["time_c"] / 1000) for o in results)), 2)
median_c_e = round(statistics.median((o["energy_c_e"] for o in results)), 2)
median_t = round(statistics.median((o["energy"] + o["energy_c"] - (sys_energy * results[i]["time"] / 1000) for o in results)), 2)
median_t_e = round(statistics.median((o["energy_e"] + o["energy_c_e"] for o in results)), 2)

# std deviation:
std = round(statistics.stdev((o["energy"] - (sys_energy * results[i]["time"] / 1000) for o in results)), 2)
std_e = round(statistics.stdev((o["energy_e"] for o in results)), 2)
std_c = round(statistics.stdev((o["energy_c"] - (sys_energy * results[i]["time"] / 1000) for o in results)), 2)
std_c_e = round(statistics.stdev((o["energy_c_e"] for o in results)), 2)
std_t = round(statistics.stdev((o["energy"] + o["energy_c"] - (sys_energy * results[i]["time"] / 1000) for o in results)), 2)
std_t_e = round(statistics.stdev((o["energy_e"] + o["energy_c_e"] for o in results)), 2)

# save data
if save:
    value = []
    value.append(round(results[0]['time'] / 1000, 2))
    value.append(round(results[0]['energy'], 2))
    value.append(round(results[0]['energy_e'], 2))
    value.append(round(results[0]['time_c'] / 1000, 2))
    value.append(round(results[0]['energy_c'], 2))
    value.append(round(results[0]['energy_c_e'], 2))
    value.append(mean_t)
    value.append(median_t_e)
    value.append(std_t_e)
    value.append(time_average + time_average_c)
    value.append(mean_c)
    value.append(median_c_e)
    value.append(std_c_e)
    value.append(time_average_c)
    value.append(mean_a)
    value.append(median_e)
    value.append(std_e)
    value.append(time_average)
    with open(filename + '.csv', 'a', encoding = 'UTF8', newline = '') as file:
        writer = csv.writer(file, delimiter = ';')
        writer.writerow(value)
        for i in range(1, len(results)):
            value = []
            value.append(round(results[i]['time'] / 1000, 2))
            value.append(round(results[i]['energy'], 2))
            value.append(round(results[i]['energy_e'], 2))
            value.append(round(results[i]['time_c'] / 1000, 2))
            value.append(round(results[i]['energy_c'], 2))
            value.append(round(results[i]['energy_c_e'], 2))
            for j in range(12): value.append(0)
            writer.writerow(value)
else:
    print(' '.join(f"{o['energy']:.2f}" for o in results))
    print(' '.join(f"{o['energy_e']:.2f}" for o in results))
    print(' '.join(f"{o['time'] / 1000:.2f}" for o in results))
    print(' '.join(f"{o['energy_c']:.2f}" for o in results))
    print(' '.join(f"{o['energy_c_e']:.2f}" for o in results))
    print(' '.join(f"{o['time_c'] / 1000:.2f}" for o in results))

print(f'Average system energy: {mean_s:.2f} joules')
print(f'Average app energy: {mean_a:.2f} joules')
print(f'Average conf system energy: {mean_s_c:.2f} joules')
print(f'Average conf energy: {mean_c:.2f} joules')
print(f'Average total system energy: {mean_s_t:.2f} joules')
print(f'Average total energy: {mean_t:.2f} joules')

print(f'Median app: {median:.2f} joules')
print(f'Median_e app: {median_e:.2f} joules')
print(f'Median conf: {median_c:.2f} joules')
print(f'Median_e conf: {median_c_e:.2f} joules')
print(f'Median total: {median_t:.2f} joules')
print(f'Median_e total: {median_t_e:.2f} joules')

print(f'Std deviation app: {std:.2f}')
print(f'Std deviation_e app: {std_e:.2f}')
print(f'Std deviation conf: {std_c:.2f}')
print(f'Std deviation_e conf: {std_c_e:.2f}')
print(f'Std deviation total: {std_t:.2f}')
print(f'Std deviation_e total: {std_t_e:.2f}')

print(f'Average app execution time: {time_average:.2f} seconds')
print(f'Average conf execution time: {time_average_c:.2f} seconds')
print(f'Average total execution time: {time_average + time_average_c:.2f} seconds')
