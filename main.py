import pyrealsense2 as rs
import numpy as np
import argparse
import requests
import time
import json
import cv2
import os

# construct the argument parse 
parser = argparse.ArgumentParser(description='Script to run MobileNet-SSD object detection network')
parser.add_argument("--prototxt",
                    default="MobileNetSSD_deploy.prototxt",
                    help='Path to text network file: MobileNetSSD_deploy.prototxt for Caffe model'
                    )
parser.add_argument("--weights",
                    default="MobileNetSSD_deploy.caffemodel",
                    help='Path to weights: MobileNetSSD_deploy.caffemodel for Caffe model'
                    )
parser.add_argument("--thr",
                    default=0.7,
                    type=float,
                    help="confidence threshold to filter out weak detections"
                    )

# Labels of Network.
classNames = {
    0: 'background',
    1: 'aeroplane',
    2: 'bicycle',
    3: 'bird',
    4: 'boat',
    5: 'bottle',
    6: 'bus',
    7: 'car',
    8: 'cat',
    9: 'chair',
    10: 'cow',
    11: 'diningtable',
    12: 'dog',
    13: 'horse',
    14: 'motorbike',
    15: 'person',
    16: 'pottedplant',
    17: 'sheep',
    18: 'sofa',
    19: 'train',
    20: 'tvmonitor'
}

GeoAPI = 'https://www.googleapis.com/geolocation/v1/geolocate?key=[YOURAPIKEY]'
server_base = 'http://18.208.184.238:5050'
server_image = server_base + '/visions/save_img'
server_geo = server_base + '/locations/save_loc'
headers = {'content-type': 'image/jpeg'}

args = parser.parse_args()

# Load the Caffe model
net = cv2.dnn.readNetFromCaffe(args.prototxt, args.weights)

########################################################################################################################
# Create a pipeline
pipeline = rs.pipeline()

# Create a config and configure the pipeline to stream
#  different resolutions of color and depth streams
config = rs.config()
config.enable_stream(rs.stream.depth, 480, 270, rs.format.z16, 6)
config.enable_stream(rs.stream.color, 424, 240, rs.format.bgr8, 6)

# Start streaming
profile = pipeline.start(config)

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: ", depth_scale)

# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)

heightFactor = 240 / 300
widthFactor = 424 / 300
WindowWidth = 5
autoexpo = 0
loopcount = 0
report_freq = 15
try:
    while autoexpo < 6:
        # WARM UP... Capture 30 frames to give auto-exposure, etc. a chance to settle
        frames = pipeline.wait_for_frames()
        autoexpo += 1

    while True:
        loopcount += 1
        alertleft = {}
        alertmiddle = {}
        alertright = {}
        # Get frameset of color and depth
        frames = pipeline.wait_for_frames()

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        # Get aligned frames, aligned_depth_frame is a 640x480 depth image
        aligned_depth_frame = aligned_frames.get_depth_frame()
        aligned_color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not aligned_color_frame:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(aligned_color_frame.get_data())

        # resize color_image for prediction
        color_image_resized = cv2.resize(color_image, (300, 300))

        # Perform a mean subtraction (127.5, 127.5, 127.5) to normalize the input,
        blob = cv2.dnn.blobFromImage(color_image_resized, 0.007843, (300, 300), (127.5, 127.5, 127.5), False)
        # Set to network the input blob
        net.setInput(blob)
        # Prediction of network
        detections = net.forward()

        # Size of frame resize (W640xH480)
        cols = color_image_resized.shape[1]
        rows = color_image_resized.shape[0]

        # Get the class and location of object detected...
        # There are fixed indexes for class, location and confidence value in @detections MAT[].
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]  # Confidence of prediction
            if confidence > args.thr:  # Filter confidence
                class_id = int(detections[0, 0, i, 1])  # Class label

                # Object location
                left = int(detections[0, 0, i, 3] * cols * widthFactor)
                top = int(detections[0, 0, i, 4] * rows * heightFactor)
                right = int(detections[0, 0, i, 5] * cols * widthFactor)
                bottom = int(detections[0, 0, i, 6] * rows * heightFactor)

                # Draw location of object
                cv2.rectangle(color_image, (left, top), (right, bottom), (0, 255, 0), 2)

                # Get depth data for object detected, Mean(Depth) of central
                centerx = int((left + right) / 2)
                centery = int((top + bottom) / 2)
                window_left = centerx - WindowWidth if centerx - WindowWidth >= 0 else centerx
                window_right = centerx + WindowWidth if centerx + WindowWidth <= 424 else 424
                window_top = centery - WindowWidth if centery - WindowWidth >= 0 else centery
                window_bottom = centery + WindowWidth if centery + WindowWidth <= 240 else 240

                depth_window = depth_image[window_top:window_bottom, window_left:window_right]
                depth = np.nanmean(depth_window) * depth_scale

                # Draw label and confidence of prediction in frame resized
                if class_id in classNames:
                    obj_name = classNames[class_id]
                    label = obj_name + ": {0:.2f}m".format(depth)
                    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_TRIPLEX, 0.3, 1)

                    top = max(top, labelSize[1])
                    cv2.rectangle(
                        color_image,
                        (left, top - labelSize[1]),
                        (left + labelSize[0], top + baseLine),
                        (255, 255, 255), cv2.FILLED
                    )
                    cv2.putText(
                        color_image,
                        label,
                        (left, top),
                        cv2.FONT_HERSHEY_TRIPLEX,
                        0.3,
                        (0, 0, 0)
                    )
                    print(label)  # print class and confidence
                    if depth < 1.5:
                        if centerx < 141:
                            if obj_name in alertleft:
                                alertleft[obj_name] += 1
                            else:
                                alertleft[obj_name] = 1
                        elif centerx > 282:
                            if obj_name in alertright:
                                alertright[obj_name] += 1
                            else:
                                alertright[obj_name] = 1
                        else:
                            if obj_name in alertmiddle:
                                alertmiddle[obj_name] += 1
                            else:
                                alertmiddle[obj_name] = 1
                    else:
                        pass
                else:
                    pass
            else:
                pass

        # Start to speak
        alerts = ""
        if len(alertmiddle) > 0:
            alerts += "middle "
            for key in alertmiddle:
                alerts += "{0} {1} ".format(alertmiddle[key], key)
        if len(alertright) > 0:
            alerts += "right "
            for key in alertright:
                alerts += "{0} {1} ".format(alertright[key], key)
        if len(alertleft) > 0:
            alerts += "left "
            for key in alertleft:
                alerts += "{0} {1} ".format(alertleft[key], key)
        if len(alerts) > 0:
            print(alerts)
            os.system("espeak '{}'".format(alerts))
        #cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
        #cv2.imshow("frame", color_image)
        if loopcount > report_freq:
            print("Report...")
            loopcount = 0
            try:
                r_geo = requests.post(url=GeoAPI, json={}, headers={})
                coord = r_geo.json()
                print(coord)
                cv2.imwrite('1.jpg', color_image)
                img = open('1.jpg', 'rb').read()
                response = requests.post(url=server_geo, data=json.dumps(coord), headers={})
                response = requests.post(url=server_image, data=img, headers=headers)
            except:
                print("request error...")
                pass
finally:
    pipeline.stop()
