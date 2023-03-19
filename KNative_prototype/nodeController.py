import os
import requests
import json
import os
import socket
import time
import threading
import sys
import signal
import subprocess
import logging


# CPU_NUM is the maximum number of cores we can use
# NODE_MAX is the maximum number of nodes we can use (SET NODE_MAX = 1 if we want to do simulation on one node)
CPU_NUM = 4
NODE_MAX = 2

# map physical cores to function owners
mapCores = {}
reqCores = {}
mapFuncToCores = {}
scaleUp = {}

# initialize mapCores and setFreeCores
for i in range(0, CPU_NUM):
    mapCores[i] = "none"

# set log level (INFO, DEBUG)
logging.basicConfig(level=logging.INFO)





# get the url of a function
def getUrlByFuncName(funcName):
    try:
        output = subprocess.check_output("kn service describe " + funcName + " -vvv", shell=True).decode("utf-8")
    except Exception as e:
        print("Error in kn service describe == " + str(e))
        return None
    lines = output.splitlines()
    for line in lines:
        if "URL:"  in line:
            url = line.split()[1]
            return url


# get the affinity mask of a function
def getAffinityMaskByFuncName(funcName):
    ret = []
    for i in mapCores:
        if i[1] == funcName:
            ret.append(i[0])
    return ret


def signal_handler(sig, frame):
    serverSocket.close()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


# Create a socket for receiving connections
myHost = '0.0.0.0'
myPort = 8080
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((myHost, myPort))
serverSocket.listen(1)


# map functions to owning cores
mapFuncToCores = {}

# get basic environment information
serviceNames = []

