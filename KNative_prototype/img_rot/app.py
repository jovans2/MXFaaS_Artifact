import time
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient
import dnld_blob

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

fileAppend = open("../funcs.txt", "a")

def lambda_handler():
    t1 = time.time()
    blobName = "img10.jpg"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(blobName, "wb") as my_blob:
        t3 = time.time()
        download_stream = dnld_blob.download_blob_new(blob_client)
        t4 = time.time()
        my_blob.write(download_stream.readall())
    image = Image.open(blobName)
    img = image.transpose(Image.ROTATE_90)
    img.save('newImage.jpeg')
    fRead = open("newImage.jpeg","rb")
    value = fRead.read()
    blobName = "img10_rot.jpg"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    t5 = time.time()
    dnld_blob.upload_blob_new(blob_client, value)
    t6 = time.time()
    t2 = time.time()
    print("--- IMG ROT ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4-t3+t6-t5, file=fileAppend)
    return {"Image":"rotated"}