import os
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient
import dnld_blob

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

fileAppend = open("../funcs.txt", "a")

def lambda_handler():
    blobName = "img10.jpg"
    dnld_blob.download_blob_new(blobName)
    full_blob_name = blobName.split(".")
    proc_blob_name = full_blob_name[0] + "_" + str(os.getpid()) + full_blob_name[1]
    
    image = Image.open(proc_blob_name)
    img = image.transpose(Image.ROTATE_90)
    img.save('tempImage_'+str(os.getpid())+'.jpeg')

    fRead = open('tempImage_'+str(os.getpid())+'.jpeg',"rb")
    value = fRead.read()
    blobName = "img10_rot.jpg"
    dnld_blob.upload_blob_new(blobName, value)
    
    return {"Image":"rotated"}