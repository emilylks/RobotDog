from adafruit_motorkit import MotorKit
import RPi.GPIO as GPIO
import socket
from time import sleep
car = MotorKit()

GPIO.setmode(GPIO.BCM)  # check the mode and pin numbers
sensorW = 6
sensorY = 12
sensorG = 13
sensorB = 16

GPIO.setup(sensorW, GPIO.IN)
GPIO.setup(sensorY, GPIO.IN)
GPIO.setup(sensorG, GPIO.IN)
GPIO.setup(sensorB, GPIO.IN)

SENSORS = [0, 0, 0, 0]
KP = 0.125  # 1/8
KD = 0.062 #0.083  # half the value of KD
PREV1 = 0.0
PREV2 = 0.0

#UDP_IP = "137.82.226.215" this is the IP for the controller pi
#UDP_IP = "0.0.0.0"
#UDPPORT = 5005

#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.bind((UDP_IP, UDP_PORT))
#cmd, addr = sock.recvfrom(1024)  # Define input from controller

def updateSensors():
	SENSORS[0] = GPIO.input(sensorY) # leftmost
	SENSORS[1] = GPIO.input(sensorG)
	SENSORS[2] = GPIO.input(sensorW)
	SENSORS[3] = GPIO.input(sensorB)  # rightmost

def updateMotors(m1, m2, y, g, w, b):  # right m1 and left m2
	# range of m1: 0 to 1
	# range of m2: -1 to 0	
	global PREV1
	global PREV2
	a = 0	
	m1_error = m1 - PREV1
	m2_error = m2 - PREV2
	m1_prev_error = 0.0
	m2_prev_error = 0.0
	sp1 = PREV1
	sp2 = PREV2	
	for j in range (0, 8):  # steady change on speed of wheels
		sp1 += (m1_error * KP) + (m1_prev_error * KD)
		sp2 += (m2_error * KP) + (m2_prev_error * KD)

		if (sp1 >= 0.8):
			sp1 = 0.8
		if (sp2 <= -0.8):
			sp2 = -0.8

		# if switch is ON, move the wheels
		car.motor1.throttle = sp1
		car.motor2.throttle = sp2
		print("SP1 {} SP2 {}".format(sp1, sp2))

		m1_prev_error = m1_error
		m2_prev_error = m2_error	
		updateSensors()  # detect the change of sensor values
		if (SENSORS[0] != y) or (SENSORS[1] != g) or (SENSORS[2] != w) or (SENSORS[3] != b): 
			a = a + 1
		if a == 2:   # if sensors keep changing the values, break
			break
	PREV1 = sp1
	PREV2 = sp2

# treat motor1 and RIGHT motor, motor2 as LEFT motor
def lineSensors():
	try:
		while True:
			updateSensors()
			LL = SENSORS[0] # very left
			LM = SENSORS[1]# left middle
			RM = SENSORS[2] # right middle
			RR = SENSORS[3]  # very right

			print("Sensor Yellow: ", LL)
			print("Sensor Green ", LM)
			print("Sensor White: ", RM)
			print("Sensor Blue: ", RR)

			if (not LL) and (not RR) and RM and LM: # stay on track
				updateMotors(0.5, -0.5, 0, 1, 1, 0)
			elif (not LL) and (not RR) and RM and (not LM): # stay on track
				updateMotors(0.5, -0.5, 0, 0, 1, 0)
			elif (not LL) and (not RR) and LM and (not RM): # stay on track
				updateMotors(0.5, -0.5, 0, 1, 0, 0)
			elif (not LL) and (not LM) and RM and RR: # turn right
				updateMotors(0.2, -0.6, 0, 0, 1, 1)
			elif (not LL) and LM and RM and RR: # slight turn right
				updateMotors(0.3, -0.5, 0, 1, 1, 1)
			elif (not LL) and (not LM) and (not RM) and RR: # sharp turn right
				updateMotors(0.15, -0.75, 0, 0, 0, 1)

			elif (not RM) and (not RR) and LL and LM: # turn left
				updateMotors(0.6, -0.2, 1, 1, 0, 0)
			elif RM and (not RR) and LL and LM: # slight turn left
				updateMotors(0.5, -0.3, 1, 1, 1, 0)
			elif (not RR) and LL and LM and RM: # sharp turn left
				updateMotors(0.75, -0.15, 1, 0, 0, 0)

			elif LL and LM and RM and RR: # crossroad
				updateMotors(0.5, -0.5, 1, 1, 1, 1)
			elif (not LL) and (not RR) and (not RM) and (not LM): # gap/end of track
				stop = 1
				for i in range(0, 7):
					sleep(0.3)
					updateSensors()
					if (SENSORS[0] or SENSORS[1] or SENSORS[2] or SENSORS[3]):
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

# Loop that selects function to run based on input from controller
#while True:
#	if 'treat' in str(cmd):
lineSensors()
#	else:
