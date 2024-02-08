import json
import os
from statistics import mean
import sys
import signal
import threading
import socket
import pickle
import requests
import time
import psutil

def signal_handler(sig, frame):
    serverSocket_.close()
    sys.exit(0)

class PrintHook:
    def __init__(self,out=1):
        self.func = None
        self.origOut = None
        self.out = out

    def TestHook(self,text):
        f = open('hook_log.txt','a')
        f.write(text)
        f.close()
        return 0,0,text

    def Start(self,func=None):
        if self.out:
            sys.stdout = self
            self.origOut = sys.__stdout__
        else:
            sys.stderr= self
            self.origOut = sys.__stderr__
            
        if func:
            self.func = func
        else:
            self.func = self.TestHook

    def Stop(self):
        self.origOut.flush()
        if self.out:
            sys.stdout = sys.__stdout__
        else:
            sys.stderr = sys.__stderr__
        self.func = None

    def flush(self):
        self.origOut.flush()
  
    def write(self,text):
        proceed = 1
        lineNo = 0
        addText = ''
        if self.func != None:
            proceed,lineNo,newText = self.func(text)
        if proceed:
            if text.split() == []:
                self.origOut.write(text)
            else:
                if self.out:
                    if lineNo:
                        try:
                            raise "Dummy"
                        except:
                            codeObject = sys.exc_info()[2].tb_frame.f_back.f_code
                            fileName = codeObject.co_filename
                            funcName = codeObject.co_name     
                self.origOut.write(newText)

def MyHookOut(text):
    return 1,1,' -- pid -- '+ str(os.getpid()) + ' ' + text

serverSocket_ = None
actionModule = None
mapPIDtoPriority = {}
sleepTimes = {}
requestQueue = []
mapPIDtoStatus = {}
mapPIDtoIdle = {}
mapPIDtoWaiting = {}
lastWaiting = {}
idleTimePerEpoch = []
numInserted = 0
numCores = 8
waitTimePerEpoch = []
numActualCalls = 0

def myFunction(clientSocket_):
    global actionModule
    global numInserted
    data_ = clientSocket_.recv(1024)
    dataStr = data_.decode('UTF-8')
    dataStrList = dataStr.splitlines()
    message = json.loads(dataStrList[-1])
    args = message['value']
    result = actionModule.main(args)
    result["myPID"] = os.getpid()
    result["idleTime"] = float(sum(idleTimePerEpoch) / max(numInserted,1))
    result["waitingTime"] = float(sum(waitTimePerEpoch) / max(numInserted,1))
    msg = json.dumps(result)

    response_headers = {
        'Content-Type': 'text/html; encoding=utf8',
        'Content-Length': len(msg),
        'Connection': 'close',
    }

    response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

    response_proto = 'HTTP/1.1'
    response_status = '200'
    response_status_text = 'OK' # this can be random

    # sending all this stuff
    r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)

    clientSocket_.send(r.encode(encoding="utf-8"))
    clientSocket_.send(response_headers_raw.encode(encoding="utf-8"))
    clientSocket_.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
    clientSocket_.send(msg.encode(encoding="utf-8"))

    clientSocket_.close()

class Message:
    def __init__(self):
        self.url_func = ""
        self.parameters = {}
        self.authentication = ("", "")
        self.arguments = {}
        self.PID = -1
        self.sleepNum = 0.0

