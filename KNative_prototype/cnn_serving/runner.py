import json
import os
import sys
import signal
import threading
import socket
import logging
import psutil
import numpy as np
import time
import re
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")


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

# Global variables
serverSocket_ = None # serverSocket
actionModule = None # action module

checkTable = {}
checkTableShadow = {}
valueTable = {}
mapPIDtoIO = {}
lockCache = threading.Lock()

requestQueue = [] # queue of child processes
mapPIDtoStatus = {} # map from pid to status (running, waiting)

responseMapWindows = [] # map from pid to response

affinity_mask = {0,1,2,3,4,5,6,7}


# The function to update the core nums by request. 
def updateThread():
    # Shared vaiable: numCores
    global numCores

    # Bind to 0.0.0.0:5500
    myHost = '0.0.0.0'
    myPort = 5500 

    # Create a socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    # Handle request
    while True:
        # Accept a connection
        (clientSocket, _) = serverSocket.accept()
        data_ = clientSocket.recv(1024)
        dataStr = data_.decode('UTF-8')
        dataStrList = dataStr.splitlines()
        message = json.loads(dataStrList[-1])
        
        # Get the numCores and update the global variable
        numCores = message["numCores"]
        logging.debug("Update core num to {}".format(numCores))
        result = {"Response": "Ok"}
        msg = json.dumps(result)

        # Send the result and close the socket
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

def myFunction(data_, clientSocket_):
    global actionModule
    global numCores
    
    dataStr = data_.decode('UTF-8')
    dataStrList = dataStr.splitlines()
    numCoreFlag = False
    try:
        message = json.loads(dataStrList[-1])
        numCores = int(message["numCores"])
        numCoreFlag = True
        result = {"Response": "Ok"}
        msg = json.dumps(result)
    except:
        pass

    # Set the main function
    if numCoreFlag == False:
        result = actionModule.lambda_handler()

        # Send the result (Test Pid)
        result["myPID"] = os.getpid()
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
    try:
        clientSocket_.send(r.encode(encoding="utf-8"))
        clientSocket_.send(response_headers_raw.encode(encoding="utf-8"))
        clientSocket_.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
        clientSocket_.send(msg.encode(encoding="utf-8"))
    except:
        clientSocket_.close()
    clientSocket_.close()



def waitTermination(childPid):
    # wait for the running child process to exit
    os.waitpid(childPid, 0)
    for responseTime in responseMapWindows:
        if responseTime[0] == childPid:
            responseTime[1][1] = time.time()
            break
    requestQueue.remove(childPid)
    mapPIDtoStatus.pop(childPid)
    for index in range(len(requestQueue)):
        # Find the first waiting child process and run it.
        if(mapPIDtoStatus[requestQueue[index]] == "waiting"):
            mapPIDtoStatus[requestQueue[index]] = "running"
            psutil.Process(requestQueue[index]).resume()
            # logging.debug("Resume process for pid %d", requestQueue[index])
            break

def threadChangeStatus(clientSocket_):
    global mapPIDtoStatus
    global numCores
    while True:
        try:
            data_ = clientSocket_.recv(1024)
            if not data_:
                break
            dataStr = data_.decode('UTF-8')
            dataStrLines = dataStr.splitlines()
            for line in dataStrLines:
                if "unblocked" in line:
                    string1 = line.split(" - ")[-1]
                    unblockedID = int(re.search(r'\d+', string1).group()) # get PID
                    numRunning = 0 # number of running processes
                    for child in mapPIDtoStatus.copy():
                        if mapPIDtoStatus[child] == "running":
                            numRunning += 1
                    if numRunning < numCores:
                        mapPIDtoStatus[unblockedID] = "running"
                    else:
                        mapPIDtoStatus[unblockedID] = "waiting"
                        psutil.Process(unblockedID).suspend()
                    result = "ok"
                    clientSocket_.send(result.encode(encoding="utf-8"))
                    break
                elif "blocked" in line:
                    string1 = line.split(" - ")[-1]
                    blockedID = int(re.search(r'\d+', string1).group())
                    mapPIDtoStatus[blockedID] = "blocked"
                    for child in mapPIDtoStatus.copy():
                        if mapPIDtoStatus[child] == "waiting":
                            mapPIDtoStatus[child] = "running"
                            psutil.Process(requestQueue[child]).resume()
                            break
        except:
            break

