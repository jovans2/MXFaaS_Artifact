import subprocess
import docker
import numpy as np
import time
import requests
import threading
import os
from statistics import mean, median

services = ["create_ord_cpu_test", "create_ord_cpu_test_base"]
ip_addresses = []

def measure_cpu_util():
    while True:
        time.sleep(2) 
        output = os.popen("docker stats " + service+  " --no-stream --format '{{.CPUPerc}}'").read()   
        flout = float(output[:-2])
        perc_cpu = max(0, flout-100)
        print(print(f"number: {perc_cpu:.2f}"))

containers = ["MXContainer", "Baseline"]
for service in services:
    output = subprocess.check_output("docker run -d --name " + service + " --cpuset-cpus=0,1 jovanvr97/" + service, shell=True).decode("utf-8")
    time.sleep(5)
    print("Start")
    threading.Thread(target=measure_cpu_util).start()
    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['IPAddress']
    ip_addresses.append(ip_add)

    time.sleep(50)

    output = subprocess.check_output("docker stop " + service, shell=True).decode("utf-8")
    output = subprocess.check_output("docker rm " + service, shell=True).decode("utf-8")