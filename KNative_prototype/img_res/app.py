import os
from PIL import Image
from azure.storage.blob import BlobServiceClient, BlobClient
import dnld_blob

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

def lambda_handler():
    blobName = "img10.jpg"
    dnld_blob.download_blob_new(blobName)
    full_blob_name = blobName.split(".")
    proc_blob_name = full_blob_name[0] + "_" + str(os.getpid()) + "." + full_blob_name[1]
    
    image = Image.open(proc_blob_name)
    width, height = image.size
    # Setting the points for cropped image
    left = 4
    top = height / 5
    right = 100
    bottom = 3 * height / 5
    im1 = image.crop((left, top, right, bottom))
    im1.save('tempImage_'+str(os.getpid())+'.jpeg')

    fReadname = 'tempImage_'+str(os.getpid())+'.jpeg'
    blobName = "img10_res.jpg"
    dnld_blob.upload_blob_new(blobName, fReadname)

    return {"Image":"resized"}