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
        print("Use: python fuspaq.py repository model objetive")
        exit()

rep = repository.repository()
rep.load(sys.argv[1])
mod = model.model()
mod.load(sys.argv[2])
qosmodel = qos.qos(rep, mod)
qosmodel.readObjective(sys.argv[3])
config = configuration.configuration()
start_time = datetime.datetime.now()
config = qosmodel.createZ3Model(config)
end_time = datetime.datetime.now()
time_diff = (end_time - start_time)
execution_time = time_diff.total_seconds() * 1000
print(f'Execution time: {execution_time:.2f} milliseconds')
#config.save(mod, 'config')
s = server.server(config, qosmodel)
x = threading.Thread(target=s.startqos, daemon=True)
x.start()
s.start()