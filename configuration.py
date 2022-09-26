import json
import task
import service
import threading

class configuration:

    def __init__(self):
        self.modelname = ""
        self.tasks = []
        self.services = []
        self.opt_time = 0
        self.model_time = 0
        self.qos_time = 0

    def addTask(self, name):
        t = task.task(name)
        self.tasks.append(t)

    def addService(self, name, function):
        s = service.service(name, function)
        self.services.append(s)

    def load(self, config):
        print("Loading configuration " + config)
        with open(config + ".json") as file:
            data = json.load(file)
            self.modelname = data['model']
            for datat in data['tasks']:
                self.addTask(datat['name'])
                print("Task " + datat['name'] + " loaded")
            for datas in data['services']:
                self.addService(datas['name'], datas['function'])
                print("Service " + datas['name'].name + " loaded")

    def save(self, mod, filename):
        data = {}
        data['model'] = mod.name
        tasklist = []
        for t in self.tasks:
            tasklist.append({'name':t.name})
        data['tasks'] = tasklist
        servlist = []
        for s in self.services:
            servlist.append({'name':s.name, 'function':s.function})
        data['services'] = servlist
        jsondata = json.dumps(data, indent=4)
        with open(filename + '.json', 'w') as file:
            file.write(jsondata)

    def getTask(self, name):
        for task in self.tasks:
            if task.name == name:
                return task
        return None

    def getFunction(self, servicename):
        for s in self.services:
            if s.name == servicename:
                return s.function
        return None

    def executeTask(self, repository, taskconfig):
        print("Executing task " + taskconfig.name)
        for i in range(len(taskconfig.services)):
            repository.executeFunction(taskconfig.services[i].function)

    def exec(self, repository, model, workflow):
        op = workflow.get('op')
        if op != None:
            if op == 'and':
                for task in workflow['tasks']:
                    if task.get('op') != None:
                        self.exec(repository, model, task)
                    else:
                        taskconfig = model.getTask(task['name'])
                        t = threading.Thread(target=self.executeTask, args=(repository, taskconfig))
                        t.start()
            elif op == 'xor':
                for task in workflow['tasks']:
                    taskconfig = model.getTask(task['name'])
                    if task.get('op') != None:
                        self.exec(repository, model, task)
                    else:
                        t = threading.Thread(target=self.executeTask, args=(repository, taskconfig))
                        t.start()
                    break
            elif op == 'or':
                for task in workflow['tasks']:
                    taskconfig = model.getTask(task['name'])
                    if task.get('op') != None:
                        self.exec(repository, model, task)
                    else:
                        t = threading.Thread(target=self.executeTask, args=(repository, taskconfig))
                        t.start()

    def execute(self, repository, model):
        for wf in model.workflows:
            self.exec(repository, model, wf)