import json
from random import randint
import function

class repository:

    def __init__(self):
        self.functions = []
        self.servicenames = set()

    def addFunction(self, function):
        self.functions.append(function)

    def load(self, rep):
        print("Loading repository " + rep)
        with open(rep + ".json") as file:
            data = json.load(file)
            for i in range(len(data['functions'])):
                dataf = data['functions'][i]
                f = function.function(dataf['name'], dataf['service'])
                f.execTime = dataf['execTime']
                f.cost = dataf['cost']
                self.addFunction(f)
                self.servicenames.add(dataf['service'])
                print("Function " + f.name + " loaded")

    def loadDummy(self, numtasks, numops, numfunc, numparam, numval):
        print("Loading dummy repository")
        nfunc = numfunc * numparam * numval
        for t in range(1, numtasks + 1):
            for i in range(1, numops + 1):
                for j in range(1, nfunc + 1):
                    f = function.function("f" + str(t) + "_" + str(i) + "_" + str(j), "op" + str(t) + "_" + str(i))
                    f.execTime = randint(0,2)
                    f.cost = randint(0,2)
                    self.addFunction(f)
                    self.servicenames.add("op" + str(t) + "_" + str(i))
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
        print(f.name)
        # r = requests.get("http://" + server + ":" + port + "/function/" + f.name, data={"t":1})
        # print(r.text)