import pickle
import json
import os
import socket
import sys
import signal
import runner

def signal_handler(sig, frame):
    serverSocket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

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

phOut = PrintHook()
phOut.Start(MyHookOut)

myHost = '0.0.0.0'
myPort = 8080

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((myHost, myPort))
serverSocket.listen(1)

(clientSocket, address) = serverSocket.accept()
clientAddress = address[0]

data = clientSocket.recv(102400)
dataStr = data.decode('UTF-8')
dataStrList = dataStr.splitlines()
message = json.loads(dataStrList[-1])
value = message['value']
env = value['env']
code = value['code']
numCores = env['numCores']
print(code, file=open("/pythonAction/actionToExec.py","w"))

msg = "OK"

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

runner.run(env,serverSocket,numCores)