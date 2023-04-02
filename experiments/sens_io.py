import json
import time
from azure.storage.blob import BlobClient
import numpy as np
import sys
import threading
import random

myImages = []
for indImg in range(20):
    myImages.append("img"+str(indImg)+".png")

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"

def fetch_data_storage(key):
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=key)
    blob_client.download_blob()

def fetch_data(key, myId, tMerge):
    # Function: fetch the data value from the remote global storage
    global request_table
    global wait_events
    global return_values
    global numIssued
    global numWait
    global issueTimes
    global to_issue
    global to_inform

    issueTimes.append(time.time())

    leader = False
    toIssue = False
    
    lockTable.acquire()

    if key not in request_table:
        request_table[key] = []
        toIssue = True
        if len(to_issue) == 0:
            leader = True
        else:
            wait_event = threading.Event()
            to_inform[myId] = wait_event
        to_issue.append(myId)
    else:
        myEvent = threading.Event()
        wait_events[myId] = myEvent
    
    request_table[key].append(myId)

    lockTable.release()

    if toIssue:

        if leader:

            time.sleep(tMerge)

            lockTable.acquire()

            list_to_inform = to_issue
            list_to_inform.remove(myId)
            to_issue = []

            lockTable.release()
            
            numIssued += 1

            fetch_data_storage(key)

            for elemInf in list_to_inform:
                to_inform[elemInf].set()
        else:
            numWait += 1
            wait_event.wait()

        returnValue = {}
        returnValue["value"] = 1
        returnValue["seq_num"] = 2
        
        lockTable.acquire()

        
        
        return_values[key] = returnValue
        request_table[key].remove(myId)
        toWakeUp = request_table[key]
        for elem in toWakeUp:
            wait_events[elem].set()
            wait_events.pop(elem)

        if len(request_table[key]) == 0:
            request_table.pop(key)

        lockTable.release()
    
    else:
        
        myEvent.wait()

        lockTable.acquire()

        numWait += 1

        returnValue = return_values[key]
        request_table[key].remove(myId)
        if len(request_table[key]) == 0:
            request_table.pop(key)
        else:
            toWakeUp = request_table[key]
            for elem in toWakeUp:
                if elem in wait_events:
                    wait_events[elem].set()
                    wait_events.pop(elem)

        lockTable.release()

    return returnValue

def lambda_func(params):
    global times

    time1 = time.time()
    keyIn = params["inImg"]
    fetch_data(keyIn, params["myId"], params["tMerge"])
    time4 = time.time()

    times.append(time4-time1)
    return {"Image":"rotated"}

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

tMerges = [1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.001, 0.0005, 0]
prints1 = []
prints2 = []

for tMerge in tMerges:

    times = []

    request_table = {}
    wait_events = {}
    return_values = {}
    lockTable = threading.Lock()
    numIssued = 0
    numWait = 0

    to_issue = []
    to_inform = {}

    issueTimes = []

    duration = 5
    seed = 100
    rate = 500

    # generate Poisson's distribution of events 
    inter_arrivals = []
    np.random.seed(seed)
    beta = 1.0/rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
    instance_events = EnforceActivityWindow(0,duration,inter_arrivals)
    threads = []
    after_time, before_time = 0, 0

    st = 0
    for t in instance_events:
        st = st + t - (after_time - before_time)
        before_time = time.time()
        if st > 0:
            time.sleep(st)
        inImg = myImages[random.randint(0,len(myImages)-1)]
        keyArg = {"inImg":inImg, "outImg":"jovan_photo_rot.jpg", "myId":len(threads), "tMerge": tMerge}
        threadToAdd = threading.Thread(target=lambda_func, args=(keyArg,))
        threads.append(threadToAdd)
        threadToAdd.start()
        after_time = time.time()

    for thread in threads:
        thread.join()

    prints1.append(float(numWait/(numWait+numIssued)))
    prints2.append(np.percentile(times, 95))

print("Tmerge values = ", tMerges)
print("Percentage of merged I/Os = ", prints1)
print("Tail Latencies = ", prints2)