import repository
import model
import configuration
from z3 import *
import datetime

MINCOST = 1
MINTIME = 2
MINENERGY = 3
MAXUX = 4

class qos:

    def __init__(self, rep, mod):
        self.rep = rep
        self.mod = mod
        # default values:
        self.objective = MINCOST
        self.objective2 = 0
        self.tmax = 0
        self.cmax = 0
        # cached values:
        self.wm = {}  # workflow model
        self.execTask = {}  # set of tasks that can be executed
        self.taskExecTime = {}  # total execution time of a task
        self.totalCost = {}  # total cost of a task
        self.totalEnergy = {}  # total energy of a task
        self.totalUX = {}  # total ux of a task

    def getWorkflowModel(self, execTask, workflow):
        tasklist = []
        op = workflow.get('op')
        if op != None:
            if op == 'and':
                for task in workflow['tasks']:
                    if task.get('op') != None:
                        tasklist.append(self.getWorkflowModel(execTask, task))
                    else:
                        tasklist.append(execTask[task['name']])
                return And(tasklist)
            elif op == 'xor':
                for task in workflow['tasks']:
                    if task.get('op') != None:
                        tasklist.append(self.getWorkflowModel(execTask, task))
                    else:
                        tasklist.append(execTask[task['name']])
                return (Sum([If(b,1,0) for b in tasklist]) == 1)
            elif op == 'or':
                for task in workflow['tasks']:
                    if task.get('op') != None:
                        tasklist.append(self.getWorkflowModel(execTask, task))
                    else:
                        tasklist.append(execTask[task['name']])
                return Or(tasklist)

    def createZ3Model(self):
        config = configuration.configuration()
        start_time = datetime.datetime.now()
        opt = Optimize()
        vars = {}
        execTime = {}
        cost = {}
        energy = {}
        ux = {}
        execTask = {}
        if len(execTask) == 0:
            # service functions: select only one per service:
            for service in self.mod.services:
                vars.clear()
                fs = self.rep.getFunctionsByServiceName(service.name)
                for f in fs:
                    vars[f.name] = Bool(f.name)
                    execTime[f.name] = If(vars[f.name], RealVal(f.execTime), RealVal(0))
                    cost[f.name] = If(vars[f.name], RealVal(f.cost), RealVal(0))
                    energy[f.name] = If(vars[f.name], RealVal(f.energy), RealVal(0))
                    ux[f.name] = If(vars[f.name], RealVal(f.ux), RealVal(0))
                opt.add(Sum([If(b,1,0) for b in vars.values()]) == 1)
            # calculate parameters per task:
            start_time_qos = datetime.datetime.now()
            taskExecTime = {}
            taskCost = {}
            taskEnergy = {}
            taskUX = {}
            for task in self.mod.tasks:
                taskExecTime[task.name] = RealVal(0)
                taskCost[task.name] = RealVal(0)
                taskEnergy[task.name] = RealVal(0)
                taskUX[task.name] = RealVal(0)
                for service in task.services:
                    for f in self.rep.functions:
                        if f.servicename == service.name:
                            taskExecTime[task.name] = Sum(taskExecTime[task.name], execTime[f.name])
                            taskCost[task.name] = Sum(taskCost[task.name], cost[f.name])
                            taskEnergy[task.name] = Sum(taskEnergy[task.name], energy[f.name])
                            taskUX[task.name] = Sum(taskUX[task.name], ux[f.name])
            # calculate total parameters:
            totalCost = RealVal(0)
            totalEnergy = RealVal(0)
            totalUX = RealVal(0)
            maxtime = Real('maxTime')
            for task in self.mod.tasks:
                execTask[task.name] = Bool(task.name)
                totalCost = Sum(totalCost, If(execTask[task.name], taskCost[task.name], 0))
                totalEnergy = Sum(totalEnergy, If(execTask[task.name], taskEnergy[task.name], 0))
                totalUX = Sum(totalUX, If(execTask[task.name], taskUX[task.name], 0))
            # define model:
            start_time_wf = datetime.datetime.now()
            for wf in self.mod.workflows:
                wm = self.getWorkflowModel(execTask, wf)
                opt.add(wm)
            self.opt = opt
            self.execTask = execTask
            self.taskExecTime = taskExecTime
            self.totalCost = totalCost
            self.totalEnergy = totalEnergy
            self.totalUX = totalUX
        opt = self.opt
        execTask = self.execTask
        taskExecTime = self.taskExecTime
        totalCost = self.totalCost
        totalEnergy = self.totalEnergy
        totalUX = self.totalUX
        #print(execTask)
        #print(taskExecTime)
        start_time_opt = datetime.datetime.now()
        if self.objective == MINCOST:
            if self.tmax != 0:
                for task in self.mod.tasks:
                    opt.add(If(execTask[task.name], taskExecTime[task.name] <= RealVal(self.tmax), True))
            opt.minimize(totalCost)
        elif self.objective == MINTIME:
            for task in self.mod.tasks:
                opt.add(If(execTask[task.name], taskExecTime[task.name] <= maxtime, True))
            if self.cmax != 0:
                opt.add(totalCost <= RealVal(self.cmax))
            opt.minimize(maxtime)
        elif self.objective == MINENERGY:
            if self.tmax != 0:
                for task in self.mod.tasks:
                    opt.add(If(execTask[task.name], taskExecTime[task.name] <= RealVal(self.tmax), True))
            if self.cmax != 0:
                opt.add(totalCost <= RealVal(self.cmax))
            opt.minimize(totalEnergy)
        elif self.objective == MAXUX:
            if self.tmax != 0:
                for task in self.mod.tasks:
                    opt.add(If(execTask[task.name], taskExecTime[task.name] <= RealVal(self.tmax), True))
            if self.cmax != 0:
                opt.add(totalCost <= RealVal(self.cmax))
            opt.maximize(totalUX)
        if self.objective2 == MINCOST:
            if self.tmax != 0:
                for task in self.mod.tasks:
                    opt.add(If(execTask[task.name], taskExecTime[task.name] <= RealVal(self.tmax), True))
            opt.minimize(totalCost)
        elif self.objective2 == MINTIME:
            for task in self.mod.tasks:
                opt.add(If(execTask[task.name], taskExecTime[task.name] <= maxtime, True))
            if self.cmax != 0:
                opt.add(totalCost <= RealVal(self.cmax))
            opt.minimize(maxtime)
        elif self.objective2 == MINENERGY:
            if self.tmax != 0:
                for task in self.mod.tasks:
                    opt.add(If(execTask[task.name], taskExecTime[task.name] <= RealVal(self.tmax), True))
            if self.cmax != 0:
                opt.add(totalCost <= RealVal(self.cmax))
            opt.minimize(totalEnergy)
        elif self.objective2 == MAXUX:
            if self.tmax != 0:
                for task in self.mod.tasks:
                    opt.add(If(execTask[task.name], taskExecTime[task.name] <= RealVal(self.tmax), True))
            if self.cmax != 0:
                opt.add(totalCost <= RealVal(self.cmax))
            opt.maximize(totalUX)
        if opt.check() == sat:
            z3m = opt.model()
            m = {}
            for d in z3m:
                if is_bool(z3m[d]):
                    m[d.name()] = bool(z3m[d])
            for task in self.mod.tasks:
                if m[task.name]:
                    config.addTask(task.name)
                    t = self.mod.getTask(task.name)
                    for s in t.services:
                        fs = self.rep.getFunctionsByServiceName(s.name)
                        for f in fs:
                            if m[f.name]:
                                config.addService(s.name, f.name)
            print('Configuration created')
        else:
            print('Configuration not found')
        end_time = datetime.datetime.now()
        time_diff = (end_time - start_time_opt)
        config.opt_time = time_diff.total_seconds() * 1000
        time_diff = (start_time_qos - start_time + start_time_opt - start_time_wf)
        config.model_time = time_diff.total_seconds() * 1000
        time_diff = (start_time_wf - start_time_qos)
        config.qos_time = time_diff.total_seconds() * 1000

        return config

    def readObjective(self, objective, num=1):
        if objective == "mincost":
            if num==1: self.objective = MINCOST
            else: self.objective2 = MINCOST
            print('Objective set to mincost')
        elif objective == "mintime":
            if num==1: self.objective = MINTIME
            else: self.objective2 = MINTIME
            print('Objective set to mintime')
        elif objective == "minenergy":
            if num==1: self.objective = MINENERGY
            else: self.objective2 = MINENERGY
            print('Objective set to minenergy')
        elif objective == "maxux":
            if num==1: self.objective = MAXUX
            else: self.objective2 = MAXUX
            print('Objective set to maxux')
        else: print('Invalid value for objective')