def mySchedulerFunction(clientSocket):
    global mapPIDtoPriority
    global mapPIDtoStatus
    global mapPIDtoIdle
    global numCores
    global numActualCalls
    data = b''
    while True:
        data += clientSocket.recv(1024)
        try:
            pickle.loads(data)
            break
        except:
            pass
    mReceived = pickle.loads(data)
    mapPIDtoPriority[mReceived.PID] += 1
    #from this moment we know process is blocked -- can schedule another one to run
    mapPIDtoStatus[mReceived.PID] = "blocked"
    for index in range(len(requestQueue)):
        if(mapPIDtoStatus[requestQueue[index]] == "waiting"):
            mapPIDtoWaiting[requestQueue[index]] += time.time() - lastWaiting[requestQueue[index]]
            mapPIDtoStatus[requestQueue[index]] = "running"
            psutil.Process(requestQueue[index]).resume()
            break
    start = time.time()
    future = originalRequest(mReceived.url_func, params=mReceived.parameters, auth=mReceived.authentication, json=mReceived.arguments, verify=False)
    numActualCalls += 1
    print("Num actual calls = " + str(numActualCalls))
    end = time.time()
    mapPIDtoIdle[mReceived.PID] += end - start
    clientSocket.sendall(pickle.dumps(future))
    clientSocket.close()
    numRunning = 0
    for index in range(len(requestQueue)):
        if(mapPIDtoStatus[requestQueue[index]] == "running"):
            numRunning += 1
    if numRunning >= numCores:
        lastWaiting[mReceived.PID] = float(time.time())
        mapPIDtoStatus[mReceived.PID] = "waiting"
        psutil.Process(mReceived.PID).suspend()

def sleepRequest(clientSocket):
    global mapPIDtoPriority
    global mapPIDtoStatus
    global mapPIDtoIdle
    global numCores
    global sleepTimes
    data = b''
    while True:
        data += clientSocket.recv(1024)
        try:
            pickle.loads(data)
            break
        except:
            pass
    mReceived = pickle.loads(data)
    mapPIDtoPriority[mReceived.PID] += 1
    num = mReceived.sleepNum
    #from this moment we know process is blocked -- can schedule another one to run
    mapPIDtoStatus[mReceived.PID] = "blocked"
    for index in range(len(requestQueue)):
        if(mapPIDtoStatus[requestQueue[index]] == "waiting"):
            mapPIDtoWaiting[requestQueue[index]] += time.time() - lastWaiting[requestQueue[index]]
            mapPIDtoStatus[requestQueue[index]] = "running"
            psutil.Process(requestQueue[index]).resume()
            break
    start = time.time()
    previousTime = 0
    if (mReceived.PID%10) in sleepTimes:
        previousTime = sleepTimes[mReceived.PID%10]
    if previousTime > start:
        originalSleep(previousTime - start)
    else:
        sleepTimes[mReceived.PID%10] = start + num
        originalSleep(num)
    end = time.time()
    clientSocket.sendall(b'Done sleeping')
    clientSocket.close()
    mapPIDtoIdle[mReceived.PID] += end - start
    numRunning = 0
    for index in range(len(requestQueue)):
        if(mapPIDtoStatus[requestQueue[index]] == "running"):
            numRunning += 1
    if numRunning >= numCores:
        lastWaiting[mReceived.PID] = float(time.time())
        mapPIDtoStatus[mReceived.PID] = "waiting"
        psutil.Process(mReceived.PID).suspend()

def sendRequest(url, params={}, auth=("",""), json={}, verify=False):
    myHost = '0.0.0.0'
    myPort = 1234
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((myHost, myPort))
    message = Message()
    message.PID = os.getpid()
    message.url_func = url
    message.parameters = params
    message.authentication = auth
    message.arguments = json
    mToSend = pickle.dumps(message)
    clientSocket.sendall(mToSend)
    data = b''
    while True:
        data += clientSocket.recv(1024)
        try:
            pickle.loads(data)
            break
        except:
            pass
    return pickle.loads(data)

def sleepWrapper(num):
    myHost = '0.0.0.0'
    myPort = 1235
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((myHost, myPort))
    message = Message()
    message.PID = os.getpid()
    message.sleepNum = num
    mToSend = pickle.dumps(message)
    clientSocket.sendall(mToSend)
    data = b''
    data += clientSocket.recv(1024)

originalRequest = requests.post
requests.post = sendRequest

originalSleep = time.sleep
time.sleep = sleepWrapper


def schedulerThread():
    global numCores
    myHost = '0.0.0.0'
    myPort = 1234

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, address) = serverSocket.accept()
        thread = threading.Thread(target=mySchedulerFunction, args=(clientSocket,))
        thread.start()

def sleeperThread():
    global numCores
    myHost = '0.0.0.0'
    myPort = 1235

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, address) = serverSocket.accept()
        thread = threading.Thread(target=sleepRequest, args=(clientSocket,))
        thread.start()

