import os
from azure.storage.blob import BlobServiceClient, BlobClient
import dnld_blob

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

def lambda_handler():
    blobName = "money.txt"
    dnld_blob.download_blob_new(blobName)
    
    moneyF = open("money_"+str(os.getpid())+".txt", "r")
    money = float(moneyF.readline())
    moneyF.close()
    money -= 100.0
    new_file = open("moneyTemp"+str(os.getpid())+".txt", "w")
    new_file.write(str(money))
    new_file.close()
    fReadname = "moneyTemp"+str(os.getpid())+".txt" 
    blobName = "money.txt"
    dnld_blob.upload_blob_new(blobName, fReadname)

    return {"Money":"withdrawn"}