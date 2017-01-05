#!/usr/bin/python

#import all of the required modules 
    import sys
    import time
    from neopixel import *
    import Adafruit_MCP9808.MCP9808 as MCP9808
    from tentacle_pi.TSL2561 import TSL2561
    import csv
    import RPi.GPIO as GPIO
    from SHT31 import *
    import ConfigParser

#arguments will be in a separate .ini file which is read in and parsed

    inputfile=str(sys.argv[1])
    Config = ConfigParser.ConfigParser()
    Config.read(inputfile)
    brightness=Config.getint("settings", "brightness")
    R=Config.getint("settings", "R")
    G=Config.getint("settings", "G")
    B=Config.getint("settings", "B")
    W=Config.getint("settings", "W")
    onTime=Config.getint("settings", "onTime")
    offTime=Config.getint("settings", "offTime")
    checkTime=Config.getfloat("settings", "checkTime")
    outfile_name=Config.get("settings", "outfile_name")
    
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


LED_COUNT      = 24   # Number of LED pixels.
LED_PIN        = 18                 # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000             # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5                  # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = int(sys.argv [2])  # Set to 0 for darkest and 255 for brightest
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
wrtr.writerow(["TimeStamp", "MCP9808Temp", "SHT31Temp", "Humidity", "Lux", "Lights"])

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
    time_in_hours=hour+minute/60
    print "time in hours is", time_in_hours
    #read MCP9808 sensor
    currtemp=sensor.readTempC()
    print "MCP9808 Temperature is", currtemp
    SHT31reading=read_SHT31()
    print "SHT31 Temperature is", SHT31reading[0]
    print "SHT31 Humidity is", SHT31reading[1]
    #read light sensor
    currlux=tsl.lux()
    print "Lux is", currlux
    print 
    if onTime <= time_in_hours < offTime:
        print ' Lights on!'
        lights=True
        GPIO.output(16, True)
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(G,B,R,W))
            strip.show()
    else:
        print 'Lights off!, LED off'
        GPIO.output(16,False)
        lights=False
        for i in range(LED_COUNT):
            strip.setPixelColor(i,Color(0,0,0,0))
            strip.show()
    wrtr.writerow([timeStamp,currtemp, SHT31reading[0], SHT31reading[1], currlux, lights])
    c.flush()
    time.sleep(checkTime - ((time.time() - starttime) % 60.0))
