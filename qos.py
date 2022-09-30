from tkinter import Wm
import repository
import model
import configuration
from z3 import *
import datetime

MINCOST = 1
MINTIME = 2

class qos:

    def __init__(self, rep, mod):
        self.rep = rep
        self.mod = mod
        # default values:
        self.objective = MINCOST
        self.tmax = 0
        self.cmax = 0
        # cached values:
        self.wm = {}
        self.execTask = {}
        self.taskExecTime = {}
        self.totalCost = {}

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

    def createZ3Model(self, config):
        start_time = datetime.datetime.now()
        opt = Optimize()
        vars = {}
        execTime = {}
        cost = {}
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
                opt.add(Sum([If(b,1,0) for b in vars.values()]) == 1)
            # calculate cost and execTime per task:
            start_time_qos = datetime.datetime.now()
            taskExecTime = {}
            taskCost = {}
            for task in self.mod.tasks:
                taskExecTime[task.name] = RealVal(0)
                taskCost[task.name] = RealVal(0)
                for service in task.services:
                    for f in self.rep.functions:
                        if f.servicename == service.name:
                            taskExecTime[task.name] = Sum(taskExecTime[task.name], execTime[f.name])
                            taskCost[task.name] = Sum(taskCost[task.name], cost[f.name])
            # calculate total cost and execTime:
            totalCost = RealVal(0)
            maxtime = Real('maxTime')
            for task in self.mod.tasks:
                execTask[task.name] = Bool(task.name)
                totalCost = Sum(totalCost, If(execTask[task.name], taskCost[task.name], 0))
            # define model:
            start_time_wf = datetime.datetime.now()
            for wf in self.mod.workflows:
                wm = self.getWorkflowModel(execTask, wf)
                opt.add(wm)
            self.opt = opt
            self.execTask = execTask
            self.TaskExecTime = taskExecTime
            self.totalCost = totalCost
        opt = self.opt
        execTask = self.execTask
        taskExecTime = self.taskExecTime
        totalCost = self.totalCost
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

    def readObjective(self, objective):
        if objective == "mincost":
            self.objective = MINCOST
            print('Objective set to mincost')
        elif objective == "mintime":
            self.objective = MINTIME
            print('Objective set to mintime')
        else: print('Invalid value for objective')