def epochThread():
    global idleTimePerEpoch
    global waitTimePerEpoch
    global numInserted
    myHost = '0.0.0.0'
    myPort = 1235

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, address) = serverSocket.accept()
        result = {}
        result["idleTime"] = float(sum(idleTimePerEpoch) / numInserted)
        result["waitingTime"] = float(sum(waitTimePerEpoch) / numInserted)
        msg = json.dumps(result)

        response_headers = {
            'Content-Type': 'text/html; encoding=utf8',
            'Content-Length': len(msg),
            'Connection': 'close',
        }

        response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())

        response_proto = 'HTTP/1.1'
        response_status = '200'
        response_status_text = 'OK'

        r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)

        clientSocket.send(r.encode(encoding="utf-8"))
        clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
        clientSocket.send('\r\n'.encode(encoding="utf-8"))
        clientSocket.send(msg.encode(encoding="utf-8"))

        clientSocket.close()

def waitTermination(childPid):
    global mapPIDtoStatus
    global mapPIDtoIdle
    global numInserted
    os.waitpid(childPid, 0)
    #from this moment we know process is completed -- can schedule another one to run
    requestQueue.remove(childPid)
    mapPIDtoStatus.pop(childPid)
    idleTime = mapPIDtoIdle[childPid]
    waitTime = mapPIDtoWaiting[childPid]
    idleTimePerEpoch.pop(0)
    idleTimePerEpoch.append(idleTime)
    waitTimePerEpoch.pop(0)
    waitTimePerEpoch.append(waitTime)
    numInserted = min(numInserted+1, 10)
    mapPIDtoIdle.pop(childPid)
    mapPIDtoWaiting.pop(childPid)
    for index in range(len(requestQueue)):
        if(mapPIDtoStatus[requestQueue[index]] == "waiting"):
            mapPIDtoWaiting[requestQueue[index]] += time.time() - lastWaiting[requestQueue[index]]
            mapPIDtoStatus[requestQueue[index]] = "running"
            psutil.Process(requestQueue[index]).resume()
            break

def run(env, serverSocket, _numCores):
    global serverSocket_
    global actionModule
    global mapPIDtoPriority
    global requestQueue
    global mapPIDtoStatus
    global mapPIDtoIdle
    global idleTimePerEpoch
    global waitTimePerEpoch
    global numInserted
    global numCores
    numInserted = 0
    numCores = int(_numCores)
    for i in range(0, 10):
        idleTimePerEpoch.append(0)
        waitTimePerEpoch.append(0)
    threadScheduler = threading.Thread(target=schedulerThread)
    threadScheduler.start()
    threadSleeper = threading.Thread(target=sleeperThread)
    threadSleeper.start()
    #threadEpoch = threading.Thread(target=epochThread)
    #threadEpoch.start()
    serverSocket_ = serverSocket
    import actionToExec
    actionModule = actionToExec
    os.environ = env
    signal.signal(signal.SIGINT, signal_handler)
    phOut = PrintHook()
    phOut.Start(MyHookOut)
    while(True):
        (clientSocket, address) = serverSocket.accept()
        alreadyRunning = False
        numRunning = 0
        for child in mapPIDtoStatus:
            if mapPIDtoStatus[child] == "running":
                numRunning += 1
        if numRunning >= numCores:
            alreadyRunning = True
        #if not alreadyRunning:
        childProcess = os.fork()
        if childProcess == 0:
            myFunction(clientSocket)
            os._exit(os.EX_OK)
        else:
            if alreadyRunning:
                mapPIDtoStatus[childProcess] = "waiting"
                lastWaiting[childProcess] = time.time()
                psutil.Process(childProcess).suspend()
            else:
                mapPIDtoStatus[childProcess] = "running"
            requestQueue.append(childProcess)
            mapPIDtoIdle[childProcess] = 0
            mapPIDtoWaiting[childProcess] = 0
            mapPIDtoPriority[childProcess] = 0
            threadWait = threading.Thread(target=waitTermination, args=(childProcess,))
            threadWait.start()
            clientSocket.close()