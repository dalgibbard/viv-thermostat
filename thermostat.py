#!/usr/bin/python
#
# Reptile thermostat with remote socket triggering
#

TSET  = 25.5
TMARG = 0.25
STATE = None
TEMP_SCALE = "C"

YELLOW=int(17)
GREEN=int(27)

switchscript = "~fishfeedtime/fishfeedtime/switch"
remotehost = "192.168.0.50"
remoteuser = "dalgibbard"

import os, time, sys, glob, lcddriver
from datetime import datetime as t
import RPi.GPIO as GPIO

if os.geteuid() != 0:
        os.execvp("sudo", ["sudo"] + sys.argv)

lcd = lcddriver.lcd()

#Setting GPIO controling LED - ON when heating is running, OFF when it's not running
GPIO.setmode(GPIO.BCM) ## Use board pin numbering
GPIO.setwarnings(False)
GPIO.setup(GREEN, GPIO.OUT, False)
GPIO.setup(YELLOW, GPIO.OUT, False)

SOCKETS = [ {"socket": "4"} ]

#Set sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

#Def reading temperature as raw
def read_temp_raw():
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

#Def read temperature with nice conversation
def read_temp():
        lines = read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp = float(temp_string) / 1000.0
                if TEMP_SCALE is 'F' :
                        temp = temp * 9.000 / 5.000 + 32.000
                return temp

def sockets(state, LED):
    if state == "on":
        GPIO.output(LED, True)
    elif state == "off":
        GPIO.output(LED, False)
    if state == "on" or state == "off":
        for a in SOCKETS:
            sock = str(a['socket'])
            switchcmd = str("ssh ") + str(remoteuser) + str("@") + str(remotehost) + str(" 'sudo ") + str(switchscript) + " " + str(sock) + " " + str(state) + str("'")
            os.system(switchcmd)
    else:
        print("Invalid state sent to sockets(): " + str(state))
        raise


class color:
    HEADER = '\033[97m'
    BLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

GPIO.output(GREEN, True)

try:
    count = 0
    while True:
        HOUR = t.now().hour
        MINUTE = t.now().minute
   
        os.system('clear')

        #Display parameters
	msg = "Time: " + str(HOUR).zfill(2) + ":" + str(MINUTE).zfill(2) + "   "
        lcd.lcd_display_string(msg, 1)
        msg = "Temp Min: " + str(TSET - TMARG) + str(TEMP_SCALE)
        lcd.lcd_display_string(msg, 2)
        msg = "Temp Max: " + str(TSET) + str(TEMP_SCALE)
        lcd.lcd_display_string(msg, 3)

        print color.HEADER + ( "Settings:\n" + "Time : " + str(HOUR).zfill(2) + ":" + str(MINUTE).zfill(2) + "\n" + "Temperature min: " + str(TSET - TMARG) + str(TEMP_SCALE) + "\n" + "Temperature max: " + str(TSET) + str(TEMP_SCALE) + "\n") + color.ENDC
       
   
        #Reading curent temperature and making sure it's a number
        tmpinit = read_temp()
	tmp = float(format(tmpinit, '.3f').zfill(6))
        try:
            int(tmp)
        except:
            msg = "Temperature value is not a number"
            lcd.lcd_display_string(msg, 4)
            print color.FAIL + (msg) + color.ENDC
            heating_status("False")
   
   
        #Making decision weather to switch on/off
        #tmp >=tset - switching off
        if float(tmp) >= float(TSET) and (STATE==None or STATE==True):
            STATE = False
            sockets("off", YELLOW)
            msg = "TEMP " + str(format(tmp, '.3f').zfill(6)) + str(TEMP_SCALE) + "- SW OFF"
            lcd.lcd_display_string(msg, 4)
            print color.OKGREEN + msg + color.ENDC
        #tmp >= tset just being off
        elif float(tmp) >= float(TSET) and (STATE==False):
            if count > 3:
                sockets("off", YELLOW)
                count = 0
            msg = "TEMP " + str(format(tmp, '.3f').zfill(6)) + str(TEMP_SCALE) + "- OFF   "
            lcd.lcd_display_string(msg, 4)
            print color.OKGREEN + msg + color.ENDC
        #tmp<tset status is true and heating is running
        elif float(tmp) < float(TSET) and (STATE==True):
            if count > 3:
                sockets("on", YELLOW)
                count = 0
            msg = "TEMP " + str(format(tmp, '.3f').zfill(6)) + str(TEMP_SCALE) + "- ON    "
            lcd.lcd_display_string(msg, 4)
            print color.BLUE + msg + color.ENDC
        #tmp<tset-tmarg switching on
        elif float(tmp) < float(TSET) - float(TMARG) and (STATE==None or not STATE or STATE==False):
            STATE = True
            sockets("on", YELLOW)
            msg = "TEMP " + str(format(tmp, '.3f').zfill(6)) + str(TEMP_SCALE) + "- SW ON "
            lcd.lcd_display_string(msg, 4)
            print color.BLUE + msg + color.ENDC
        #tset-tmarg<=tmp
        elif float(tmp) >= float(TSET) - float(TMARG) and STATE==False:
            msg = "TEMP " + str(format(tmp, '.3f').zfill(6)) + str(TEMP_SCALE) + "- OFF   "
            lcd.lcd_display_string(msg, 4)
            print color.WARNING + msg + color.ENDC
        
        count = count + 1
        time.sleep(5)
except KeyboardInterrupt:
    sockets("off", YELLOW)
    msg = "   ** INACTIVE **   "
    lcd.lcd_display_string(msg, 1)
    lcd.lcd_display_string(msg, 2)
    lcd.lcd_display_string(msg, 3)
    lcd.lcd_display_string(msg, 4)
    GPIO.cleanup()
    print("Quitting...")
except Exception as err:
    sockets("off", YELLOW)
    msg = "   ** INACTIVE **   "
    lcd.lcd_display_string(msg, 1)
    lcd.lcd_display_string(msg, 2)
    lcd.lcd_display_string(msg, 3)
    lcd.lcd_display_string(msg, 4)
    GPIO.cleanup()
    print("Error: " + str(err))
    sys.exit(1)


