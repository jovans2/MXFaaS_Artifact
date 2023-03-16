import statistics
import collections
import numpy as np
from csv import reader
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure


azureFile = open("AzureFunctionsInvocationTraceForTwoWeeksJan2021.txt","r")

figure(figsize=(8, 3))
plt.xscale('log',base=2)

index = 0
response_times = []
apps = set()
funcPerApps = {}
lineFile = []
for line in azureFile:
    index += 1
    if index == 1:
        continue
    lineFile.append(line)
    listLines = line.split(",")
    duration = float(listLines[3])
    apps.add(listLines[0])
    if listLines[0] not in funcPerApps:
        funcPerApps[listLines[0]] = set()
    funcPerApps[listLines[0]].add(listLines[1])

print(index)
print(len(apps))
print(index / len(apps))

numbers = []
targetFunc = ""
for key in funcPerApps:
    numbers.append(len(funcPerApps[key]))

print(min(numbers))
print(max(numbers))
print(statistics.mean(numbers))

apps_per_minute = {}
for line in lineFile:
    listLines = line.split(",")
    duration = float(listLines[3])
    endTime = float(listLines[2])
    startTime = endTime - duration
    startMin = int(startTime/60)
    appName = listLines[0]
    if appName not in apps_per_minute:
        apps_per_minute[appName] = []
    apps_per_minute[appName].append(startMin)

calls_per_minute = []
bucket_2 = 0
bucket_5 = 0
bucket_10 = 0
bucket_20 = 0
bucket_50 = 0
bucket_100 = 0
bucket_200 = 0
bucket_500 = 0
bucket_1000 = 0
overallNum = 0
for elem in apps_per_minute:
    listMinutes = apps_per_minute[elem]
    frequency = {}
    for minute in listMinutes:
        if minute not in frequency:
            frequency[minute] = 0
        frequency[minute] += 1
    for key in frequency:
        overallNum += 1
        if frequency[key] <= 500 and frequency[key] > 0:
            calls_per_minute.append(frequency[key])
        if frequency[key] >= 2:
            bucket_2 += 1
        if frequency[key] >= 5:
            bucket_5 += 1
        if frequency[key] >= 10:
            bucket_10 += 1
        if frequency[key] >= 20:
            bucket_20 += 1
        if frequency[key] >= 50:
            bucket_50 += 1
        if frequency[key] >= 100:
            bucket_100 += 1
        if frequency[key] >= 200:
            bucket_200 += 1
        if frequency[key] >= 500:
            bucket_500 += 1
        if frequency[key] >= 1000:
            bucket_1000 += 1

x = np.sort(calls_per_minute)
y = np.arange(len(calls_per_minute)) / float(len(calls_per_minute))

plt.xlabel('Number of concurrent invocations of the same function', fontsize=18)
plt.ylabel('CDF', fontsize=18)

print("--- Azure ---")
print(x)
print(y)
  
plt.plot(x, y, label="Azure", color="black", linewidth=3)


plt.subplots_adjust(wspace=0.3, hspace=0.5)

plt.legend(fontsize=18)

plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.tight_layout()
plt.savefig("azure_burstiness.png")