#!/usr/bin/python

#import all of the required modules 
import sys
import time
from neopixel import *
import Adafruit_MCP9808.MCP9808 as MCP9808
from tentacle_pi.TSL2561 import TSL2561
import csv
import RPi.GPIO as GPIO
sys.path.append("/home/pi/SHT31_PAE")
from SHT31 import *
import ConfigParser

#arguments will be in a separate .ini file (sys.argv[1]) which is read in and parsed to get different argument types

inputfile=str(sys.argv[1])
Config = ConfigParser.ConfigParser()
Config.read(inputfile)
brightness=Config.getint("settings", "brightness") #brightness for main lights on
R=Config.getint("settings", "R") #red spectrum for main lights on
G=Config.getint("settings", "G") #green spectrum for main lights on
B=Config.getint("settings", "B") #blue spectrum for main lights on
W=Config.getint("settings", "W") #white spectrum for main lights on
onTime=Config.getfloat("settings", "onTime") #time that lights will reach full intensity
offTime=Config.getfloat("settings", "offTime") #time that lights will stop being at full intensity
checkTime=Config.getfloat("settings", "checkTime") #frequency of checking time and recording data (usually 60 seconds)
outFile=Config.get("settings", "outfile_name") #name of output file that will save data log
Pulse=Config.getboolean("pulse", "Pulse") #True/false for whether a light pulse will be used
Pulse_on=Config.getfloat("pulse", "Pulse_on") #Time that pulse will start (in hours)
Pulse_off=Config.getfloat("pulse", "Pulse_off") #Time that pulse will end (in hours)
Pulse_R=Config.getint("pulse", "Pulse_R") #red spectrum for pulse
Pulse_G=Config.getint("pulse", "Pulse_G") #green spectrum for pulse
Pulse_B=Config.getint("pulse", "Pulse_B") #blue spectrum for pulse
Pulse_W=Config.getint("pulse", "Pulse_W") #white spectrum for pulse
Ramp_on=Config.getboolean("ramp_on", "Ramp_on") #true/false for whether a ramp will be used
ramp_ontime=Config.getfloat("ramp_on", "Ramp_ontime") #time that lights will start ramping on
Heat=Config.getboolean("heat", "Heat") #true false for whether the heater will be used
heatOn=Config.getfloat("heat", "heatOn") #time that heater should turn on
heatOff=Config.getfloat("heat", "heatOff") #time that heater should turn off 

#set up LED indicator light
GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.OUT)

#setup Heater
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)

#set up light moniter
tsl = TSL2561(0x39,"/dev/i2c-1")
tsl.enable_autogain()
tsl.set_time(0x00)

#specify LED configuration
LED_COUNT      = 24   # Number of LED pixels (always 24 in ring).
LED_PIN        = 18                 # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000             # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5                  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = brightness  # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False              # True to invert the signal (when using NPN transistor
LED_CHANNEL    = 0
LED_STRIP      = ws.SK6812_STRIP_RGBW	

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)

# Intialize the library (must be called once before other functions).
strip.begin()

#Turn on temperature sensor
sensor = MCP9808.MCP9808()
sensor.begin()

#make a datafile
c =(open(outFile, 'wb'))
wrtr = csv.writer(c)
wrtr.writerow(["TimeStamp", "MCP9808Temp", "SHT31Temp", "Humidity", "Lux", "Lights", "Time_in_hours", "R", "G", "B", "W"])

#start checking the time
while True:
    #what time is it?
    loopstart=time.time()
    now= time.localtime(time.time())
    timeStamp=time.strftime("%y-%m-%d %H:%M:%S", now)
    print timeStamp

    #apply calculation to time
    hour= float(time.strftime("%H "))
    minute= float(time.strftime("%M "))
    second=float(time.strftime("%S "))
    time_in_hours=hour+minute/60+second/3600
    print "time in hours is", time_in_hours

    #turn heat on if needed
    if Heat == True and heatOn <= time_in_hours <heatOff:
            GPIO.output(23, True)
    else:
        GPIO.output(23, False)

    #read sensors
    currtemp=sensor.readTempC()
    print "MCP9808 Temperature is", currtemp
    SHT31reading=read_SHT31()
    print "SHT31 Temperature is", SHT31reading[0]
    print "SHT31 Humidity is", SHT31reading[1]
    currlux=tsl.lux()
    print "Lux is", currlux

    #check for light pulse
    if Pulse == True and Pulse_on <= time_in_hours < Pulse_off:
        print "Pulsing"
        lights="Pulse"
        GPIO.output(16, True)
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(Pulse_G,Pulse_R,Pulse_B,Pulse_W))
            strip.show()
        currR=Pulse_R
        currG=Pulse_G
        currB=Pulse_B
        currW=Pulse_W
    #then check for ramping
    elif Ramp_on == True and ramp_ontime <= time_in_hours < onTime:
        print "Ramping"
        Ramp_time=onTime - ramp_ontime #total time that will be spent ramping
        fade=(time_in_hours-ramp_ontime)/Ramp_time #proportion of ramping that is completed
        lights="increasing"
        tempR=int(float(R)*fade) #calculate a red value based on proporition of ramping completed
        tempG=int(float(G)*fade) #calculate a green value based on proporition of ramping completed
        tempB=int(float(B)*fade) #calculate a blue value based on proporition of ramping completed
        tempW=int(float(W)*fade) #calculate a white value based on proporition of ramping completed
        for i in range(LED_COUNT):
            GPIO.output(16, True)
            strip.setPixelColor(i,Color(tempG,tempR,tempB,tempW))
            strip.show()
        currR=tempR
        currG=tempG
        currB=tempB
        currW=tempW
    #then check if lights are on main cycle     
    elif onTime <= time_in_hours < offTime:
        print ' Lights on!'
        lights="on"
        GPIO.output(16, True)
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(G,R,B,W))
            strip.show()
        currR=R
        currG=G
        currB=B
        currW=W
    #if none of the above conditions are true, lights should be off
    else:
        print 'Lights off!, LED off'
        GPIO.output(16,False)
        lights="Off"
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(0,0,0,0))
            strip.show()
        currR=0
        currG=0
        currB=0
        currW=0
    #write all the current data
    wrtr.writerow([timeStamp,currtemp, SHT31reading[0], SHT31reading[1], currlux, lights, time_in_hours, currR, currG, currB, currW])
    c.flush()
    # this will make it so that loop is initiated exactly ever 60 seconds by accounting for the elapsed time
    time.sleep(checkTime - ((time.time() - loopstart) % 60.0)) 
