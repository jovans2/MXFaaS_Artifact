import time
from azure.storage.blob import BlobServiceClient, BlobClient

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

fileAppend = open("../funcs.txt", "a")

def main(params):
    t1 = time.time()
    blobName = "money.txt"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        t3 = time.time()
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())
        t4 = time.time()
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
    t5 = time.time()
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)
    t6 = time.time()
    t2 = time.time()
    print("--- WEB SERVE ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4+t6-t3-t5, file=fileAppend)
    return {"Money":"withdrawn"}

main({"test":"func"})