import socket
import os

def download_blob_new(blb_cl):
    myHost = '0.0.0.0'
    myPort = 3333
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((myHost, myPort))
    clientSocket.sendall(("blocked - " + str(os.getpid())).encode(encoding="utf-8"))
    clientSocket.close()

    blb_to_ret = blb_cl.download_blob()

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((myHost, myPort))
    clientSocket.sendall(("unblocked - " + str(os.getpid())).encode(encoding="utf-8"))
    clientSocket.close()

    return blb_to_ret