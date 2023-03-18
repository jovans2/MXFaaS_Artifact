import subprocess
import docker
import numpy as np
import time
import requests
import threading
from statistics import mean, median

services = ["cnn_serving", "img_res", "img_rot", "ml_train", "vid_proc", "web_serve"]
ip_addresses = []

for service in services:
    output = subprocess.check_output("docker run -d --name " + service + " --cpu-shares=0 jovanvr97/" + service + "_knative", shell=True).decode("utf-8")

    client = docker.DockerClient()
    container = client.containers.get(service)
    ip_add = container.attrs['NetworkSettings']['IPAddress']
    ip_addresses.append(ip_add)

def lambda_func(service):
    global times
    while True:
        try:
            t1 = time.time()
            r = requests.post(service, json={"name": "test"})
            break
        except:
            pass
    t2 = time.time()
    times.append(t2-t1)

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

loads = [5, 30, 80]
load_desc = ["LOW_LOAD", "MED_LOAD", "HIGH_LOAD"]

output_file = open("run-all-out.txt", "w")

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
        times = []
        after_time, before_time = 0, 0

        st = 0
        for t in instance_events:
            st = st + t - (after_time - before_time)
            before_time = time.time()
            if st > 0:
                time.sleep(st)

            threadToAdd = threading.Thread(target=lambda_func, args=("http://"+ip_addresses[services.index(service)]+":9999", ))
            threads.append(threadToAdd)
            threadToAdd.start()
            after_time = time.time()

        for thread in threads:
            thread.join()

        print("=====================" + service + load_desc[loads.index(load)] + "=====================", file=output_file, flush=True)
        print(mean(times), file=output_file, flush=True)
        print(median(times), file=output_file, flush=True)
        print(np.percentile(times, 90), file=output_file, flush=True)
        print(np.percentile(times, 95), file=output_file, flush=True)
        print(np.percentile(times, 99), file=output_file, flush=True)


for service in services:
    output = subprocess.check_output("docker stop " + service, shell=True).decode("utf-8")
    output = subprocess.check_output("docker rm " + service, shell=True).decode("utf-8")

