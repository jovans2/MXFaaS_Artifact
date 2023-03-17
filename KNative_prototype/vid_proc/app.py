import os
import cv2
from azure.storage.blob import BlobServiceClient, BlobClient
import dnld_blob

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

tmp = "/tmp/"

vid_name = 'vid1.mp4'

result_file_path = tmp + vid_name

def lambda_handler():
    blobName = "vid1.mp4"
    dnld_blob.download_blob_new(blobName)
    video = cv2.VideoCapture("vid1_"+str(os.getpid())+".mp4")

    width = int(video.get(3))
    height = int(video.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'MPEG')
    out = cv2.VideoWriter('output_'+str(os.getpid())+'.avi',fourcc, 20.0, (width, height))

    while video.isOpened():
        ret, frame = video.read()
        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            tmp_file_path = tmp+'tmp'+str(os.getpid())+'.jpg'
            cv2.imwrite(tmp_file_path, gray_frame)
            gray_frame = cv2.imread(tmp_file_path)
            out.write(gray_frame)
            break
        else:
            break

    fRead = open('output_'+str(os.getpid())+'.avi',"rb")
    value = fRead.read()
    blobName = "output.avi"
    dnld_blob.upload_blob_new(blobName, value)

    video.release()
    out.release()

    return {"Video": "Done"}