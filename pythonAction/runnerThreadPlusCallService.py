import threading
import socket
import os
import sys
import time
import json
import re
import signal
import requests

serverSocket_ = None
actionModule = None
mapPIDtoEvents = {}
sleepTimes = {}
requestQueue = []
mapPIDtoStatus = {}
mapPIDtoIdle = {}
mapPIDtoWaiting = {}
lastWaiting = {}
idleTimePerEpoch = []
waitTimePerEpoch = []
numCores = 32
numRunning = 0
numInserted = 0
lockStatus = threading.Lock()
translation_table = {}

def checkPrint():
    print("Hello world from Runner!")

def callService(serviceName, parameters, arguments):
    global translation_table
    if serviceName not in translation_table:
        APIHOST = "http://192.168.5.1:3233"
        base_url = APIHOST + '/api/v1/namespaces/guest/actions/'
        send_url = base_url + serviceName
        AUTH_KEY = "23bc46b1-71f6-4ed5-8c54-816aa4f8c502:123zO3xZCLrMN6v2BKK1dXYFpXlPkccOFqm12CdAsMgRU4VrNZ9lyGVCGuMDGIwP" 
        user_pass = AUTH_KEY.split(':')
        authentication = (user_pass[0], user_pass[1])
        result = requests.post(send_url, params=parameters, auth=authentication, json=arguments, verify=False)
        resultAsDict = json.loads(result.text)
        serviceIP = resultAsDict["myIP"]
        instanceID = resultAsDict["instance"]
        print("Instance ID = ", instanceID)
        translation_table[serviceName] = serviceIP
        return result
    else:
        serviceIP = translation_table[serviceName]
        return requests.post("http://"+serviceIP, json={'value':arguments}, verify=False)

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

#before (threading. current_thread().ident)%10000
def MyHookOut(text):
    return 1,1,' -- pid -- '+ str(threading.get_native_id()) + ' ' + text

def sleepWrapper(num):
    global mapPIDtoStatus
    global numCores
    global numRunning

    lockStatus.acquire()
    mapPIDtoStatus[threading.get_native_id()] = "blocked"
    numRunning -= 1
    for child in mapPIDtoStatus:
        if mapPIDtoStatus[child] == "waiting":
            mapPIDtoStatus[child] = "running"
            numRunning += 1
            mapPIDtoEvents[child].set()
            break
    lockStatus.release()

    originalSleep(num)
    
    waitNeed = 0
    lockStatus.acquire()
    if numRunning < numCores:
        mapPIDtoStatus[threading.get_native_id()] = "running"
    else:
        mapPIDtoStatus[threading.get_native_id()] = "waiting"
        waitNeed = 1
    lockStatus.release()

    if waitNeed == 1:
        mapPIDtoEvents[threading.get_native_id()].wait()


def postWrapper(url, data=None, jsonElem=None, **kwargs):
    global mapPIDtoStatus
    global numCores
    global numRunning

    lockStatus.acquire()
    mapPIDtoStatus[threading.get_native_id()] = "blocked"
    numRunning -= 1
    for child in mapPIDtoStatus:
        if mapPIDtoStatus[child] == "waiting":
            mapPIDtoStatus[child] = "running"
            numRunning += 1
            mapPIDtoEvents[child].set()
            break
    lockStatus.release()

    toReturnValue = originalPost(url, data, jsonElem, **kwargs)
    
    waitNeed = 0
    lockStatus.acquire()
    if numRunning < numCores:
        mapPIDtoStatus[threading.get_native_id()] = "running"
    else:
        mapPIDtoStatus[threading.get_native_id()] = "waiting"
        waitNeed = 1
    lockStatus.release()

    if waitNeed == 1:
        mapPIDtoEvents[threading.get_native_id()].wait()
    
    return toReturnValue


