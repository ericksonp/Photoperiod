#!/usr/bin/python

#import all of the required modules 
import sys
import time
from neopixel import *
import Adafruit_MCP9808.MCP9808 as MCP9808
from tentacle_pi.TSL2561 import TSL2561
import csv
import RPi.GPIO as GPIO
sys.path.append("/home/pi/SHT31_PAE")#adds the custom SHT31 function
from SHT31 import *
import ConfigParser

#arguments will be in a separate .ini file (sys.argv[1]) which is read in and parsed to get different argument types
inputfile=str(sys.argv[1]) #the input .ini file is given as the first argument when the python script is called
Config = ConfigParser.ConfigParser()
Config.read(inputfile)

#Main light cycle
brightness=Config.getint("settings", "brightness") #brightness for main lights on. This will be passed to all steps, so further brightness must be adjusted via the color levels.
R=Config.getint("settings", "R") #red spectrum for main lights on
G=Config.getint("settings", "G") #green spectrum for main lights on
B=Config.getint("settings", "B") #blue spectrum for main lights on
W=Config.getint("settings", "W") #white spectrum for main lights on
onTime=Config.getfloat("settings", "onTime") #time in hours that lights will reach full intensity
offTime=Config.getfloat("settings", "offTime") #time in hours that lights will stop being at full intensity
checkTime=Config.getfloat("settings", "checkTime") #frequency in seconds of checking time and recording data (usually 60 seconds)
outFile=Config.get("settings", "outfile_name") #name of output file that will save data log

#Pulse
Pulse=Config.getboolean("pulse", "Pulse") #True/false for whether a light pulse will be used
Pulse_on=Config.getfloat("pulse", "Pulse_on") #Time in hours that pulse will start 
Pulse_off=Config.getfloat("pulse", "Pulse_off") #Time in hours that pulse will end 
Pulse_R=Config.getint("pulse", "Pulse_R") #red spectrum for pulse
Pulse_G=Config.getint("pulse", "Pulse_G") #green spectrum for pulse
Pulse_B=Config.getint("pulse", "Pulse_B") #blue spectrum for pulse
Pulse_W=Config.getint("pulse", "Pulse_W") #white spectrum for pulse

#Ramp on
Ramp_on=Config.getboolean("ramp_on", "Ramp_on") #true/false for whether a ramp will be used
ramp_ontime=Config.getfloat("ramp_on", "Ramp_ontime") #time in hours that lights will start ramping on

#Ramp off
Ramp_off=Config.getboolean("ramp_off", "Ramp_off") #true/false for whether a ramp will be used
ramp_offtime=Config.getfloat("ramp_off", "Ramp_offtime") #time in hours that lights will complete ramping

#Heat
Heat=Config.getboolean("heat", "Heat") #true false for whether the heater will be used
heatOn=Config.getfloat("heat", "heatOn") #time in hours that heater should turn on
heatOff=Config.getfloat("heat", "heatOff") #time in hours that heater should turn off 

#color2
color2=Config.getboolean("color2", "color2_used") #true false for using a second color
color2_offtime=Config.getfloat("color2", "color2_offtime") #off time for second color
R2=Config.getint("color2", "R2") #red spectrum for second color
G2=Config.getint("color2", "G2") #green spectrum for second color
B2=Config.getint("color2", "B2") #blue spectrum for second color
W2=Config.getint("color2", "W2") #white spectrum for second color

#color3
color3=Config.getboolean("color3", "color3_used") #true false for using a third color
color3_offtime=Config.getfloat("color3", "color3_offtime") #off time for a third color
R3=Config.getint("color3", "R3") #red spectrum for third color
G3=Config.getint("color3", "G3") #green spectrum for third color
B3=Config.getint("color3", "B3") #blue spectrum for third color
W3=Config.getint("color3", "W3") #white spectrum for third color

#set up LED indicator light via GPIO 16 (turns on whenever lights are on)
GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.OUT)

#setup Heater via Powerswitch on GPIO 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)

#set up light moniter
tsl = TSL2561(0x39,"/dev/i2c-1")
tsl.enable_autogain()
tsl.set_time(0x00)

#specify LED configuration
LED_COUNT      = 24                 # Number of LED pixels (always 24 in ring).
LED_PIN        = 18                 # GPIO pin connected to the pixels (must support PWM-always 18!).
LED_FREQ_HZ    = 800000             # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5                  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = brightness         # Set to 0 for darkest and 255 for brightest
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
#write a header column
wrtr.writerow(["TimeStamp", "Elapsed", "MCP9808Temp", "SHT31Temp", "Humidity", "Lux", "Lights", "Time_in_hours", "R", "G", "B", "W", "Heater"])

#determine program start time
programstart=time.time()

