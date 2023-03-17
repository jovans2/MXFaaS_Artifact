import psutil
import os
pid = os.getpid()
python_process = psutil.Process(pid)
memoryUse_old = 0
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient

fileAppend = open("../funcs.txt", "a")

memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print("--- IMG ROT ---", file=fileAppend)
print('memory use 1:', memoryUse-memoryUse_old, file=fileAppend)

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print('memory use 2:', memoryUse-memoryUse_old, file=fileAppend)

def main(params):
    blobName = "img10.jpg"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())
    image = Image.open(blobName)
    img = image.transpose(Image.ROTATE_90)
    img.save('newImage.jpeg')
    fRead = open("newImage.jpeg","rb")
    value = fRead.read()
    blobName = "img10_rot.jpg"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)
    return {"Image":"rotated"}

main({"test":"func"})
memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print('memory use 3:', memoryUse-memoryUse_old, file=fileAppend)