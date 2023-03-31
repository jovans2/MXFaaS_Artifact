import subprocess
import docker
import numpy as np
import time
import requests
import threading
import os
from statistics import mean, median

services = ["cnn_serving"]
ip_addresses = []

for service in services:
    output = subprocess.check_output("docker run -d --name " + service + " --cpu-shares=0 jovanvr97/" + service + "_knative_cpu", shell=True).decode("utf-8")

    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['IPAddress']
    ip_addresses.append(ip_add)

def lambda_func(service):
    while True:
        try:
            requests.post(service, json={"name": "test"})
            break
        except:
            pass

def EnforceActivityWindow(start_time, end_time, instance_events):
    events_iit = []
    events_abs = [0] + instance_events
    event_times = [sum(events_abs[:i]) for i in range(1, len(events_abs) + 1)]
    event_times = [e for e in event_times if (e > start_time)and(e < end_time)]
    try:
        events_iit = [event_times[0]] + [event_times[i]-event_times[i-1]
                                         for i in range(1, len(event_times))]
    except:
        pass
    return events_iit

loads = [1000]

def measure_cpu_util():
    while True:
        time.sleep(0.1) 
        output = os.popen("docker stats " + service+  " --no-stream --format '{{.CPUPerc}}'").read()   
        print(float(output[:-2]))

indR = 0
for load in loads:
    duration = 1
    seed = 100
    rate = load
    # generate Poisson's distribution of events 
    inter_arrivals = []
    np.random.seed(seed)
    beta = 1.0/rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
    instance_events = EnforceActivityWindow(0,duration,inter_arrivals)
        
    for service in services:
        
        threads = []
        after_time, before_time = 0, 0

        st = 0
        print("Start")
        threading.Thread(target=measure_cpu_util).start()

        for t in instance_events:
            st = st + t - (after_time - before_time)
            before_time = time.time()

            threadToAdd = threading.Thread(target=lambda_func, args=("http://"+ip_addresses[services.index(service)]+":9999", ))
            threads.append(threadToAdd)
            threadToAdd.start()
            after_time = time.time()

        for thread in threads:
            thread.join()


for service in services:
    output = subprocess.check_output("docker stop " + service, shell=True).decode("utf-8")
    output = subprocess.check_output("docker rm " + service, shell=True).decode("utf-8")
