from csv import reader
import matplotlib.pyplot as plt
import numpy as np

per_blob_timestamps = {}
with open('azurefunctions-accesses-2020.csv', 'r') as read_obj:
    csv_reader = reader(read_obj)
    #    row0      row1         row2        row3             row4                   row5          row6          row7          row8      row9    row10
    #
    # Timestamp	AnonRegion	AnonUserId	AnonAppName	AnonFunctionInvocationId	AnonBlobName	BlobType	AnonBlobETag	BlobBytes	Read	Write
    for row in csv_reader:
        blobName = row[5]
        invocationId = row[4]
        if blobName == "AnonBlobName":
            continue
        timestamp = int(row[0])
        if blobName not in per_blob_timestamps:
            per_blob_timestamps[blobName] = []
        per_blob_timestamps[blobName].append(timestamp)

diff_times = []
overall = 0
index = 0
for elem in per_blob_timestamps:
    timestamp_list = per_blob_timestamps[elem]
    if len(timestamp_list) > 1:
        timestamp_list.sort()
        new_timestamp_list = [j-i for i, j in zip(timestamp_list[:-1], timestamp_list[1:])]
        for new_elem in new_timestamp_list:
            overall += 1
            if new_elem <= 500:
                diff_times.append(new_elem)

fileWrite = open("diff_times.txt","w")
fileWrite.write(str(diff_times))
fileWrite.close()

from matplotlib.pyplot import figure

diffFile = open("diff_times.txt","r")
strDiff = diffFile.readline()
res = strDiff.strip('][').split(', ')
diff_times = []
for elem in res:
    diff_times.append(int(elem))

x = np.sort(diff_times)
y = np.arange(len(diff_times)) / float(len(diff_times))

figure(figsize=(8, 3))
plt.xlabel('Interarrival time (ms)',fontsize=18)
plt.ylabel('CDF',fontsize=18)
  
plt.plot(x, y, color="black", linewidth=3)

plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.tight_layout()
plt.savefig("azure_blobs.png")