#start checking the time
while True:
    
    #determine current time
    loopstart=time.time() #record start time of loop so that total loop time can be precisely adjusted
    now= time.localtime(time.time()) #current time
    timeStamp=time.strftime("%y-%m-%d %H:%M:%S", now) #break time into H, M, S
    print timeStamp

    #apply calculation to time to determine time in hours as a decimal
    hour= float(time.strftime("%H "))
    minute= float(time.strftime("%M "))
    second=float(time.strftime("%S "))
    time_in_hours=hour+minute/60+second/3600
    print "time in hours is", time_in_hours

    #turn heat on if needed
    if Heat == True and heatOn <= time_in_hours < heatOff:
        GPIO.output(23, True)
        print "Heat on!"
        heater=True
    else:
        GPIO.output(23, False)
        print "Heat off"
        heater=False
        
    #read sensors for temperature, humidity, and light intensity
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
    
    #then check for ramping on. Ramp lights are automatically same as first color
    elif Ramp_on == True and ramp_ontime <= time_in_hours < onTime:
        print "Ramping on"
        Ramp_time=onTime - ramp_ontime #total time that will be spent ramping
        fade=(time_in_hours-ramp_ontime)/Ramp_time #proportion of ramping that is completed
        lights="increasing"
        tempR=int(float(R)*fade) #calculate a red value based on proporition of ramping completed
        tempG=int(float(G)*fade) #calculate a green value based on proporition of ramping completed
        tempB=int(float(B)*fade) #calculate a blue value based on proporition of ramping completed
        tempW=int(float(W)*fade) #calculate a white value based on proporition of ramping completed
        for i in range(LED_COUNT):
            GPIO.output(16, True)
            strip.setPixelColor(i,Color(tempG,tempR,tempB,tempW)) #assigns a temporary modulated color value based on ramp progression
            strip.show()
        currR=tempR
        currG=tempG
        currB=tempB
        currW=tempW
        
    #then check if lights are on main cycle     
    elif onTime <= time_in_hours < offTime:
        print ' Lights on!'
        lights="on, main"
        GPIO.output(16, True)
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(G,R,B,W)) #sets LEDs to main color
            strip.show()
        currR=R
        currG=G
        currB=B
        currW=W
        
    #then check if lights should be on color2    
    elif color2==True and offTime <= time_in_hours < color2_offtime:
        print ' Lights on color2!'
        lights="on, color2"
        GPIO.output(16, True)
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(G2,R2,B2,W2)) #sets strip to second color scheme
            strip.show()
        currR=R2
        currG=G2
        currB=B2
        currW=W2
        
    #then check if lights should be on color3    
    elif color3 ==True and color2_offtime <= time_in_hours < color3_offtime:
        print ' Lights on color 3!'
        lights="on, color3"
        GPIO.output(16, True)
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(G3,R3,B3,W3)) #sets lights to third color scheme
            strip.show()
        currR=R3
        currG=G3
        currB=B3
        currW=W3
        
    #then check for ramping off. Ramping off will occur for last used color
    elif Ramp_off == True and color2 == False and color3 == False and offTime <= time_in_hours < ramp_offtime:
        print "Ramping off"
        Ramp_time=ramp_offtime - offTime #total time that will be spent ramping down
        fade=(ramp_offtime-time_in_hours)/Ramp_time #proportion of ramping that is uncompleted
        lights="decreasing main color"
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
    
    #ramping off if 2 colors:
    elif Ramp_off == True and color2 == True and color3 == False and color2_offtime <= time_in_hours < ramp_offtime:
        print "Ramping off color2"
        Ramp_time=ramp_offtime - color2_offtime #total time that will be spent ramping down
        fade=(ramp_offtime-time_in_hours)/Ramp_time #proportion of ramping that is uncompleted
        lights="decreasing color2"
        tempR=int(float(R2)*fade) #calculate a red value based on proporition of ramping completed
        tempG=int(float(G2)*fade) #calculate a green value based on proporition of ramping completed
        tempB=int(float(B2)*fade) #calculate a blue value based on proporition of ramping completed
        tempW=int(float(W2)*fade) #calculate a white value based on proporition of ramping completed
        for i in range(LED_COUNT):
            GPIO.output(16, True)
            strip.setPixelColor(i,Color(tempG,tempR,tempB,tempW))
            strip.show()
        currR=tempR
        currG=tempG
        currB=tempB
        currW=tempW
        
    #ramping off if 3 colors:
    elif Ramp_off == True and color2 == True and color3 == True and color3_offtime <= time_in_hours < ramp_offtime:
        print "Ramping off color3"
        Ramp_time=ramp_offtime - color3_offtime #total time that will be spent ramping down
        fade=(ramp_offtime-time_in_hours)/Ramp_time #proportion of ramping that is uncompleted
        lights="decreasing color3"
        tempR=int(float(R3)*fade) #calculate a red value based on proporition of ramping completed
        tempG=int(float(G3)*fade) #calculate a green value based on proporition of ramping completed
        tempB=int(float(B3)*fade) #calculate a blue value based on proporition of ramping completed
        tempW=int(float(W3)*fade) #calculate a white value based on proporition of ramping completed
        for i in range(LED_COUNT):
            GPIO.output(16, True)
            strip.setPixelColor(i,Color(tempG,tempR,tempB,tempW))
            strip.show()
        currR=tempR
        currG=tempG
        currB=tempB
        currW=tempW
        
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
        
    #write all the current data to a new line in data file
    elapsedtime=(time.time()-programstart)/3600 #Elapsed time in hours since program started
    wrtr.writerow([timeStamp, elapsedtime, currtemp, SHT31reading[0], SHT31reading[1], currlux, lights, time_in_hours, currR, currG, currB, currW, heater])
    c.flush()
    
    # determine how much time to wait so that loop is executed based on checkTime seconds
    time.sleep(checkTime - ((time.time() - loopstart) % 60.0)) 
