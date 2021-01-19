# LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1 python3
import cv2
import numpy
from adafruit_motorkit import MotorKit
from imutils.video import VideoStream
import time

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM) 

# configure two pins to send signals to itsy bitsy
data_one = 17
data_two = 27

GPIO.setup(data_one, GPIO.OUT)
GPIO.setup(data_two, GPIO.OUT)

# Gets a frame from stream and converts it to HSV
def get_frameHSV(stream):
    frame = stream.read()
    cv2.imshow('frame', frame)
    return  cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# Returns a mask designed to isolate pixels that represent the ball
def get_mask(frame):
    lower_green = numpy.array([40, 50, 50])
    upper_green = numpy.array([110, 200, 200])

    return cv2.inRange(frame, lower_green, upper_green)

# Gets info on the position of the ball
# - mask is an image with a color mask applied to it
# Returns a tuple containing
# - the average x position
# - the max x position
# - the average y position
# - the max y position
# - the ratio of masked to unmasked pixels
def get_frame_info(mask):
    height, width = mask.shape
    xsum = 0
    ysum = 0
    pixels = 0

    for x in range (0, width - 1):
        for y in range (0, height - 1):
            if (mask[y, x]):
                pixels = pixels + 1
                xsum = xsum + x
                ysum = ysum + y

    # print(width, ' ', xsum / pixels)
    # print(height, ' ', ysum / pixels)
    # print(pixels / (height * width) * 100, ' ')

    if (pixels == 0):
        return 0, 0 ,0, 0, 0
    
    return xsum / pixels, width, ysum / pixels, height, pixels / (height * width) * 100


# updates the motor's throttles, taking into account the reversed wiring for motor2
# for example, if you would usually reverse motor2's throttle value to account for
# the backwards wiring, don't
def update_motors(car, left_motor, right_motor):
    car.motor1.throttle = left_motor
    car.motor2.throttle = 1.1 * -1 * right_motor

# Executes one itteration of the follow alogorithm
# Is meant to be called continuously
#  - car is the object the motor throttle values are changed through
# - stream is the video stream
# - center_tolerence is a value from 0 to 1 that defines how big the center is as a percentage
#   of the width of the image. It's used to center Sven on the ball before he moves
#   towards it
# - target_ratio is the percent of pixels that are filled by the ball when Sven is close
#   enough to stop
def follow(car, stream, center_tolerence, ideal_ratio):
    # try:
    avg_x, max_x, avg_y, max_y, ratio = get_frame_info(get_mask(get_frameHSV(stream)))
    #     print("No Error")
    # except:
    #     print("Error")
    #     return

    print(avg_x, ' ', max_x, ' ', ratio)

    if (ratio < 1) :
        update_motors(car, 0, 0) # point turn left
        GPIO.output(data_one, 1)
        GPIO.output(data_two, 0)
        print("Nowhere to be found 10")
    elif (avg_x < (max_x / 2) - max_x * (center_tolerence / 2)): # if the ball is left of center
        update_motors(car, 0.3, -0.3) # point turn left
        GPIO.output(data_one, 0)
        GPIO.output(data_two, 1)
        print("Left 01")
    elif (avg_x > (max_x / 2) + max_x * (center_tolerence / 2)): # if the ball is right of center
        update_motors(car, -0.3, 0.3) # point turn right
        GPIO.output(data_one, 0)
        GPIO.output(data_two, 1)
        print("Right 01")
    elif (ratio < ideal_ratio): # if ball is within 'center_tolerence' distanve of center but still too far away
        update_motors(car, 0.5, 0.5) # move straight\
        GPIO.output(data_one, 0)
        GPIO.output(data_two, 1)
        print("Straight 01")
    else: # if ball is within 'center_tolerence' distanve of center and close
        update_motors(car, 0, 0) # stop
        GPIO.output(data_one, 1)
        GPIO.output(data_two, 1)
        print("Stop 11")

usingPiCamera = True
# Set initial frame size
frameSize = (320, 240)

car = MotorKit()
VS = VideoStream(src=0, usePiCamera=usingPiCamera, resolution=frameSize,framerate=32).start()
time.sleep(2.0)

while(1):
    try:
        follow(car, VS, 0.3, 20)
        # print(VS.read())
        time.sleep(1.0)
        
    except KeyboardInterrupt:
        car.motor1.throttle = 0
        car.motor2.throttle = 0
        print("Finished")
        VS.stop()
        quit()