# We loop every 5 seconds to update information and do scheduling
while(1):
    
    ReTry = 0 # ReTry is a marker. If we cannot resolve information, we will log error and continue.
    
    # kn service list (Services discover)
    output = ''
    try:
        output = subprocess.check_output("kn service list", shell=True).decode("utf-8")
    except Exception as e:
        print("Error in kn service list == " + str(e))
        ReTry = 1
    lines = output.splitlines()
    lines = lines[1:] # delete the first line

    for line in lines:
        serviceName = line.split()[0] 
        if serviceName not in serviceNames:
            serviceNames.append(serviceName)
            reqCores[serviceName] = 0
            scaleUp[serviceName] = 1
    print("Services discoverd:",serviceNames)

    
    
    for serviceName in serviceNames:
        
        # map functions to owning cores
        result = requests.post(getUrlByFuncName(serviceName), json={"Q": 1})
        message = result.json()
        print(message)
        if "affinity_mask" in message:
            affinity_mask = message["affinity_mask"]
            print(affinity_mask)
            print(mapCores)
            new_affinity_mask = []
            for i in mapCores:
                if i not in affinity_mask and mapCores[i] == serviceName:
                    mapCores[i] = "none"
            for i in affinity_mask:
                if mapCores[i] == "none":
                    # if no service is using the core, then let the service use it
                    mapCores[i] = serviceName
                    new_affinity_mask.append(i)
                elif mapCores[i] == serviceName:
                    # if the service is using the core, then let the service use it
                    new_affinity_mask.append(i)
                elif mapCores[i] != serviceName:
                    # if the service using other service's core, then realloc one
                    realloc = True
                    for j in mapCores:
                        if mapCores[j] == "none":
                            mapCores[j] = serviceName
                            new_affinity_mask.append(j)
                            realloc = False
                            break
                    if realloc == True:
                        reqCores[serviceName] = reqCores[serviceName] + 1
            if affinity_mask != new_affinity_mask and new_affinity_mask!=[]:
                logging.info("Updating service " + serviceName + " to " + str(new_affinity_mask))
                try:
                    result = requests.post(getUrlByFuncName(serviceName), json={"numCores": len(new_affinity_mask),"affinity_mask": new_affinity_mask})
                except:
                    print("Error in updating affinity_mask")            
                mapFuncToCores[serviceName] = new_affinity_mask
            else:
                mapFuncToCores[serviceName] = affinity_mask
        else:
            print("Error in getting affinity_mask")
            ReTry = 1
            
        # map function to scaleUp
        try:
            output = subprocess.check_output("kn service describe " + serviceName + " ", shell=True).decode("utf-8")
        except Exception as e:
            print("Error in kn service describe == " + str(e))
        lines = output.splitlines()
        for line in lines:
            if "Replicas" in line:
                scaleUp[serviceName] = int(line.split()[1].split("/")[0])
        time.sleep(1)

    logging.info("Init environment finished.")
    logging.info(mapCores)
    logging.info(reqCores)
    logging.info(mapFuncToCores)
    logging.info(scaleUp)

    THRESHOLD = 0.7 # THRESHOLD to scale up
    THRESHOLD2 = 0.5 # THRESHOLD to scale down
    SLO = 2 # SLO
    
    if ReTry == 1:
        time.sleep(2)
        continue
    
    # Get p95 of each function and do cpu assignment (Find Requesters)
    for serviceName in serviceNames:
        url = getUrlByFuncName(serviceName)
        try:
            result = requests.post(url, json={"Q": 1})
            message = result.json()
        except Exception as e:
            print("Error in getting Q == " + str(e))
        if "p95" in message:
            p95 = message["p95"]
            print("p95 of " + serviceName + " is " + str(p95) + " s")
            if p95 > THRESHOLD * SLO:
                # Add 1 core
                Fail = True
                for i in mapCores: 
                    if mapCores[i] == "none":
                        mapCores[i] = serviceName
                        mapFuncToCores[serviceName].append(i)
                        logging.info("Updating service " + serviceName + " to " + str(mapFuncToCores[serviceName]))
                        try:
                            requests.post(getUrlByFuncName(serviceName), json={"numCores": len(mapFuncToCores[serviceName]),"affinity_mask": mapFuncToCores[serviceName]})
                        except:
                            print("Error in updating affinity_mask")   
                            ReTry = 1
                            break         
                        Fail = False
                        break
                # if fail, then record to find any donators or scale up
                if Fail:
                    reqCores[serviceName] = 1
                    logging.info("Request service " + serviceName + " to add 1 core")
        else:
            print("Fail in getting p95 for " + serviceName)
            ReTry = 1
        time.sleep(1)   
        
    if ReTry == 1:
        time.sleep(2)
        continue
            
    # Find donators
    for serviceName in serviceNames:
        url = getUrlByFuncName(serviceName)
        try:
            result = requests.post(url, json={"Q": 1})
            message = result.json()
        except Exception as e:
            print("Error in getting Q == " + str(e))
        if p95 < THRESHOLD2 * SLO:
            # Can scale down
            if scaleUp[serviceName] > 1:
                scaleUp[serviceName] = scaleUp[serviceName] - 1
                print("Scale down " + serviceName + " to" + str(scaleUp[serviceName]))
                try:
                    output = subprocess.check_output("kn service update " + serviceName + " --scale-target " + str(scaleUp[serviceName]), shell=True).decode("utf-8")
                except Exception as e:
                    print("Error in kn service update == " + str(e))
            # Can be donator
            for recipient in reqCores:
                while(reqCores[recipient] > 0 and len(mapFuncToCores[serviceName]) > 1):
                    for coreID in mapFuncToCores[serviceName]:
                        mapCores[coreID] = recipient
                        mapFuncToCores[serviceName].remove(coreID)
                        mapFuncToCores[recipient].append(coreID)
                        reqCores[recipient] = 0
                        logging.info("Updating service " + serviceName + " to " + str(mapFuncToCores[serviceName]) + "(Donator)")
                        requests.post(getUrlByFuncName(serviceName), json={"numCores": len(mapFuncToCores[serviceName]),"affinity_mask": mapFuncToCores[serviceName]})
                        
                        logging.info("Updatings service " + recipient + " to " + str(mapFuncToCores[recipient]) + "(Recipient)")
                        requests.post(getUrlByFuncName(recipient), json={"numCores": len(mapFuncToCores[recipient]),"affinity_mask": mapFuncToCores[i]})
        time.sleep(1)


    # If no donators but exist requesters, then scale up
    for serviceName in reqCores:
        if reqCores[serviceName] > 0 and scaleUp[serviceName] < NODE_MAX:
            # Need to scale up       
            try:
                # clear responseMapWindows
                result = requests.post(getUrlByFuncName(serviceName), json={"Clear": 1})
                message = result.json()
            except Exception as e:
                print("Error in getting Q == " + str(e))
            logging.info("Service " + serviceName + " still need " + str(reqCores[serviceName]) + " cores and will do scale")
            scaleUp[serviceName] = scaleUp[serviceName] + 1
            try:
                output = subprocess.check_output("kn service update " + serviceName + " --scale-target " + str(scaleUp[serviceName]), shell=True).decode("utf-8")
                time.sleep(3)
                # Update affinity_mask to new Replicas
                for i in range(3):
                    requests.post(getUrlByFuncName(serviceName), json={"numCores": len(getAffinityMaskByFuncName(serviceName)),"affinity_mask": getAffinityMaskByFuncName(serviceName)})
            except Exception as e:
                print("Error in kn service update == " + str(e))
            reqCores[serviceName] = 0
        time.sleep(1)
    time.sleep(1)


