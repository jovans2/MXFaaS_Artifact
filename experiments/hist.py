from PIL import Image
import io
import json
import time
from azure.storage.blob import BlobClient
import numpy as np
import sys
import threading
import random
from statistics import mean, median,variance,stdev

myImages = ["img1.jpg", "img2.jpg", "img3.jpg", "jovan_photo.jpg", "img5.jpg", "img6.jpg", "img7.jpg", "img8.jpg", "img9.jpg", "img10.jpg"]

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
times = []

request_table = {}
wait_events = {}
return_values = {}
lockTable = threading.Lock()
numIssued = 0
numWait = 0

issueTimes = []

def fetch_data_orig(key):
    global issueTimes

    key = key.replace("\'", "\"")
    keyDic = json.loads(key)
    containerName = keyDic["containerName"]
    blobName = keyDic["blobName"]
    blob_client = BlobClient.from_connection_string(connection_string, container_name=containerName, blob_name=blobName)

    locVal = "None"
    locSeqNum = -1

    try:
        issueTimes.append(time.time())
        download_stream = blob_client.download_blob()
        blob_properties = blob_client.get_blob_properties()
        sequence_number = blob_properties.metadata.get('sequence_number')
        locVal = download_stream.readall()
        locSeqNum = sequence_number
    except:
        pass

    returnValue = {}
    returnValue["value"] = locVal
    returnValue["seq_num"] = locSeqNum

    return returnValue

def fetch_data(key, myId):
    # Function: fetch the data value from the remote global storage
    global request_table
    global wait_events
    global return_values
    global numIssued
    global numWait
    global issueTimes

    issueTimes.append(time.time())

    toIssue = False
    
    lockTable.acquire()

    orig_req_table = request_table

    if key not in request_table:
        request_table[key] = []
        toIssue = True
    else:
        myEvent = threading.Event()
        wait_events[myId] = myEvent
    
    request_table[key].append(myId)

    lockTable.release()

    if toIssue:

        keyOrig = key
        key = key.replace("\'", "\"")
        keyDic = json.loads(key)
        containerName = keyDic["containerName"]
        blobName = keyDic["blobName"]
        blob_client = BlobClient.from_connection_string(connection_string, container_name=containerName, blob_name=blobName)

        locVal = "None"
        locSeqNum = -1

        try:
            download_stream = blob_client.download_blob()
            blob_properties = blob_client.get_blob_properties()
            sequence_number = blob_properties.metadata.get('sequence_number')
            locVal = download_stream.readall()
            locSeqNum = sequence_number
        except:
            pass

        key = keyOrig

        returnValue = {}
        returnValue["value"] = locVal
        returnValue["seq_num"] = locSeqNum
        
        lockTable.acquire()

        numIssued += 1
        
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
    keyIn = str({"containerName":"artifacteval","blobName":params["inImg"]})
    fetch_data_orig(keyIn)
    time4 = time.time()

    times.append(time4-time1)
    return {"Image":"rotated"}

def lambda_func_opt(params):
    global times

    time1 = time.time()
    keyIn = str({"containerName":"artifacteval","blobName":params["inImg"]})
    fetch_data(keyIn, params["myId"])
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

duration = 5
seed = 100
rate = 500

#while True:
# generate Poisson's distribution of events 
inter_arrivals = []
np.random.seed(seed)
beta = 1.0/rate
oversampling_factor = 2
inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
instance_events = EnforceActivityWindow(0,duration,inter_arrivals)
#print(len(instance_events))

threads = []
after_time, before_time = 0, 0

st = 0
for t in instance_events:
    st = st + t - (after_time - before_time)
    before_time = time.time()
    if st > 0:
        time.sleep(st)
    inImg = myImages[random.randint(0,len(myImages)-1)]
    keyArg = {"inImg":inImg, "outImg":"jovan_photo_rot.jpg", "myId":len(threads)}
    threadToAdd = threading.Thread(target=lambda_func, args=(keyArg,))
    threads.append(threadToAdd)
    threadToAdd.start()
    after_time = time.time()

for thread in threads:
    thread.join()

print("********************BASELINE******************** ")
print("Mean = ", mean(times))
print("Median = ", median(times))
print("P95 = ", np.percentile(times, 95))
print("P99 = ", np.percentile(times, 99))



duration = 5
seed = 100
rate = 500

#while True:
# generate Poisson's distribution of events 
inter_arrivals = []
np.random.seed(seed)
beta = 1.0/rate
oversampling_factor = 2
inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
instance_events = EnforceActivityWindow(0,duration,inter_arrivals)
#print(len(instance_events))

threads = []
times = []
issueTimes = []
after_time, before_time = 0, 0

st = 0
for t in instance_events:
    st = st + t - (after_time - before_time)
    before_time = time.time()
    if st > 0:
        time.sleep(st)
    inImg = myImages[random.randint(0,len(myImages)-1)]
    keyArg = {"inImg":inImg, "outImg":"jovan_photo_rot.jpg", "myId":len(threads)}
    threadToAdd = threading.Thread(target=lambda_func_opt, args=(keyArg,))
    threads.append(threadToAdd)
    threadToAdd.start()
    after_time = time.time()

for thread in threads:
    thread.join()

print("********************MXFaaS******************** ")
print("Mean = ", mean(times))
print("Median = ", median(times))
print("P95 = ", np.percentile(times, 95))
print("P99 = ", np.percentile(times, 99))