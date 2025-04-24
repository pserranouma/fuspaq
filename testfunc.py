import socketserver
import http.server
import requests
import datetime
import threading
import time
import subprocess
import csv
import locale


def app():
    total = 0
    for i in range(10000):
    	for j in range(10000):
            total += i*j
    print("Drawing rectangles - a")


n=24000
for i in range(n):
    app()

"""n=5*2000
for i in range(n):
    service("FaceDetect", {"mode": 0})
    #service("FaceDetect")
    #time.sleep(0.1)
for i in range(n):
    service("WriteResult")
for i in range(n):
    service("DrawImage")
for i in range(n):
    service("DrawRect")
for i in range(n):
    service("SearchDb", {"mode": 0})"""


"""n=2000
for i in range(n):
    service("MoveDetect")
    service("FaceDetect", {"mode": 0})
    time.sleep(1.5)
    service("SearchDb")
    service("WriteResult")
    service("DrawImage")
    service("DrawRect")
    thread1 = threading.Thread(target=analize)
    thread2 = threading.Thread(target=draw)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()"""


""" def daemon():
    n = 50
    for i in range(n):
        x = threading.Thread(target=app)
        x.start()
        x.join()
    n = 1000
    for i in range(n):
        x = threading.Thread(target=app)
        x.start()
        x.join()

daemonthreads = list()
for i in range(10):
    x = threading.Thread(target=daemon)
    daemonthreads.append(x)
    x.start()

for i, thread in enumerate(daemonthreads):
    thread.join() """
