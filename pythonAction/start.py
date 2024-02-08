import subprocess
import time 

subprocess.Popen(["python3","scheduler.py"])
subprocess.Popen(["python3","init.py"])

while True:
    time.sleep(100)