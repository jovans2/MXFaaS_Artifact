import time
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

fileAppend = open("../funcs.txt", "a")

def main(params):
    t1 = time.time()
    blobName = "ordIDs.txt"
    ordID = 1
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        t3 = time.time()
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())
        t4 = time.time()
    orderF = open(blobName, "r")
    orderIDs = orderF.readlines()
    orderPrice = -1
    for line in orderIDs:
        lineStr = line.split(" ")
        if int(lineStr[0]) == ordID:
            orderPrice = float(lineStr[1])
            break
    orderF.close()
    new_file = open("ordTemp.txt", "w")
    new_file.write(str(uuid.uuid1()) + " ---" + str(orderPrice))
    new_file.close()
    fRead = open("ordTemp.txt","rb")
    value = fRead.read()
    blobName = "ordPrice.txt"
    t5 = time.time()
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)
    t6 = time.time()
    t2 = time.time()
    print("--- Create Ord ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4+t6-t3-t5, file=fileAppend)
    return {"Order":"created"}

main({"test":"func"})