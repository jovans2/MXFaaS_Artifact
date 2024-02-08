import requests
import os
import threading
import threading
import pipes
import socket
import json

print("MY TID = ", threading.get_native_id())
print("MY PID = ", os.getpid())

def threadDo(clientSocket_):
    while True:
        try:
            data_ = clientSocket_.recv(1024)
            if not data_:
                break
            dataStr = data_.decode('UTF-8')
            dataStrLines = dataStr.splitlines()
            for line in dataStrLines:
                if ("unblocked" in line):
                    print("Thread id unblocked = " + line.split(" - ")[-1])
                elif ("blocked" in line):
                    print("Thread id blocked = " + line.split(" - ")[-1])
            print("Message = " + dataStr)
            if "unblocked" in dataStr:
                result = "ok"
                clientSocket_.send(result.encode(encoding="utf-8"))
                break
        except:
            break
    print("Thread done")
    

def threadCheck():
    myHost = '0.0.0.0'
    myPort = 3333

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, _) = serverSocket.accept()
        print("Spawn new thread")
        doThread = threading.Thread(target=threadDo, args=(clientSocket,))
        doThread.start()

#threading.Thread(target=threadCheck).start()
data_run = {"action_name":"/guest/funcB","action_version":"0.0.1","activation_id":"8cc0d938952e437e80d938952e637e9d","deadline":"1645662489031","namespace":"guest","transaction_id":"aYtvu7ZYIOBRi9FU3zuyGBSqu5mYDy3b","value":{"password":123,"username":"jovan"}}
#future = requests.post('http://192.168.0.1:8080/run', json=data_run)
future = requests.get("http://google.com")
print(future.text)
print(type(threading.get_native_id()))
#while(True):
#    pass