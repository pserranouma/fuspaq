import base64
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

def analizing(image_url, rects):
    facedata = rects
    facedata.update({"image_url": image_url})
    data = servicepost("SearchDb", facedata)
    data  = json.loads(data)
    identity = servicepost("GetImages", data)

def drawing(image_url, rects):
    image = servicepost("DrawImage", image_url)
    image = servicepost("DrawRect", rects)

def app():
    image1_url = "https://images.unsplash.com/photo-1668004828851-af95a042793e?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    image2_url = "https://images.unsplash.com/photo-1668004841450-5f5bda6c4564?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    res = servicepost("MoveDetect", {
    "image1_url": image1_url,
    "image2_url": image2_url
    })
    res  = json.loads(res)
    if (res["motion_detected"] == "true"):
        rects = servicepost("DetectFace", {"image_url":image2_url})
        rects  = json.loads(rects)
    thread1 = threading.Thread(target=analizing, args={image2_url, rects})
    thread2 = threading.Thread(target=drawing, args={image2_url, rects})
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

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

# test services:
image1 = "17443.jpg"
image2 = "17476.jpg"
image1_url = ""
image2_url = ""
with open(image1, 'rb') as img_file:
    image1_base64 = base64.b64encode(img_file.read()).decode('utf-8')
with open(image1, 'rb') as img_file:
    image2_base64 = base64.b64encode(img_file.read()).decode('utf-8')
n=500
for i in range(n):
    #res = servicepost("MoveDetect", {"image1_url": image1_url,"image2_url": image2_url})
    #res  = json.loads(res)
    if True:#(res["motion_detected"]):
        #rects = servicepost("FaceDetect", {"image_url": image2_url})
        #rects  = json.loads(rects)
        rects = {"faces": [{"x": 133, "y": 38, "w": 46, "h": 46}]}
        #image = servicepost("DrawImage", {"image_url":image2_url})
        #rects.update({"image_url": image2_url})
        #image = servicepost("DrawRect", rects)
        known_faces = servicepost("SearchDb", {"client_id": 1})
        known_faces = json.loads(known_faces)
        known_faces.update({"image_url": image2_url})
        res = servicepost("GetIdentity", known_faces)


"""     res = servicepost("MoveDetect", {"image1_url": image1_url,"image2_url": image2_url})
    res  = json.loads(res)
    if (res["motion_detected"]):
        rects = servicepost("FaceDetect", {"image_url":image2_url})
        rects  = json.loads(rects)
        image = servicepost("DrawImage", {"image_url":image2_url})
        rects.update({"image_url": image2_url})
        image = servicepost("DrawRect", rects)
        known_faces = servicepost("SearchDb", {"client_id": 1}) """

# test app:
""" n=1
for i in range(n):
    app() """

# test concurrent connections:
""" res = servicepost("MoveDetect", {
    "image1_url": "https://images.unsplash.com/photo-1668004828851-af95a042793e?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    "image2_url": "https://images.unsplash.com/photo-1668004841450-5f5bda6c4564?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    })
    res  = json.loads(res)
    if (res["motion_detected"] == "true"):
        rects = servicepost("DetectFace", {"image_url":"https://images.unsplash.com/photo-1668004841450-5f5bda6c4564?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"})
        rects  = json.loads(rects)
def daemon():
    n = 1
    for i in range(n):
        x = threading.Thread(target=processmodel, args={data})
        x.start()
        x.join()

daemonthreads = list()
for i in range(1):
    x = threading.Thread(target=daemon)
    daemonthreads.append(x)
    x.start()

for i, thread in enumerate(daemonthreads):
    thread.join() """
