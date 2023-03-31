import psutil
import os
pid = os.getpid()
python_process = psutil.Process(pid)
memoryUse_old = 0
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient

fileAppend = open("../funcs.txt", "a")

memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print("--- IMG RES ---", file=fileAppend)
print('memory use 1:', memoryUse-memoryUse_old, file=fileAppend)

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

images = {}
for indI in range(0, 20):
    blbName = "img" + str(indI) + ".png"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blbName)
    with open(blbName, "wb") as my_blob:
        download_stream = blob_client.download_blob()
        my_blob.write(download_stream.readall())
    images[blbName] = Image.open(blbName)

memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print('memory use 2:', memoryUse-memoryUse_old, file=fileAppend)

def main(params):
    blobName = "img20.png"
    if blobName not in images:
        blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
        with open(blobName, "wb") as my_blob:
            download_stream = blob_client.download_blob()
            my_blob.write(download_stream.readall())
        image = Image.open(blobName)
        images.append(image)
    else:
        image = images[blobName]
    width, height = image.size
    # Setting the points for cropped image
    left = 4
    top = height / 5
    right = 100
    bottom = 3 * height / 5
    im1 = image.crop((left, top, right, bottom))
    im1.save("newImage.png")

    fRead = open("newImage.png","rb")
    value = fRead.read()
    blobName = "img10_res.png"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)
    return {"Image":"rotated"}

main({"test":"func"})
memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**20  # memory use in MB
print('memory use 3:', memoryUse-memoryUse_old, file=fileAppend)