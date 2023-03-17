import socket
import os

import socket
import os
import json
import base64
import time

def download_blob_new(blobName):
    myHost = '0.0.0.0'
    myPort = 3333
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((myHost, myPort))
    message = {"blobName": blobName, "operation": "get", "pid": os.getpid()}
    messageStr = json.dumps(message)
    clientSocket.sendall(messageStr.encode(encoding="utf-8"))

    data_ = b''
    data_ += clientSocket.recv(1024)

def upload_blob_new(blobName, value):
    myHost = '0.0.0.0'
    myPort = 3333
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((myHost, myPort))
    message = {"blobName": blobName, "operation": "set", "value": value, "pid": os.getpid()}
    messageStr = json.dumps(message)
    clientSocket.sendall(messageStr.encode(encoding="utf-8"))

    data_ = b''
    data_ += clientSocket.recv(1024)