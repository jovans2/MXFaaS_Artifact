import time
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient

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

fileAppend = open("../funcs.txt", "a")

def main(params):
    t1 = time.time()
    blobName = "img20.png"
    if blobName not in images:
        blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
        with open(blobName, "wb") as my_blob:
            t3 = time.time()
            download_stream = blob_client.download_blob()
            t4 = time.time()
            my_blob.write(download_stream.readall())
        image = Image.open(blobName)
        images[blobName] = image
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
    blobName = "img10_res.jpg"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    t5 = time.time()
    blob_client.upload_blob(value, overwrite=True)
    t6 = time.time()
    t2 = time.time()
    print("--- IMG RES ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4-t3+t6-t5, file=fileAppend)
    return {"Image":"rotated"}

main({"test":"func"})