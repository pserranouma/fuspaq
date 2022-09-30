import json
from random import randint,choice
import task
import service

class model:

    def __init__(self):
        self.name = ""
        self.workflows = []
        self.tasks = []
        self.services = []
        self.constraints = []

    def load(self, model):
        try:
            file = open(model + ".json")
            print("Loading model " + model)
        except OSError:
            print("Error reading model " + model)
            exit()
        with file:
            data = json.load(file)
            self.name = data['name']
            self.workflows = data['workflows']
            for datat in data['taskservices']:
                t = task.task(datat['task'])
                for serv in datat['services']:
                    s = service.service(serv['name'])
                    #s.description = serv['description']
                    t.addService(s)
                    self.services.append(s)
                self.tasks.append(t)
                print("Task " + t.name + " loaded")
    
    def createTasks(self,wf,ntask,ntasks): # ntasks pending to create
        ops = (['and', 'or', 'xor'])
        wf["op"] = choice(ops)
        wf["tasks"] = []
        #print(wf["op"])
        ntasks_ant = ntasks
        #print(ntasks_ant)
        nt = ntask # id of the next task to assign
        #print(nt)
        while ntasks > 0: # ntaks to assign
            if ntasks == 1:
                t = {}
                t["name"] = "t"+ str(nt)
                nt += 1
                ntasks -= 1
                wf["tasks"].append(t)
            elif ntasks == 2:
                t = {}
                t["name"] = "t"+ str(nt)
                nt += 1
                ntasks -= 1
                wf["tasks"].append(t)
                t = {}
                t["name"] = "t"+ str(nt)
                nt += 1
                ntasks -= 1
                wf["tasks"].append(t)
            else:
                tipo = randint(0,1)
                if tipo == 0: # simple
                    t = {}
                    t["name"] = "t"+ str(nt)
                    nt += 1
                    ntasks -= 1
                    wf["tasks"].append(t)
                else: # compuesta
                    if ntasks_ant != ntasks:
                        nwf = {}
                        self.createTasks(nwf,nt,ntasks)
                        wf["tasks"].append(nwf)
                        ntasks = 0

    def createParallelTasks(self,wf,ntask,ntasks): # ntasks pending to create
        wf["op"] = 'and'
        wf["tasks"] = []
        #print(wf["op"])
        ntasks_ant = ntasks
        #print(ntasks_ant)
        nt = ntask # id of the next task to assign
        #print(nt)
        while ntasks > 0: # ntasks to assign
            t = {}
            t["name"] = "t"+ str(nt)
            nt += 1
            ntasks -= 1
            wf["tasks"].append(t)

    def loadDummy(self, numtasks, numops):
        print("Loading dummy model")
        self.name = "model"
        wf={}
        wf["name"] = "main"
        self.createTasks(wf,1,numtasks)
        self.workflows.append(wf)
        for i in range(1, numtasks + 1):
            t = task.task("t" + str(i))
            for j in range(1, numops + 1):
                s = service.service("op" + str(j))
                t.addService(s)
                self.services.append(s)
            self.tasks.append(t)
        print(str(numtasks) + " tasks loaded")
        #jsondata = json.dumps(self.workflows, indent=4)
        #with open('p.json', 'w') as file:
            #file.write(jsondata)

    def loadDummyParallel(self, numtasks, numops):
        print("Loading dummy model")
        self.name = "model"
        wf={}
        wf["name"] = "main"
        self.createParallelTasks(wf,1,numtasks)
        self.workflows.append(wf)
        for i in range(1, numtasks + 1):
            t = task.task("t" + str(i))
            for j in range(1, numops + 1):
                s = service.service("op"+ str(i) + "_" + str(j))
                t.addService(s)
                self.services.append(s)
            self.tasks.append(t)
        print(str(numtasks) + " tasks loaded")

    def loadDummyOps(self, model, numtasks, numops):
        print("Loading model " + model)
        with open(model + ".json") as file:
            data = json.load(file)
            self.name = data['name']
            self.workflows = data['workflows']
        print("Loading dummy ops")
        self.name = "model"
        wf={}
        wf["name"] = "main"
        self.createTasks(wf,1,numtasks)
        self.workflows.append(wf)
        for i in range(1,numtasks+1):
            t = task.task("t" + str(i))
            for j in range(1,numops+1):
                s = service.service("op" + str(j))
                t.addService(s)
                self.services.append(s)
            self.tasks.append(t)
            print("Task " + t.name + " loaded")
        #jsondata = json.dumps(self.workflows, indent=4)
        #with open('p.json', 'w') as file:
            #file.write(jsondata)

    def getTask(self, name):
        for task in self.tasks:
            if task.name == name:
                return task
        return None

