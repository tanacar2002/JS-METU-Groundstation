import sys
import os
import json
import time
import numpy as np
import base64
import cv2
import multiprocessing as mp

VIDEO_FPS = 10
def camThread(conn):
    while True:
        parsed_stream_data = conn.recv()
        command = parsed_stream_data['command']
        if command == "OPEN_CAMERA":
            camId = parsed_stream_data['camID']
            break
        elif command == 'KILL':
            conn.send(0)
            return

    #Connect to camera
    cap = cv2.VideoCapture(camId, cv2.CAP_DSHOW)
    #Recorder for the live video feed
    recorder = cv2.VideoWriter("Data/LiveVideo.mp4", cv2.VideoWriter_fourcc(*"mp4v"),
                               VIDEO_FPS, (int(cap.get(3)), int(cap.get(4))))
    if cap.isOpened():
        t = 0
        while True:
            while time.time()-t < (1.0/VIDEO_FPS):
                pass
            t = time.time()
            if conn.poll():
                parsed_stream_data = conn.recv()
                command = parsed_stream_data['command']

                # ---------------------------- Camera openning block ------------------------------
                if command == "OPEN_CAMERA":
                    camId = parsed_stream_data['camID']
                    cap.release()
                    cap = cv2.VideoCapture(camId, cv2.CAP_DSHOW)

                # -------------------------- Script termination block ----------------------------
                elif command == 'KILL':
                    #Save the video properly
                    cap.release()
                    recorder.release()
                    conn.send(0)
                    break
                
            #Get the next video frame from OTG Reciever
            suc, frame = cap.read()
            if suc:
                recorder.write(frame)
                output = {
                    'type': 'FRAME_DATA',
                    'dimentions': frame.shape,
                    'result': str(base64.b64encode(frame[:, :, ::-1].flatten())) # Type ndarray is not JSON Serializable
                }
                print(json.dumps(output))
                sys.stdout.flush()

def main():
    index = 0
    cam_array = []
    while True:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.read()[0]:
            break
        else:
            cam_array.append(index)
        cap.release()
        index += 1

    output = {
        'type': 'CAMERA_DATA',
        'result': {"devices":cam_array}
    }
    print(json.dumps(output))
    sys.stdout.flush()

    camPipe, camProcessPipe = mp.Pipe()
    x = mp.Process(target=camThread, args=(camProcessPipe,), daemon=True)
    x.start()

    while(True):
        in_stream_data = input()
        parsed_stream_data = json.loads(in_stream_data)
        camPipe.send(parsed_stream_data)

        # -------------------------- Script termination block ----------------------------
        if camPipe.poll():
            res = camPipe.recv()
            break

    x.join(timeout=10)


if __name__ == '__main__':
    main()