def performIO(clientSocket_):
    global mapPIDtoStatus
    global numCores
    global checkTable
    global mapPIDtoIO
    global valueTable
    global checkTableShadow

    data_ = b''
    data_ += clientSocket_.recv(1024)
    dataStr = data_.decode('UTF-8')

    while True:
        dataStrList = dataStr.splitlines()
        
        message = None   
        try:
            message = json.loads(dataStrList[-1])
            break
        except:
            data_ += clientSocket_.recv(1024)
            dataStr = data_.decode('UTF-8')
    
    operation = message["operation"]
    blobName = message["blobName"]
    blockedID = message["pid"]

    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)

    mapPIDtoStatus[blockedID] = "blocked"
    for child in mapPIDtoStatus.copy():
        if mapPIDtoStatus[child] == "waiting":
            mapPIDtoStatus[child] = "running"
            psutil.Process(child).resume()
    
    if operation == "get":
        lockCache.acquire()
        if blobName in checkTable:
            myEvent = threading.Event()
            mapPIDtoIO[threading.get_native_id()] = myEvent
            checkTable[blobName].append(threading.get_native_id())
            checkTableShadow[blobName].append(threading.get_native_id())
            lockCache.release()
            myEvent.wait()
            blob_val = valueTable[blobName]
            mapPIDtoIO.pop(threading.get_native_id())
            checkTableShadow[blobName].remove(threading.get_native_id())
            if len(checkTableShadow[blobName]) == 0:
                checkTableShadow.pop(blobName)
                valueTable.pop(blobName)
        else:
            checkTable[blobName] = []
            checkTableShadow[blobName] = []
            checkTable[blobName].append(threading.get_native_id())
            lockCache.release()
            blob_val = (blob_client.download_blob()).readall()
            lockCache.acquire()
            valueTable[blobName] = blob_val
            checkTable[blobName].remove(threading.get_native_id())
            for elem in checkTable[blobName]:
                mapPIDtoIO[elem].set()
            checkTable.pop(blobName)
            lockCache.release()
    else:
        blob_client.upload_blob(message["value"])
        blob_val = "none"
    
    full_blob_name = blobName.split(".")
    proc_blob_name = full_blob_name[0] + "_" + str(blockedID) + full_blob_name[1]
    with open(proc_blob_name, "wb") as my_blob:
        my_blob.write(blob_val)

    numRunning = 0 # number of running processes
    for child in mapPIDtoStatus.copy():
        if mapPIDtoStatus[child] == "running":
            numRunning += 1
    if numRunning < numCores:
        mapPIDtoStatus[blockedID] = "running"
    else:
        mapPIDtoStatus[blockedID] = "waiting"
        psutil.Process(blockedID).suspend()

    messageToRet = json.dumps({"value":"OK"})
    clientSocket_.send(messageToRet.encode(encoding="utf-8"))
    clientSocket_.close()
    

def interceptThread():
    myHost = '0.0.0.0'
    myPort = 3338

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        threading.Thread(target=threadChangeStatus, args=(clientSocket,)).start()

def IOThread():
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        threading.Thread(target=performIO, args=(clientSocket,)).start()

