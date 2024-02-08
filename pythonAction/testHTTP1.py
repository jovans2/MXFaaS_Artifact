import ctypes
import requests
libc = ctypes.CDLL('libc.so.6')

def mywrapper():
    print("hello")

orig_recvfrom = libc.recvfrom
orig_open = libc.open
libc.recvfrom = mywrapper
libc.open = mywrapper
print(libc.recvfrom)
f = open("filename.txt", "r")