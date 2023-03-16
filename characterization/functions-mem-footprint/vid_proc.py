import psutil
import os
pid = os.getpid()
python_process = psutil.Process(pid)
memoryUse_old = 0
import cv2
from azure.storage.blob import BlobServiceClient, BlobClient

fileAppend = open("../funcs.txt", "a")

memoryUse = python_process.memory_info()[0]/2.**30  # memory use in GB
print("--- VID PROC ---", file=fileAppend)
print('memory use 1:', memoryUse-memoryUse_old, file=fileAppend)

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

tmp = "/tmp/"

vid_name = 'vid1.mp4'

blobName = "vid1.mp4"
blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
with open(vid_name, "wb") as my_blob:
    download_stream = blob_client.download_blob()
    my_blob.write(download_stream.readall())

result_file_path = tmp + vid_name

memoryUse_old = memoryUse
memoryUse = python_process.memory_info()[0]/2.**30  # memory use in GB
print('memory use 2:', memoryUse-memoryUse_old, file=fileAppend)

def video_processing():

    video = cv2.VideoCapture(vid_name)

    width = int(video.get(3))
    height = int(video.get(4))
    fourcc = cv2.VideoWriter_fourcc(*'MPEG')
    out = cv2.VideoWriter('output.avi',fourcc, 20.0, (width, height))

    while video.isOpened():
        ret, frame = video.read()
        if ret:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            tmp_file_path = tmp+'tmp.jpg'
            cv2.imwrite(tmp_file_path, gray_frame)
            gray_frame = cv2.imread(tmp_file_path)
            out.write(gray_frame)
            break
        else:
            break

    fRead = open("output.avi","rb")
    value = fRead.read()
    blobName = "output.avi"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    blob_client.upload_blob(value, overwrite=True)

    video.release()
    out.release()
    return

def serve():
    video_processing()

if __name__ == '__main__':
    serve()
    memoryUse_old = memoryUse
    memoryUse = python_process.memory_info()[0]/2.**30  # memory use in GB
    print('memory use 3:', memoryUse-memoryUse_old, file=fileAppend)