import psutil
import os
pid = os.getpid()
python_process = psutil.Process(pid)
memoryUse_old = 0
from azure.storage.blob import BlobServiceClient, BlobClient

fileAppend = open("../funcs.txt", "a")

memoryUse = python_process.memory_info()[0]/2.**30  # memory use in GB
print("--- WEB SERVE ---", file=fileAppend)
print('memory use 1:', memoryUse-memoryUse_old, file=fileAppend)

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**30  # memory use in GB
print('memory use 2:', memoryUse-memoryUse_old, file=fileAppend)

def main(params):
    blobName = "money.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())
    moneyF = open(blobName, "r")
    money = float(moneyF.readline())
    moneyF.close()
    money -= 100.0
    new_file = open("moneyTemp.txt", "w")
    new_file.write(str(money))
    new_file.close()
    fRead = open("moneyTemp.txt","rb")
    value = fRead.read()
    blobName = "money.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)
    return {"Money":"withdrawn"}

main({"test":"func"})
memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**30  # memory use in GB
print('memory use 3:', memoryUse-memoryUse_old, file=fileAppend)