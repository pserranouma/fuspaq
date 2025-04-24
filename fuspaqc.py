import repository
import model
import configuration
import qos
import server
import datetime
import sys
import threading

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Use: python fuspaq.py repository model objective [objective2]")
        exit()

rep = repository.repository()
rep.load(sys.argv[1])
mod = model.model()
mod.load(sys.argv[2])
qosmodel = qos.qos(rep, mod)
qosmodel.readObjective(sys.argv[3])
if len(sys.argv) == 5:
    qosmodel.readObjective(sys.argv[4], 2)
start_time = datetime.datetime.now()
config = qosmodel.createZ3Model()
end_time = datetime.datetime.now()
time_diff = (end_time - start_time)
execution_time = time_diff.total_seconds() * 1000
print(f'Execution time: {execution_time:.2f} milliseconds')
config.save(mod, 'configc')
s = server.server(config, qosmodel, 'test4')
x = threading.Thread(target=s.startqos, daemon=True)
x.start()
s.start()