def myFunction(clientSocket_, threadEvent):
    global actionModule
    global numInserted
    global waitTimePerEpoch
    global idleTimePerEpoch
    global mapPIDtoStatus
    global numCores 
    global mapPIDtoEvents
    global numRunning

    waitNeed = 0
    lockStatus.acquire()
    if numRunning < numCores:
        mapPIDtoStatus[threading.get_native_id()] = "running"
        numRunning += 1
    else:
        mapPIDtoStatus[threading.get_native_id()] = "waiting"
        waitNeed = 1
    mapPIDtoEvents[threading.get_native_id()] = threadEvent
    lockStatus.release()

    if waitNeed == 1:
        threadEvent.wait()
    while(True):
        try:
            data_ = clientSocket_.recv(1024)
            dataStr = data_.decode('UTF-8')
            if dataStr == "":
                return
            dataStrList = dataStr.splitlines()
            message = json.loads(dataStrList[-1])
            break
        except:
            pass
    arguments = message['value']
    
    result = actionModule.main(arguments)
    result["myPID"] = (threading.get_native_id())
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
    response_status_text = 'OK'
    r = '%s %s %s\r\n' % (response_proto, response_status, response_status_text)

    clientSocket_.send(r.encode(encoding="utf-8"))
    clientSocket_.send(response_headers_raw.encode(encoding="utf-8"))
    clientSocket_.send('\r\n'.encode(encoding="utf-8"))
    clientSocket_.send(msg.encode(encoding="utf-8"))

    clientSocket_.close()

    lockStatus.acquire()
    mapPIDtoStatus.pop(threading.get_native_id())
    mapPIDtoEvents.pop(threading.get_native_id())
    numRunning -= 1
    for child in mapPIDtoStatus:
        if mapPIDtoStatus[child] == "waiting":
            mapPIDtoStatus[child] = "running"
            numRunning += 1
            mapPIDtoEvents[child].set()
            break
    lockStatus.release()


def evictThread():
    global translation_table
    myHost = '0.0.0.0'
    myPort = 5555

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        data_ = clientSocket.recv(1024)
        dataStr = data_.decode('UTF-8')
        dataStrList = dataStr.splitlines()
        message = json.loads(dataStrList[-1])
        copy_translation_table = {}
        for elem in translation_table:
            if (message["callee"]!=translation_table[elem]):
                copy_translation_table[elem] = translation_table[elem]
        translation_table = copy_translation_table
        result = {}
        result["Response"] = "Ok"
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

def updateThread():
    global numCores
    myHost = '0.0.0.0'
    myPort = 5500

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        data_ = clientSocket.recv(1024)
        dataStr = data_.decode('UTF-8')
        dataStrList = dataStr.splitlines()
        message = json.loads(dataStrList[-1])
        numCores = message["numCores"]
        result = {}
        result["Response"] = "Ok"
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

def threadDo(clientSocket_):
    global mapPIDtoStatus
    global numCores
    global numRunning
    while True:
        try:
            data_ = clientSocket_.recv(1024)
            if not data_:
                break
            dataStr = data_.decode('UTF-8')
            dataStrLines = dataStr.splitlines()
            for line in dataStrLines:
                if ("unblocked" in line):
                    string1 = line.split(" - ")[-1]
                    unblockedID = int(re.search(r'\d+', string1).group())
                    waitNeed = 0
                    lockStatus.acquire()
                    if numRunning < numCores:
                        mapPIDtoStatus[unblockedID] = "running"
                    else:
                        mapPIDtoStatus[unblockedID] = "waiting"
                        waitNeed = 1
                    lockStatus.release()

                    if waitNeed == 1:
                        mapPIDtoEvents[unblockedID].wait()
                    result = "ok"
                    clientSocket_.send(result.encode(encoding="utf-8"))
                    break
                elif ("blocked" in line):
                    string1 = line.split(" - ")[-1]
                    blockedID = int(re.search(r'\d+', string1).group())
                    lockStatus.acquire()
                    mapPIDtoStatus[blockedID] = "blocked"
                    numRunning -= 1
                    for child in mapPIDtoStatus:
                        if mapPIDtoStatus[child] == "waiting":
                            mapPIDtoStatus[child] = "running"
                            numRunning += 1
                            mapPIDtoEvents[child].set()
                            break
                    lockStatus.release()
        except:
            break

def interceptThread():
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        threading.Thread(target=threadDo, args=(clientSocket,)).start()

def run(env, serverSocket, _numCores):
    global serverSocket_
    global actionModule
    global requestQueue
    global mapPIDtoStatus
    global mapPIDtoIdle
    global idleTimePerEpoch
    global waitTimePerEpoch
    global numInserted
    global numCores

    for _ in range(0, 10):
        idleTimePerEpoch.append(0)
        waitTimePerEpoch.append(0)
    
    threadEvict = threading.Thread(target=evictThread)
    threadEvict.start()

    threadUpdate = threading.Thread(target=updateThread)
    threadUpdate.start()

    threadIntercept = threading.Thread(target=interceptThread)
    threadIntercept.start()

    numCores = int(_numCores)
    serverSocket_ = serverSocket
    import actionToExec
    actionModule = actionToExec
    os.environ = env
    signal.signal(signal.SIGINT, signal_handler)
    phOut = PrintHook()
    phOut.Start(MyHookOut)
    while(True):
        (clientSocket, address) = serverSocket.accept()
        thrEvent = threading.Event()
        threadServe = threading.Thread(target=myFunction, args=(clientSocket,thrEvent,))
        threadServe.start()

originalSleep = time.sleep
time.sleep = sleepWrapper

originalPost = requests.post
requests.post = postWrapper

if __name__ == "__main__":
    run()