import json
from random import randint
import function

class repository:

    def __init__(self):
        self.functions = []
        self.servicenames = set()

    def addFunction(self, function):
        self.functions.append(function)

    def load(self, filename):
        try:
            file = open(filename + ".json")
            print("Loading repository " + filename)
        except OSError:
            print("Error reading repository " + filename)
            exit()
        with file:
            data = json.load(file)
            for i in range(len(data['functions'])):
                dataf = data['functions'][i]
                if 'params' in dataf.keys():
                    f = function.function(dataf['name'], dataf['service'], dataf['params'])
                else: f = function.function(dataf['name'], dataf['service'])
                f.execTime = dataf['execTime']
                f.cost = dataf['cost']
                f.energy = dataf['energy']
                f.ux = dataf['ux']
                self.addFunction(f)
                self.servicenames.add(dataf['service'])
                print("Function " + f.name + " loaded")

    def save(self, filename):
        data = {}
        functions = []
        for f in self.functions:
            functions.append({'name':f.name, 'service':f.servicename, 'cost':f.cost, 'execTime':f.execTime, 'ux':f.ux, 'energy':f.energy})
        data['functions'] = functions
        jsondata = json.dumps(data, indent=4)
        with open(filename + '.json', 'w') as file:
            file.write(jsondata)

    def loadDummy(self, numtasks, numops, numfunc, numparam = 1, numval = 1, maxTime = 0, costLevels = 0, energyLevels = 0, UXLevels = 0):
        print("Loading dummy repository")
        nfunc = numfunc * numparam * numval
        for t in range(1, numtasks + 1):
            for i in range(1, numops + 1):
                for j in range(1, nfunc + 1):
                    f = function.function("f" + str(j) + "_o" + str(i) + "_t" + str(t), "Op" + str(i) + "_t" + str(t))
                    f.execTime = randint(0, maxTime)
                    f.cost = randint(0, costLevels)
                    if energyLevels == -1: f.energy = 20
                    else: f.energy = randint(0, energyLevels)
                    f.ux = randint(0, UXLevels)
                    #print(f.name + ": " + str(f.energy))
                    self.addFunction(f)
                    self.servicenames.add("Op" + str(i) + "_t" + str(t))
        print(str(numtasks * numops * nfunc) + " total functions loaded")

    def getFunctionByName(self, name):
        for f in self.functions:
            if f.name == name:
                return f
        return None

    def getFunctionsByServiceName(self, servicename):
        fs = []
        for f in self.functions:
            if f.servicename == servicename:
                fs.append(f)
        return fs

    def executeFunction(self, functionname):
        f = self.getFunctionByName(functionname)
        print('Executing ' + f.name)
        # r = requests.get("http://" + server + ":" + port + "/function/" + f.name, data={"t":1})
        # print(r.text)