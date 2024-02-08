import socket
import requests
import threading
import pickle

class Message:
    def __init__(self):
        self.url_func = ""
        self.parameters = {}
        self.authentication = ("", "")
        self.arguments = {}

def myFunction(clientSocket):
    data = clientSocket.recv(1024)
    mReceived = pickle.loads(data)
    future = requests.post(mReceived.url_func, params=mReceived.parameters, auth=mReceived.authentication, json=mReceived.arguments, verify=False)
    clientSocket.sendall(str(future.content).encode('utf-8'))
    clientSocket.close()

def sendRequest(url, params={}, auth=("",""), args={}):
    myHost = '0.0.0.0'
    myPort = 1234
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((myHost, myPort))
    message = Message()
    message.url_func = url
    message.parameters = params
    message.authentication = auth
    message.arguments = args
    mToSend = pickle.dumps(message)
    clientSocket.sendall(mToSend)
    data = clientSocket.recv(1024)
    data = data.decode("utf-8")[2:-1]
    print(data)
    return data

if __name__ == "__main__":
    myHost = '0.0.0.0'
    myPort = 1234

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((myHost, myPort))
    serverSocket.listen(1)

    while True:
        (clientSocket, address) = serverSocket.accept()
        thread = threading.Thread(target=myFunction, args=(clientSocket,))
        thread.start()
