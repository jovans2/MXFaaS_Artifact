import time
import cv2
from azure.storage.blob import BlobServiceClient, BlobClient
import dnld_blob

connection_string = "DefaultEndpointsProtocol=https;AccountName=serverlesscache;AccountKey=O7MZkxwjyBWTcPL4fDoHi6n8GsYECQYiMe+KLOIPLpzs9BoMONPg2thf1wM1pxlVxuICJvqL4hWb+AStIKVWow==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("artifacteval")

tmp = "/tmp/"

vid_name = 'vid1.mp4'

result_file_path = tmp + vid_name

fileAppend = open("../funcs.txt", "a")

def lambda_handler():
    t1 = time.time()
    blobName = "vid1.mp4"
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    with open(vid_name, "wb") as my_blob:
        t3 = time.time()
        download_stream = dnld_blob.download_blob_new(blob_client)
        t4 = time.time()
        my_blob.write(download_stream.readall())
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
    t5 = time.time()
    blob_client = BlobClient.from_connection_string(connection_string, container_name="artifacteval", blob_name=blobName)
    dnld_blob.upload_blob_new(blob_client, value)
    t6 = time.time()

    video.release()
    out.release()
    t2 = time.time()
    print("--- VID PROC ---", file=fileAppend)
    print("Handler time = ", t2-t1, file=fileAppend)
    print("Idle time = ", t4-t3+t6-t5, file=fileAppend)
    return {"Video": "Done"}