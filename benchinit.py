from time import sleep
from auxfunc import readData

req = "http://127.0.0.1:9090/api/v1/query?query=kepler_node_core_joules_total"

# calculate system energy (idle):
interval = 3600
start_energy, start_ienergy = readData(req, 2, "Energy", True)
sleep(interval) # high enough
end_energy, end_ienergy = readData(req, 2, "Energy", True)
sys_energy = (end_energy - start_energy) / interval  # energy consumption per second
print("System energy: " + str(sys_energy))