def run():
    # serverSocket_: socket 
    # actionModule:  the module to execute
    # requestQueue: 
    # mapPIDtoStatus: store status for each process (waiting / running)
    global serverSocket_
    global actionModule
    global requestQueue
    global mapPIDtoStatus
    global numCores
    global responseMapWindows
    global affinity_mask
    # Set the core of mxcontainer
    numCores = 8
    os.sched_setaffinity(0, affinity_mask)

    # Set the address and port, the port can be acquired from environment variable
    myHost = '0.0.0.0'
    myPort = int(os.environ.get('PORT', 9999))

    # Bind the address and port
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    # serverSocket_ = serverSocket
    
    # Set actionModule
    import app
    actionModule = app

    # Set the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Redirect the stdOut and stdErr
    phOut = PrintHook()
    phOut.Start(MyHookOut)


    # Monitor numCore update
    threadUpdate = threading.Thread(target=updateThread)
    threadUpdate.start()

    # Monitor I/O Block
    # threadIntercept = threading.Thread(target=interceptThread)
    # threadIntercept.start()

    # Monitor I/O Block
    threadIntercept = threading.Thread(target=IOThread)
    threadIntercept.start()

    # If a request come, then fork.
    while(True):
        
        (clientSocket, address) = serverSocket.accept()
        print("Accept a new connection from %s" % str(address))
        
        data_ = b''

        data_ += clientSocket.recv(1024)

        dataStr = data_.decode('UTF-8')

        if 'Host' not in dataStr:
            msg = 'OK'
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
            try:
                clientSocket.send(r.encode(encoding="utf-8"))
                clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
                clientSocket.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
                clientSocket.send(msg.encode(encoding="utf-8"))
                clientSocket.close()
                continue
            except:
                clientSocket.close()
                continue

        while True:
            dataStrList = dataStr.splitlines()
            
            message = None   
            try:
                message = json.loads(dataStrList[-1])
                break
            except:
                data_ += clientSocket.recv(1024)
                dataStr = data_.decode('UTF-8')
        
        responseFlag = False
        if message != None:

            if "numCores" in message:
                numCores = int(message["numCores"])
                result = {"Response": "Ok"}
                responseMapWindows = []
                if "affinity_mask" in message:
                    affinity_mask = message["affinity_mask"]
                    os.sched_setaffinity(0, affinity_mask)
                msg = json.dumps(result)
                responseFlag = True

            if "Q" in message:
                i = []
                for responseTime in responseMapWindows:
                    if responseTime[1][1] != -1:
                        i.append(responseTime[1][1] - responseTime[1][0])
                if len(i) == 0:
                    result={"p95": 0}
                else:
                    result = {"p95": np.percentile(i, 95)}
                result["affinity_mask"] = list(affinity_mask)
                result["numCores"] = numCores
                msg = json.dumps(result)
                responseFlag = True

            if "Clear" in message:
                responseMapWindows = []
                
        if responseFlag == True:
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

            clientSocket.send(r.encode(encoding="utf-8"))
            clientSocket.send(response_headers_raw.encode(encoding="utf-8"))
            clientSocket.send('\r\n'.encode(encoding="utf-8")) # to separate headers from body
            clientSocket.send(msg.encode(encoding="utf-8"))
            clientSocket.close()
            continue



        # a status mark of whether the process can run based on the free resources
        waitForRunning = False

        # The processes are running
        numIsRunning = 0

        for child in mapPIDtoStatus.copy():
            if mapPIDtoStatus[child] == "running":
                numIsRunning += 1
        if numIsRunning >= numCores:
            waitForRunning = True # The process need to wait for resources

        # slide windows
        if len(responseMapWindows) >=100:
            responseMapWindows.pop(0)

        childProcess = os.fork()
        if childProcess != 0:
            responseMapWindows.append([childProcess, [time.time(), -1]])


        if childProcess == 0:
            # begin fork
            myFunction(data_, clientSocket)
            os._exit(os.EX_OK)
        else:
            # Append submit time to the responseMapWindows
            if waitForRunning:
                # If there is no free resources (cpu core) for the process to run, then we set the childprocess to sleep.
                logging.debug("Process {} is waiting for resources".format(childProcess))
                mapPIDtoStatus[childProcess] = "waiting"
                psutil.Process(childProcess).suspend()
            else:
                # If there are free resources (cpu core) for the process to run, then we let the childprocess to run.
                logging.debug("Process {} is running".format(childProcess))
                mapPIDtoStatus[childProcess] = "running"
            requestQueue.append(childProcess)
            # The childprocess is running, when it is finished, let the queue find waiting childprocesses
            threadWait = threading.Thread(target=waitTermination, args=(childProcess,))
            threadWait.start()

if __name__ == "__main__":
    # main programe
    # logging.basicConfig(level=logging.DEBUG)
    run()
