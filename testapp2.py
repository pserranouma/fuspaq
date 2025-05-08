import socketserver
import http.server
import requests
import datetime
import threading
import time
import subprocess
import csv
import locale
import json

verbose = True

def service(serv, params = {}):
    try:
        r = requests.get("http://127.0.0.1:8083/" + serv, params=params)
        if verbose: print(r.content)
        return r.content
    except Exception as error:
        if verbose: print("Error:", type(error).__name__)
        return ""

def servicepost(serv, params = {}):
    try:
        r = requests.post("http://127.0.0.1:8083/" + serv, json=params)
        if verbose: print(r.content)
        return r.content
    except Exception as error:
        if verbose: print("Error:", type(error).__name__)
        return "{}"

def showphotos(location):
    location  = json.loads(location)
    location["distance"] = 1
    nearlocations = servicepost("GetNearLocations", location)
    nearlocations  = json.loads(nearlocations)
    images = servicepost("GetImages", nearlocations)
    images = json.loads(images)
    renderedimages = servicepost("RenderImages", images)

def showinfo(location):
    location  = json.loads(location)
    modeldata = servicepost("GetModelData", location)
    modeldata  = json.loads(modeldata)
    info = servicepost("PredictModel", modeldata)
    info = json.loads(info)
    info.update(location)
    renderedmap = servicepost("RenderMap", info)

def app():
    location = servicepost("GetLocation", {"address":{"city":"Málaga"}})
    location  = json.loads(location)
    thread1 = threading.Thread(target=showphotos, args={location})
    thread2 = threading.Thread(target=showinfo, args={location})
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

def processmodel(modeldata):
    servicepost("ProcessModel", modeldata)

def predictmodel(modeldata):
    servicepost("PredictModel", modeldata)

def getInstance(fname):
    proc = subprocess.run(["faas", "logs", fname, "--instance", "--lines", "1", "--tail=false"], capture_output=True, text=True)
    i = proc.stdout.find("(")
    j = proc.stdout.find(")")
    instance = proc.stdout[i+1:j]
    return instance

def getInstances(fname):  # search all active instances (replicas):
    instances = []
    proc = subprocess.run(["crictl", "pods", "-namespace", "openfaas-fn"], capture_output=True, text=True)
    i = 0
    while True:
        instance = {}
        i = proc.stdout.find(fname, i+1)
        if i == -1: break
        j = proc.stdout.rfind('\n', 0, i)
        k = proc.stdout.find(' ', j)
        l = proc.stdout.find(' ', i)
        iname = proc.stdout[i:l]
        if proc.stdout.find(" Ready", j, i) != -1:
            cid = proc.stdout[j+1:k]
            instance['name'] = iname
            instance['cid'] = cid
            instances.append(instance)
    return instances
        
# test showphotos:
""" n=5000
for i in range(n):
    location = servicepost("GetLocation", {"address":{"city":"Málaga"}})
    location  = json.loads(location)
    location["distance"] = 1
    nearlocations = servicepost("GetNearLocations", location)
    nearlocations  = json.loads(nearlocations)
    images = servicepost("GetImages", nearlocations)
    images = json.loads(images)
    renderedimages = servicepost("RenderImages", images) """

# test showinfo / process:
""" n=5000
for i in range(n):
    location = servicepost("GetLocation", {"address":{"city":"Málaga"}})
    location  = json.loads(location)
    modeldata = servicepost("GetModelData", location)
    modeldata  = json.loads(modeldata)
    info = servicepost("ProcessModel", modeldata)
    info = json.loads(info)
    info.update(location)
    renderedmap = servicepost("RenderMap", info) """

# test showinfo / predict:
""" n=5000
for i in range(n):
    location = servicepost("GetLocation", {"address":{"city":"Málaga"}})
    location  = json.loads(location)
    modeldata = servicepost("GetModelData", location)
    modeldata  = json.loads(modeldata)
    info = servicepost("PredictModel", modeldata)
    info = json.loads(info)
    info.update(location)
    renderedmap = servicepost("RenderMap", info) """

# test showphotos and showinfo:
n=200
for i in range(n):
    location = servicepost("GetLocation", {"address":{"city":"Málaga"}})
    thread1 = threading.Thread(target=showphotos, args={location})
    thread2 = threading.Thread(target=showinfo, args={location})
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

# test concurrent connections:
""" location = servicepost("GetLocation", {"address":{"city":"Málaga"}})
location  = json.loads(location)
modeldata = servicepost("GetModelData", location)
def daemon():
    n = 500
    for i in range(n):
        x = threading.Thread(target=predictmodel, args={modeldata})
        x.start()
        x.join()

daemonthreads = list()
for i in range(10):
    x = threading.Thread(target=daemon)
    daemonthreads.append(x)
    x.start()

for i, thread in enumerate(daemonthreads):
    thread.join() """
