#!/usr/bin/python
#
# Reptile thermostat with remote socket triggering
#

TSET  = 28
TMARG = 1
STATE = None
TEMP_SCALE = "C"

YELLOW=int(17)
GREEN=int(27)

switchscript = "~fishfeedtime/fishfeedtime/switch"
remotehost = "192.168.0.50"
remoteuser = "dalgibbard"

import os, time, sys, glob
from datetime import datetime as t
import RPi.GPIO as GPIO

if os.geteuid() != 0:
        os.execvp("sudo", ["sudo"] + sys.argv)

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
    while True:
        HOUR = t.now().hour
        MINUTE = t.now().minute
   
        os.system('clear')

        #Display parameters
        print color.HEADER + ( "Settings:\n" + "Time : " + str(HOUR) + ":" + str(MINUTE) + "\n" + "Temperature min: " + str(TSET - TMARG) + str(TEMP_SCALE) + "\n" + "Temperature max: " + str(TSET) + str(TEMP_SCALE) + "\n") + color.ENDC
       
   
        #Reading curent temperature and making sure it's a number
        tmp = read_temp()
        try:
            int(tmp)
        except:
            print color.FAIL + ("Temperature value is not a number") + color.ENDC
            heating_status("False")
   
   
        #Making decision weather to switch on/off
        #tmp >=tset - switching off
        if tmp >= TSET and (STATE==None or STATE==True):
            STATE = False
            sockets("off", YELLOW)
            print color.OKGREEN + ("Temperature " + str(tmp) + " " + str(TEMP_SCALE) + " :Reached MAX, switching OFF heating") + color.ENDC
        #tmp >= tset just being off
        elif tmp >= TSET and (STATE==False):
            print color.OKGREEN + ("Temperature " + str(tmp) + " " + str(TEMP_SCALE) + " :We don't need to run the heating") + color.ENDC
        #tmp<tset status is true and heating is running
        elif tmp<TSET and (STATE==True):
            print color.BLUE + ("It\'s " + str(tmp) + " " + str(TEMP_SCALE) + " :Heating is running now") + color.ENDC
        #tmp<tset-tmarg switching on
        elif tmp < TSET - TMARG and (STATE==None or not STATE or STATE==False):
            STATE = True
            sockets("on", YELLOW)
            print color.BLUE + ("It\'s " + str(tmp) + " " + str(TEMP_SCALE) + " :Switching ON heating") + color.ENDC
        #tset-tmarg<=tmp
        elif tmp >=TSET-TMARG and STATE==False:
            print color.WARNING + ("Temperature " + str(tmp) + " " + str(TEMP_SCALE) + " :Within set range, no change required") + color.ENDC
       
        time.sleep(5)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Quitting...")
except Exception as err:
    GPIO.cleanup()
    print("Error: " + str(err))
    sys.exit(1)

