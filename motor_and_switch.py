from adafruit_motorkit import MotorKit
import RPi.GPIO as GPIO
import socket
from time import sleep
from imutils.video import VideoStream
import follow

car = MotorKit()
vs = VideoStream(src=0, usePiCamera=True, resolution=(320, 240), framerate=32).start()

sleep(2.0)

GPIO.setmode(GPIO.BCM)  # check the mode and pin numbers
sensorW = 6
sensorY = 12
sensorG = 13
sensorB = 16

GPIO.setup(sensorW, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sensorY, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sensorG, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sensorB, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# configure two pins to send signals to itsy bitsy
data_one = 17
data_two = 27

GPIO.setup(data_one, GPIO.OUT)
GPIO.setup(data_two, GPIO.OUT)

# Store prev cmd
PREV_CMD = ""

# set both pins to zero to signal no tail movement
GPIO.output(data_one, 0)
GPIO.output(data_two, 0)

sensors = [0, 0, 0, 0]
KP = 0.125 #0.167  # 1/6
KD = 0.062 #0.083  # half the value of KD
PREV1 = 0
PREV2 = 0

#UDP_IP = "137.82.226.215" this is the IP for the controller pi
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((UDP_IP, UDP_PORT))
#cmd, addr = sock.recvfrom(1024)  # Define input from controller

# set time for timeout on socket
sock.settimeout(0.5)

def updateSensors():
    sensors[0] = GPIO.input(sensorY) # leftmost
    sensors[1] = GPIO.input(sensorG)
    sensors[2] = GPIO.input(sensorW)
    sensors[3] = GPIO.input(sensorB)  # rightmost

def updateMotors(m1, m2, y, g, w, b):  # right m1 and left m2
    # range of m1: 0 to 1
    # range of m2: -1 to 0
    # check the switch
    # if not 'walk' in check_cmd(PREV_CMD):
    #   #print("uh oh")
    #   return
    global PREV1
    global PREV2
    a = 0
    m1_error = m1 - PREV1
    m2_error = m2 - PREV2
    m1_prev_error = 0
    m2_prev_error = 0
    sp1 = PREV1
    sp2 = PREV2
    for i in range (0, 8):  # steady change on speed of wheels
        sp1 += (m1_error * KP) + (m1_prev_error * KD)
        sp2 += (m2_error * KP) + (m2_prev_error * KD)
        # before moving motors, check the switch
        if not 'walk' in str(check_cmd()):
            print("uh oh")
            return
        
        if (sp1 >= 0.8)
            sp1 = 0.8
        if (sp2 <= -0.8)
            sp2 = -0.8

        # if switch is ON, move the wheels
        if (sp1 > 0.7):
            sp1 = 0.7
        if (sp2 < -0.7):
            sp2 = -0.7
        car.motor1.throttle = sp1
        car.motor2.throttle = sp2
        print("SP1 {} SP2 {}".format(sp1, sp2))
        m1_prev_error = m1_error
        m2_prev_error = m2_error
        updateSensors()  # detect the change of sensor values
        if (sensors[0] != y) or (sensors[1] != g) or (sensors[2] != w) or (sensors[3] != b):
            a = a + 1
        if a == 2:   # if sensors keep changing the values, break
            break
    PREV1 = sp1
    PREV2 = sp2

def check_cmd():
    global PREV_CMD
    #cmd = sock.recv(1024)
    while True:
        try:
            cmd = sock.recv(1024)
            print("After socket")

        except socket.timeout:
            print("aghghg")
            return PREV_CMD

        PREV_CMD = cmd
        return str(cmd)

def choose_fcn():
    global PREV_CMD
    car.motor1.throttle = 0
    car.motor2.throttle = 0
    # Line following
    cmd = check_cmd()
    print(cmd)
    print('prev cmd' + str(PREV_CMD))
    if ('walk' in str(cmd)):
        # set both pins to zero to signal no tail movement
        print('walk' + "in if")
        #GPIO.output(data_one, 0)
        #GPIO.output(data_two, 0)
        lineSensors()
        return
    # Ball following
    elif ('follow' in str(cmd)):
        print('follow')
        follow.follow(car, vs, 0.3, 20)
        return
    else:
        print(str(cmd) + "in else")
        # set both pins to zero to signal no tail movement
        GPIO.output(data_one, 0)
        GPIO.output(data_two, 0)
        # stop the motors
        car.motor1.throttle = 0
        car.motor2.throttle = 0
        return

# treat motor1 and RIGHT motor, motor2 as LEFT motor
def lineSensors():
    try:
        while True:
            updateSensors()
            LL = sensors[0] # very left
            LM = sensors[1]# left middle
            RM = sensors[2] # right middle
            RR = sensors[3]  # very right

            print("Sensor Yellow: ", LL)
            print("Sensor Green ", LM)
            print("Sensor White: ", RM)
            print("Sensor Blue: ", RR)

            if (not LL) and (not RR) and RM and LM: # stay on track
                updateMotors(0.2, -0.2, 0, 1, 1, 0)
            elif (not LL) and (not RR) and RM and (not LM): # stay on track
                updateMotors(0.2, -0.2, 0, 0, 1, 0)
            elif (not LL) and (not RR) and LM and (not RM): # stay on track
                updateMotors(0.2, -0.2, 0, 1, 0, 0)
            elif (not LL) and (not LM) and RM and RR: # turn right
                updateMotors(0.15, -0.35, 0, 0, 1, 1)
            elif (not LL) and LM and RM and RR: # slight turn right
                updateMotors(0.15, -0.3, 0, 1, 1, 1)
            elif (not LL) and (not LM) and (not RM) and RR: # sharp turn right
                updateMotors(0.1, -0.5, 0, 0, 0, 1)

            elif (not RM) and (not RR) and LL and LM: # turn left
                updateMotors(0.35, -0.15, 1, 1, 0, 0)
            elif RM and (not RR) and LL and LM: # slight turn left
                updateMotors(0.3, -0.15, 1, 1, 1, 0)
            elif (not RR) and LL and LM and RM: # sharp turn left
                updateMotors(0.5, -0.1, 1, 0, 0, 0)

            elif LL and LM and RM and RR: # crossroad
                updateMotors(0.15, -0.15, 1, 1, 1, 1)
            elif (not LL) and (not RR) and (not RM) and (not LM): # gap/end of track
                stop = 1
                for i in range(0, 7):
                    sleep(0.3)
                    updateSensors()
                    if (sensors[0] or sensors[1] or sensors[2] or sensors[3]):
                        stop = 0
                        break
                if stop == 1:
                    car.motor1.throttle = 0
                    car.motor2.throttle = 0
                    break
    except KeyboardInterrupt:
        car.motor1.throttle = 0
        car.motor2.throttle = 0
        GPIO.cleanup()
        vs.stop()



# Loop that selects function to run based on input from controller
while True:
    #PREV_CMD = ""
    choose_fcn()
