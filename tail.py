# Import libraries
import board
import servo
import time
import pulseio

import displayio
import terminalio
import adafruit_imageload
from adafruit_display_text import label
from adafruit_st7735r import ST7735R

# For receiving data from raspberry pi
from digitalio import DigitalInOut, Direction, Pull

data_one = DigitalInOut(board.D9)
data_two = DigitalInOut(board.D13)

switch.direction = Direction.INPUT
switch.pull = Pull.UP

# Servo motors configuration
servo_tailL = pulseio.PWMOut(board.D12, duty_cycle=2**15, frequency=50) # blue
servo_tailM = pulseio.PWMOut(board.D11, duty_cycle=2**15, frequency=50) # green
servo_tailH = pulseio.PWMOut(board.D10, duty_cycle=2**15, frequency=50) # yellow
# servo_head = pulseio.PWMOut(board.D9, duty_cycle=2**15, frequency=50) # orange

tailL = servo.Servo(servo_tailL)
tailM = servo.Servo(servo_tailM)
tailH = servo.Servo(servo_tailH)
# head = servo.Servo(servo_head)

# Release any resources currently in use for the displays
displayio.release_displays()
spi = board.SPI()
tft_cs = board.D3
tft_dc = board.D4
rst = board.D7

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=rst)
display = ST7735R(display_bus, width=128, height=128, colstart=2, rowstart=1, rotation=270)

index = 0

def display_here(text, color, x_coor, im_x, im_y, file):
    # Make the display context
    splash = displayio.Group(max_size=10)
    display.show(splash)

    # Choose the color of the screen background
    color_bitmap1 = displayio.Bitmap(128, 40, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = color

    bg_sprite1 = displayio.TileGrid(color_bitmap1, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite1)

    # Draw label
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=x_coor, y= 20)
    splash.append(text_area)

    # Generate the Bitmap and Palette from the image
    my_bitmap, my_palette = adafruit_imageload.load(file, bitmap=displayio.Bitmap, palette=displayio.Palette)
    my_tilegrid = displayio.TileGrid(my_bitmap, pixel_shader=my_palette, x = im_x, y = im_y)
    splash.append(my_tilegrid)

# Reset all servos to default state
def default():
    tailL.angle = 0
    tailM.angle = 90
    tailH.angle = 90
    head.angle = 90

def relaxed():
    for i in range(90, 20, -5):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.04)
    for i in range(20, 90, 5):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.04)
    for i in range(90, 160, 5):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.04)
    for i in range(160, 90, -5):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.04)

def neutral():
    default()
    for i in range(0, 3, 1):
        relaxed()
        time.sleep(0.02)

def cute_1():
    for i in range(0, 40, 5):
        tailL.angle = i
        time.sleep(0.01)
    for i in range(40, 0, -5):
        tailL.angle = i
        time.sleep(0.01)

def cute_2():
    for i in range(90, 30, -10):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.02)
    for i in range(30, 90, 10):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.02)
    for i in range(90, 120, 10):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.02)
    for i in range(120, 90, -10):
        tailM.angle = i
        tailH.angle = i
        time.sleep(0.02)

def cute():
    default()
    for i in range(1, 3, 1):
        cute_1()
        time.sleep(0.02)
    for i in range(1, 3, 1):
        cute_2()
        time.sleep(0.02)
    for i in range(1, 3, 1):
        cute_1()
        time.sleep(0.02)
    for i in range(1, 3, 1):
        cute_2()
        time.sleep(0.02)
        
def excited_move():
    for i in range(0, 100, 10):
        tailH.angle = i
        time.sleep(0.02)
    for i in range(100, 0, -10):
        tailH.angle = i
        time.sleep(0.02)

def excited():
    default()
    for i in range(90, 0, -30):
        tailH.angle = i
        time.sleep(0.02)
    for i in range(0, 90, 15):
        tailL.angle = i
        time.sleep(0.02)
    for i in range(90, 180, 10):
        tailM.angle = i
        time.sleep(0.02)
    for i in range(0, 10, 1):
        excited_move()
        time.sleep(0.02)

def concerned():
    for i in range(60, 20, -1):
        tailM.angle = i
        tailH.angle = i+120
        time.sleep(0.01)
    for i in range(20, 60, 1):
        tailM.angle = i
        tailH.angle = i+120
        time.sleep(0.01)

def unpleasant():
    default()
    for i in range(90, 180, 30):
        tailH.angle = i
        time.sleep(0.02)
    for i in range(0, 90, 15):
        tailL.angle = i
        time.sleep(0.02)
    for i in range(90, 60, -10):
        tailM.angle = i
        time.sleep(0.02)
    for i in range(0, 3, 1):   
        concerned()

def dance():
    default()
    for i in range(0, 80, 10):
        tailL.angle = i
        tailM.angle = i+90
        time.sleep(0.02)
    for i in range(80, 160, 5):
        tailL.angle = i
        tailM.angle = 250-i
        time.sleep(0.02)
    for i in range(160, 80, -10):
        tailL.angle = i
        tailM.angle = 250-i
        time.sleep(0.02)
    for i in range(80, 0, -5):
        tailL.angle = i
        tailM.angle = i+90
        time.sleep(0.02)
    cute_1()
    cute_1()
    for i in range(90, 180, 10):
        tailH.angle = i
        time.sleep(0.02)
    for i in range(0, 90, 5):
        tailL.angle = i
        time.sleep(0.02)
    for i in range(90, 60, -10):
        tailM.angle = i
        time.sleep(0.02)

    
def tail(index):
    if (index % 3 == 0):
        display_here("Just Relaxing...", 0x006400, 20, 0 , 40, "/mono.bmp")
        time.sleep(3)
        neutral()
    elif(index % 3 == 1):
        display_here("Am I Cute?", 0xFF4500, 30, 0, 40, "/cute.bmp")
        time.sleep(3)
        cute()
    elif(index % 3 == 2):
        display_here("Hey There!", 0x4B0082, 30, 2, 40, "/happy.bmp")
        time.sleep(3)
        excited()
    else: # not data_one and not data_two
        time.sleep(3)
        
while (True):
    tail(index)
    index = index + 1
