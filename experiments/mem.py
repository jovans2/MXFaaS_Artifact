import os
import subprocess
import docker
import threading
import requests
 
# Getting all memory using os.popen()
total_memory, used_memory, free_memory = map(
    int, os.popen('free -t -m').readlines()[-1].split()[1:])
usedMemStart = used_memory
 
# Memory usage
# print("Before our experiments --> RAM memory % used:", round((used_memory) * 100, 2))

def lambda_func(service):
    while True:
        try:
            requests.post(service, json={"name": "test"})
            break
        except:
            pass

# BASELINE
services = ["cnn_serving"]
ip_addresses = []
for service in services:
    threads = []
    for indF in range(70):
        nameS = service + str(indF)
        output = subprocess.check_output("docker run -d --name " + nameS + " --cpu-shares=0 jovanvr97/" + service + "_knative", shell=True).decode("utf-8")
        client = docker.DockerClient()
        container = client.containers.get(nameS)
        ip_add = container.attrs['NetworkSettings']['IPAddress']
        ip_addresses.append(ip_add)
        for _ in range(8):
            threadToAdd = threading.Thread(target=lambda_func, args=("http://"+ip_addresses[services.index(service)]+":9999", ))
            threads.append(threadToAdd)
        
    for thread in threads:
        thread.start()

    # Getting all memory using os.popen()
    total_memory, used_memory, free_memory = map(
        int, os.popen('free -t -m').readlines()[-1].split()[1:])

    # Memory usage
    print("Baseline --> RAM memory used:", round((used_memory-usedMemStart) * 100, 2))

    for thread in threads:
        thread.join()
    
    output = subprocess.check_output("docker kill $(docker ps -q)", shell=True).decode("utf-8")
    for indF in range(70):
        nameS = service + str(indF)
        output = subprocess.check_output("docker rm " + nameS, shell=True).decode("utf-8")

# Getting all memory using os.popen()
total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
usedMemStart = used_memory

#MXFaaS
ip_addresses = []
for service in services:
    threads = []
    nameS = service + str(indF)
    output = subprocess.check_output("docker run -d --name " + nameS + " --cpu-shares=0 jovanvr97/" + service + "_knative", shell=True).decode("utf-8")
    client = docker.DockerClient()
    container = client.containers.get(nameS)
    ip_add = container.attrs['NetworkSettings']['IPAddress']
    ip_addresses.append(ip_add)
    for _ in range(70*8):
        threadToAdd = threading.Thread(target=lambda_func, args=("http://"+ip_addresses[services.index(service)]+":9999", ))
        threads.append(threadToAdd)
        
    for thread in threads:
        thread.start()

    # Getting all memory using os.popen()
    total_memory, used_memory, free_memory = map(
        int, os.popen('free -t -m').readlines()[-1].split()[1:])

    # Memory usage
    print("MXFaaS --> RAM memory used:", round((used_memory-usedMemStart) * 100, 2))

    for thread in threads:
        thread.join()

    output = subprocess.check_output("docker kill $(docker ps -q)", shell=True).decode("utf-8")
    output = subprocess.check_output("docker rm " + nameS, shell=True).decode("utf-8")