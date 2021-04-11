import sys
import os
import json
import csv
from datetime import datetime
import struct
import serial
import serial.tools.list_ports
import multiprocessing as mp

#Common constants for communication
telemetrystruct = "<HHBBHBBBHHhHBffhBbbbBB"
VIDEO_BUFFER_SIZE = 250        # Limited by the AltSerialLib RX_BUFFER_SIZE
TELEMETRY_DATA_BYTE = bytes([0b10010011])
ACTIVATE_VIDEO_TRANSMISSION_CMD = bytes([0b11000000])
DEACTIVATE_VIDEO_TRANSMISSON_CMD = bytes([0b10000010])
ACTIVATE_EJECTION_CMD = bytes([0b10000100])
ACTIVATE_RESET_CMD = bytes([0b10001000])
# To ACK Ground Station (State Change @ GS)
VIDEO_TRANSMISSION_CMPLTD = bytes([0b10100000])


def getvideobytes(path):
    vbytes = []
    with open(path, 'rb') as f:
        b = f.read(1)
        while b:
            vbytes.append(b)
            b = f.read(1)
        #print("Size of the video file is %d bytes" % len(vbytes))
    return vbytes

def serialThread(conn):
    telemetry = {"teamNumber": 0, "packageCounter": 0, "day": 0, "month": 0, "year": 0, "hour": 0,
                 "minute": 0, "second": 0, "pressure": 0, "altitude": 0, "speed": 0, "temperature": 0,
                 "batteryVoltage": 0, "GPS_Latitude": 0, "GPS_Longitude": 0, "GPS_Altitude": 0,
                 "status": 0, "pitch": 0, "roll": 0, "yaw": 0, "revolution": 0, "videoTransmission": 0}
    cmd_send = []
    if not os.path.exists('Data'):
        os.makedirs("Data")
    now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    datapath = 'Data/Tele_' + now + '.csv'
    videopath = 'Data/SampleVideo_1280x720_1mb.mp4'
    videosendstate = False
    videobytes = getvideobytes(videopath)
    video_send_counter = 0
    #Open a .csv file to record telemetry data
    f = open(datapath, 'w+', newline='')
    writer = csv.DictWriter(f, fieldnames=[key for key in telemetry])
    writer.writeheader()

    #Create Serial Port
    serialPort = serial.Serial(
        bytesize=8, timeout=2, write_timeout=0, stopbits=serial.STOPBITS_ONE)
    while True:
        if conn.poll():
            parsed_stream_data = conn.recv()
            command = parsed_stream_data['command']

            # ---------------------------- Port openning block ------------------------------
            if command == 'OPEN_PORT':
                port, baudrate = parsed_stream_data['port_name'], parsed_stream_data['baudrate']
                if port == "":
                    break
                if serialPort.is_open:
                    serialPort.close()
                serialPort.baudrate=baudrate
                serialPort.port=port
                serialPort.open()
                while not serialPort.is_open:
                    pass
                serialPort.flushInput()  # Clear Rx Buffer

            # --------------------------- Video selecting block ------------------------------
            elif command == "SELECT_VIDEO":
                pathinput = parsed_stream_data['path']
                if pathinput != "":
                    videobytes = getvideobytes(pathinput)
                    video_send_counter = 0

            # --------------------------- Sending commands block -----------------------------
            elif command == "EJECT":
                cmd_send.append(ACTIVATE_EJECTION_CMD)

            elif command == "START_VIDEO_SEND":
                videosendstate = True
                #cmd_send.append(ACTIVATE_VIDEO_TRANSMISSION_CMD)
                if serialPort.is_open:
                    serialPort.write(ACTIVATE_VIDEO_TRANSMISSION_CMD)

            elif command == "STOP_VIDEO_SEND":
                videosendstate = False
                cmd_send.append(DEACTIVATE_VIDEO_TRANSMISSON_CMD)

            elif command == "RESET_VIDEO_SEND":
                #Reset the video_send counter to start sending from beginning of the video file
                video_send_counter = 0

            elif command == "MOTOR_TEST":
                # cmd_send.append(_command_)
                pass

            elif command == "RESET_SATELLITE":
                cmd_send.append(ACTIVATE_RESET_CMD)
                resetSat = True
                #Close the csv file and open a new one
                f.close()
                f = open(datapath, 'w+', newline='')
                writer = csv.DictWriter(f, fieldnames=[key for key in telemetry])
                writer.writeheader()

            # -------------------------- Script termination block ----------------------------
            elif command == 'KILL':
                break
        
        # -------------------------------- Serial handling block -----------------------------
        if serialPort.is_open:
            if serialPort.in_waiting > 0:
                data = serialPort.read()
                if data == TELEMETRY_DATA_BYTE:
                    data_buffer = struct.unpack(
                        telemetrystruct, serialPort.read(36))
                    #Cast the data buffered into the dict
                    for i, key in enumerate(telemetry):
                        telemetry[key] = data_buffer[i]
                    #Re-scale some data
                    telemetry["temperature"] /= 10.0
                    telemetry["batteryVoltage"] /= 10.0
                    #Save new data into the .csv file
                    writer.writerow(telemetry)
                    output = {
                        'type': 'TELEMETRY_DATA',
                        'result': telemetry
                    }
                    print(json.dumps(output))
                    sys.stdout.flush()
                elif (data == ACTIVATE_VIDEO_TRANSMISSION_CMD) and (len(videobytes) > video_send_counter):
                    #We recieved request for one packet of videobytes
                    #Calculate the Checksum Byte to send
                    chk = ((~sum([ord(b) for b in videobytes[video_send_counter:(
                        video_send_counter+VIDEO_BUFFER_SIZE)]]))+1) & 0xff
                    #print("Checksum is {}".format(chk))
                    if cmd_send:
                        cmd = cmd_send.pop(0)
                        if cmd == DEACTIVATE_VIDEO_TRANSMISSON_CMD:
                            videosendstate = False
                        #print("Sent the {} command".format(cmd))
                    else:
                        cmd = bytes([0])
                    serialPort.write(b''.join([cmd]+[bytes([0 if ((video_send_counter+VIDEO_BUFFER_SIZE) < len(videobytes)) else (len(
                        videobytes)-video_send_counter)])] + videobytes[video_send_counter:(video_send_counter+VIDEO_BUFFER_SIZE)]+[bytes([chk])]))
                    serialPort.flush()
                    if (video_send_counter+VIDEO_BUFFER_SIZE) < len(videobytes):
                        videosendstate = False
                    ## TODO: Test and optimize the video sending process
                    #print("Sent {} bytes of video data.".format(VIDEO_BUFFER_SIZE))
                elif data == VIDEO_TRANSMISSION_CMPLTD:
                    #We successfully transmitted the data, increase the counter
                    video_send_counter += VIDEO_BUFFER_SIZE
                    #print("Video send counter incremented.")
                elif data == DEACTIVATE_VIDEO_TRANSMISSON_CMD:
                    #We couldn't successfully transmitt the data, don't increase the counter
                    pass

        #If not transmitting video file, send the buffered commands
        if (not videosendstate) and serialPort.is_open:
            for cmd in cmd_send:
                serialPort.write(cmd)
                #print("Sent the {} command".format(cmd))
            cmd_send = []
    #Clean up
    f.close()
    serialPort.close()
    conn.send(0)

def main():
    serPipe, serProcessPipe = mp.Pipe()
    x = mp.Process(target=serialThread, args=(serProcessPipe,), daemon=True)
    x.start()

    while(True):
        in_stream_data = input()
        parsed_stream_data = json.loads(in_stream_data)
        serPipe.send(parsed_stream_data)

        # -------------------------- Script termination block ----------------------------
        if serPipe.poll():
            res = serPipe.recv()
            break

    x.join(timeout=10)


if __name__ == '__main__':
    main()
